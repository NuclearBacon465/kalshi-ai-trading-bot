"""
Trade Execution Job

This job takes a position and executes it as a trade.

🚀 PHASE 4: Now uses institutional-grade enhanced execution when available!
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Iterable, Any, List

from src.utils.database import DatabaseManager, Position
from src.utils.logging_setup import get_trading_logger
from src.utils.safety import enforce_kill_switch
from src.clients.kalshi_client import KalshiClient, KalshiAPIError
from src.utils.health import is_safe_mode_active
from src.utils.notifications import get_notifier

# 🚀 PHASE 4: Import enhanced execution
try:
    from src.jobs.enhanced_execute import execute_position_enhanced, close_position_enhanced
    ENHANCED_EXECUTION_AVAILABLE = True
except ImportError:
    ENHANCED_EXECUTION_AVAILABLE = False


async def execute_position(
    position: Position,
    live_mode: bool,
    db_manager: DatabaseManager,
    kalshi_client: KalshiClient,
    total_capital: float = 100.0,
    urgency: str = "normal"
) -> bool:
    """
    Executes a single trade position.

    🚀 PHASE 4: Now uses enhanced execution with institutional-grade features when available!

    Args:
        position: The position to execute.
        live_mode: Whether to execute a live or simulated trade.
        db_manager: The database manager instance.
        kalshi_client: The Kalshi client instance.
        total_capital: Total portfolio capital (for Phase 4 execution)
        urgency: Execution urgency level: "low", "normal", "high", "urgent"

    Returns:
        True if execution was successful, False otherwise.
    """
    logger = get_trading_logger("trade_execution")
    notifier = get_notifier()

    logger.info(f"Executing position for market: {position.market_id}")

    # 🚀 PHASE 4: Try enhanced execution first!
    if ENHANCED_EXECUTION_AVAILABLE:
        try:
            logger.info("🚀 Using Phase 4 institutional-grade execution")
            return await execute_position_enhanced(
                position=position,
                live_mode=live_mode,
                db_manager=db_manager,
                kalshi_client=kalshi_client,
                total_capital=total_capital,
                urgency=urgency
            )
        except Exception as e:
            logger.warning(f"⚠️ Phase 4 execution failed, falling back to standard: {e}")
            # Continue to standard execution below

    # Standard execution (fallback or when Phase 4 not available)
    live_mode = enforce_kill_switch(live_mode, logger)

    # Check safe mode from database manager
    if db_manager.is_safe_mode():
        logger.warning(
            "Safe mode active (db_manager) - skipping trade execution",
            market_id=position.market_id,
            position_id=position.id
        )
        if position.id is not None:
            await db_manager.update_position_status(position.id, "voided")
        return False

    # Also check global safe mode
    if is_safe_mode_active():
        logger.warning(
            "Safe mode active (global) - blocking trade execution",
            market_id=position.market_id
        )
        if position.id is not None:
            await db_manager.update_position_status(position.id, "voided")
        return False

    async def fetch_fills_with_backoff(
        ticker: str,
        client_order_id: str,
        max_attempts: int = 4,
        base_delay: float = 0.5
    ) -> list:
        for attempt in range(1, max_attempts + 1):
            fills_response = await kalshi_client.get_fills(ticker=ticker)
            fills = fills_response.get("fills", [])
            matching = [
                fill for fill in fills
                if fill.get("client_order_id") == client_order_id
            ]
            if matching:
                return matching
            if attempt < max_attempts:
                sleep_time = base_delay * (2 ** (attempt - 1))
                logger.info(
                    "No fills yet for order %s (attempt %s/%s). Retrying in %.2fs.",
                    client_order_id,
                    attempt,
                    max_attempts,
                    sleep_time
                )
                await asyncio.sleep(sleep_time)
        return []

    def calculate_average_fill_price(fills: list, side: str) -> tuple[Optional[float], int]:
        total_price_cents = 0
        total_count = 0

        for fill in fills:
            fill_count = fill.get("count")
            if fill_count is None:
                fill_count = fill.get("filled") or fill.get("quantity")
            try:
                fill_count = int(fill_count) if fill_count is not None else 0
            except (TypeError, ValueError):
                fill_count = 0

            if fill_count <= 0:
                continue

            fill_price = fill.get("price")
            if fill_price is None:
                if side.upper() == "YES":
                    fill_price = fill.get("yes_price")
                else:
                    fill_price = fill.get("no_price")

            try:
                fill_price = int(fill_price) if fill_price is not None else None
            except (TypeError, ValueError):
                fill_price = None

            if fill_price is None:
                continue

            total_count += fill_count
            total_price_cents += fill_price * fill_count

        if total_count == 0:
            return None, 0

        average_price = total_price_cents / total_count / 100
        return average_price, total_count

    if db_manager.is_safe_mode_active():
        logger.warning("Safe mode active - skipping trade execution", market_id=position.market_id)
        return False

    if live_mode and is_kill_switch_enabled():
        logger.warning("Kill switch enabled: forcing simulated execution mode.")
        live_mode = False

    if live_mode:
        try:
            client_order_id = str(uuid.uuid4())

            # 🔔 Notify: Order being placed
            notifier.notify_order_placed(
                order_id=client_order_id,
                market_id=position.market_id,
                action="buy",
                side=position.side,
                quantity=position.quantity,
                order_type="market"
            )

            # 🚀 PHASE 3: Use smart limit orders by default for better fills
            if hasattr(kalshi_client, 'place_smart_limit_order'):
                try:
                    logger.info(f"💡 Using smart limit order for {position.market_id}")
                    order_response = await kalshi_client.place_smart_limit_order(
                        ticker=position.market_id,
                        client_order_id=client_order_id,
                        side=position.side.lower(),
                        action="buy",
                        count=position.quantity,
                        target_price=position.entry_price,  # Use expected entry price
                        max_slippage_pct=0.02  # 2% slippage tolerance
                    )
                except Exception as e:
                    logger.warning(f"Smart limit order failed, using market order fallback: {e}")
                    order_response = await kalshi_client.place_order(
                        ticker=position.market_id,
                        client_order_id=client_order_id,
                        side=position.side.lower(),
                        action="buy",
                        count=position.quantity,
                        type_="market"
                    )
            else:
                # Fallback to regular market order if smart limits not available
                order_response = await kalshi_client.place_order(
                    ticker=position.market_id,
                    client_order_id=client_order_id,
                    side=position.side.lower(),
                    action="buy",
                    count=position.quantity,
                    type_="market"
                )
            
            # Fetch fills with exponential backoff to get actual execution price
            fills = await fetch_fills_with_backoff(position.market_id, client_order_id)
            average_fill_price, total_filled = calculate_average_fill_price(fills, position.side)

            order_id = order_response.get('order', {}).get('order_id', client_order_id)

            if average_fill_price is not None and total_filled >= position.quantity:
                await db_manager.update_position_to_live(position.id, average_fill_price)
                
                # 🔔 Notify: Order filled
                notifier.notify_order_filled(
                    order_id=order_id,
                    market_id=position.market_id,
                    fill_price=average_fill_price
                )

                # 🔔 Notify: Trade opened
                notifier.notify_trade_opened(
                    market_id=position.market_id,
                    side=position.side,
                    quantity=position.quantity,
                    price=average_fill_price,
                    confidence=position.confidence,
                    edge=getattr(position, 'edge', 0.05)  # Estimate if not stored
                )

                logger.info(
                    "Successfully placed LIVE order for %s. Order ID: %s, Fill Price: $%.3f",
                    position.market_id,
                    order_id,
                    average_fill_price
                )
                return True

            # Partial fill or no fills found - use entry price as fallback
            logger.warning(
                "Order for %s not fully confirmed via fills (filled %s/%s). Using entry price.",
                position.market_id,
                total_filled,
                position.quantity
            )
            
            # Fall back to entry price if fills not confirmed
            fill_price = position.entry_price
            await db_manager.update_position_to_live(position.id, fill_price)

            # 🔔 Notify: Order filled (with fallback price)
            notifier.notify_order_filled(
                order_id=order_id,
                market_id=position.market_id,
                fill_price=fill_price
            )

            # 🔔 Notify: Trade opened
            notifier.notify_trade_opened(
                market_id=position.market_id,
                side=position.side,
                quantity=position.quantity,
                price=fill_price,
                confidence=position.confidence,
                edge=getattr(position, 'edge', 0.05)
            )

            logger.info(f"Successfully placed LIVE order for {position.market_id}. Order ID: {order_id}")
            return True

        except KalshiAPIError as e:
            logger.error(f"Failed to place LIVE order: {e}")
            db_manager.record_failure(f"KalshiAPIError: {e}")
            await db_manager.update_position_status(position.id, "voided")  # order failed; don't count as open exposure
            return False
    else:
        # Simulate the trade
        await db_manager.update_position_to_live(position.id, position.entry_price)
        logger.info(f"Successfully placed SIMULATED order for {position.market_id}")
        return True


def _normalize_fill_price(price: Any) -> Optional[float]:
    if price is None:
        return None
    try:
        normalized = float(price)
    except (TypeError, ValueError):
        return None
    if normalized > 1.0:
        normalized /= 100
    return normalized


def _extract_fill_price(fill: Dict[str, Any], side: str) -> Optional[float]:
    side_key = side.lower()
    if "price" in fill:
        return _normalize_fill_price(fill.get("price"))
    if side_key == "yes" and "yes_price" in fill:
        return _normalize_fill_price(fill.get("yes_price"))
    if side_key == "no" and "no_price" in fill:
        return _normalize_fill_price(fill.get("no_price"))
    if "yes_price" in fill:
        return _normalize_fill_price(fill.get("yes_price"))
    if "no_price" in fill:
        return _normalize_fill_price(fill.get("no_price"))
    return None


def _extract_fill_count(fill: Dict[str, Any]) -> Optional[int]:
    for key in ("count", "quantity", "size", "filled_count"):
        if key in fill and fill[key] is not None:
            try:
                return int(fill[key])
            except (TypeError, ValueError):
                return None
    return None


def _calculate_average_fill_price(
    fills: Iterable[Dict[str, Any]],
    side: str,
) -> Optional[float]:
    total_notional = 0.0
    total_count = 0

    for fill in fills:
        fill_price = _extract_fill_price(fill, side)
        if fill_price is None:
            continue
        fill_count = _extract_fill_count(fill) or 1
        total_notional += fill_price * fill_count
        total_count += fill_count

    if total_count == 0:
        return None
    return total_notional / total_count


async def _fetch_average_fill_price(
    kalshi_client: KalshiClient,
    ticker: str,
    client_order_id: str,
    side: str,
    max_attempts: int = 3,
    base_delay: float = 0.5,
) -> Optional[float]:
    for attempt in range(max_attempts):
        fills_response = await kalshi_client.get_fills(ticker=ticker)
        raw_fills = fills_response.get("fills") or fills_response.get("data") or []
        fills: List[Dict[str, Any]] = raw_fills if isinstance(raw_fills, list) else []

        matching_fills = [
            fill for fill in fills
            if fill.get("client_order_id") == client_order_id
            or fill.get("clientOrderId") == client_order_id
        ]

        average_price = _calculate_average_fill_price(matching_fills, side)
        if average_price is not None:
            return average_price

        if attempt < max_attempts - 1:
            await asyncio.sleep(base_delay * (2 ** attempt))

    return None


async def place_sell_limit_order(
    position: Position,
    limit_price: float,
    db_manager: DatabaseManager,
    kalshi_client: KalshiClient
) -> bool:
    """
    Place a sell limit order to close an existing position.
    
    Args:
        position: The position to close
        limit_price: The limit price for the sell order (in dollars)
        db_manager: Database manager
        kalshi_client: Kalshi API client
    
    Returns:
        True if order placed successfully, False otherwise
    """
    logger = get_trading_logger("sell_limit_order")

    if db_manager.is_safe_mode_active():
        logger.warning("Safe mode active - skipping sell limit order", market_id=position.market_id)
        return False
    
    try:
        import uuid
        client_order_id = str(uuid.uuid4())
        
        # Convert price to cents for Kalshi API
        limit_price_cents = int(limit_price * 100)
        
        # For sell orders, we need to use the opposite side logic:
        # - If we have YES position, we sell YES shares (action="sell", side="yes")
        # - If we have NO position, we sell NO shares (action="sell", side="no")
        side = position.side.lower()  # "YES" -> "yes", "NO" -> "no"
        
        order_params = {
            "ticker": position.market_id,
            "client_order_id": client_order_id,
            "side": side,
            "action": "sell",  # We're selling our existing position
            "count": position.quantity,
            "type": "limit"
        }
        
        # Add the appropriate price parameter based on what we're selling
        if side == "yes":
            order_params["yes_price"] = limit_price_cents
        else:
            order_params["no_price"] = limit_price_cents
        
        logger.info(f"🎯 Placing SELL LIMIT order: {position.quantity} {side.upper()} at {limit_price_cents}¢ for {position.market_id}")
        
        # Place the sell limit order
        response = await kalshi_client.place_order(**order_params)
        
        if response and 'order' in response:
            order_id = response['order'].get('order_id', client_order_id)
            
            # Record the sell order in the database (we could add a sell_orders table if needed)
            logger.info(f"✅ SELL LIMIT ORDER placed successfully! Order ID: {order_id}")
            logger.info(f"   Market: {position.market_id}")
            logger.info(f"   Side: {side.upper()} (selling {position.quantity} shares)")
            logger.info(f"   Limit Price: {limit_price_cents}¢")
            logger.info(f"   Expected Proceeds: ${limit_price * position.quantity:.2f}")
            
            return True
        else:
            logger.error(f"❌ Failed to place sell limit order: {response}")
            return False
            
    except KalshiAPIError as e:
        logger.error(f"❌ Kalshi error placing sell limit order for {position.market_id}: {e}")
        db_manager.record_failure("kalshi_api_error")
        return False
    except Exception as e:
        logger.error(f"❌ Error placing sell limit order for {position.market_id}: {e}")
        return False


async def place_profit_taking_orders(
    db_manager: DatabaseManager,
    kalshi_client: KalshiClient,
    profit_threshold: float = 0.25  # 25% profit target
) -> Dict[str, int]:
    """
    Place sell limit orders for positions that have reached profit targets.
    
    Args:
        db_manager: Database manager
        kalshi_client: Kalshi API client
        profit_threshold: Minimum profit percentage to trigger sell order
    
    Returns:
        Dictionary with results: {'orders_placed': int, 'positions_processed': int}
    """
    logger = get_trading_logger("profit_taking")
    
    results = {'orders_placed': 0, 'positions_processed': 0}
    
    try:
        # Get all open live positions
        positions = await db_manager.get_open_live_positions()
        
        if not positions:
            logger.info("No open positions to process for profit taking")
            return results
        
        logger.info(f"📊 Checking {len(positions)} positions for profit-taking opportunities")
        
        for position in positions:
            try:
                results['positions_processed'] += 1
                
                # Get current market data
                market_response = await kalshi_client.get_market(position.market_id)
                market_data = market_response.get('market', {})
                
                if not market_data:
                    logger.warning(f"Could not get market data for {position.market_id}")
                    continue
                
                # Get current price based on position side
                if position.side == "YES":
                    current_price = market_data.get('yes_price', 0) / 100  # Convert cents to dollars
                else:
                    current_price = market_data.get('no_price', 0) / 100
                
                # Calculate current profit
                if current_price > 0:
                    profit_pct = (current_price - position.entry_price) / position.entry_price
                    unrealized_pnl = (current_price - position.entry_price) * position.quantity
                    
                    logger.debug(f"Position {position.market_id}: Entry=${position.entry_price:.3f}, Current=${current_price:.3f}, Profit={profit_pct:.1%}, PnL=${unrealized_pnl:.2f}")
                    
                    # Check if we should place a profit-taking sell order
                    if profit_pct >= profit_threshold:
                        # Calculate sell limit price (slightly below current to ensure execution)
                        sell_price = current_price * 0.98  # 2% below current price for quick execution

                        # ⚠️ CRITICAL FIX: Ensure price is valid (minimum 1¢, maximum 99¢)
                        sell_price = max(0.01, min(0.99, sell_price))  # Clamp between 1¢ and 99¢
                        
                        logger.info(f"💰 PROFIT TARGET HIT: {position.market_id} - {profit_pct:.1%} profit (${unrealized_pnl:.2f})")
                        
                        # Place sell limit order
                        success = await place_sell_limit_order(
                            position=position,
                            limit_price=sell_price,
                            db_manager=db_manager,
                            kalshi_client=kalshi_client
                        )
                        
                        if success:
                            results['orders_placed'] += 1
                            logger.info(f"✅ Profit-taking order placed for {position.market_id}")
                        else:
                            logger.error(f"❌ Failed to place profit-taking order for {position.market_id}")
                
            except Exception as e:
                logger.error(f"Error processing position {position.market_id} for profit taking: {e}")
                continue
        
        logger.info(f"🎯 Profit-taking summary: {results['orders_placed']} orders placed from {results['positions_processed']} positions")
        return results
        
    except Exception as e:
        logger.error(f"Error in profit-taking order placement: {e}")
        return results


async def place_stop_loss_orders(
    db_manager: DatabaseManager,
    kalshi_client: KalshiClient,
    stop_loss_threshold: float = -0.10  # 10% stop loss
) -> Dict[str, int]:
    """
    Place sell limit orders for positions that need stop-loss protection.
    
    Args:
        db_manager: Database manager
        kalshi_client: Kalshi API client
        stop_loss_threshold: Maximum loss percentage before triggering stop loss
    
    Returns:
        Dictionary with results: {'orders_placed': int, 'positions_processed': int}
    """
    logger = get_trading_logger("stop_loss_orders")
    
    results = {'orders_placed': 0, 'positions_processed': 0}
    
    try:
        # Get all open live positions
        positions = await db_manager.get_open_live_positions()
        
        if not positions:
            logger.info("No open positions to process for stop-loss orders")
            return results
        
        logger.info(f"🛡️ Checking {len(positions)} positions for stop-loss protection")
        
        for position in positions:
            try:
                results['positions_processed'] += 1
                
                # Get current market data
                market_response = await kalshi_client.get_market(position.market_id)
                market_data = market_response.get('market', {})
                
                if not market_data:
                    logger.warning(f"Could not get market data for {position.market_id}")
                    continue
                
                # Get current price based on position side
                if position.side == "YES":
                    current_price = market_data.get('yes_price', 0) / 100
                else:
                    current_price = market_data.get('no_price', 0) / 100
                
                # Calculate current loss
                if current_price > 0:
                    loss_pct = (current_price - position.entry_price) / position.entry_price
                    unrealized_pnl = (current_price - position.entry_price) * position.quantity
                    
                    # Check if we need stop-loss protection
                    if loss_pct <= stop_loss_threshold:  # Negative loss percentage
                        # Calculate stop-loss sell price with safety bounds
                        # For a -10% stop loss, we want to sell at 90% * 0.9 = 81% of entry
                        stop_price = position.entry_price * (1 + stop_loss_threshold * 1.1)  # Slightly more aggressive

                        # ⚠️ CRITICAL FIX: Ensure price is valid (minimum 1¢, maximum 99¢)
                        stop_price = max(0.01, min(0.99, stop_price))  # Clamp between 1¢ and 99¢
                        
                        logger.info(f"🛡️ STOP LOSS TRIGGERED: {position.market_id} - {loss_pct:.1%} loss (${unrealized_pnl:.2f})")
                        
                        # Place stop-loss sell order
                        success = await place_sell_limit_order(
                            position=position,
                            limit_price=stop_price,
                            db_manager=db_manager,
                            kalshi_client=kalshi_client
                        )
                        
                        if success:
                            results['orders_placed'] += 1
                            logger.info(f"✅ Stop-loss order placed for {position.market_id}")
                        else:
                            logger.error(f"❌ Failed to place stop-loss order for {position.market_id}")
                
            except Exception as e:
                logger.error(f"Error processing position {position.market_id} for stop loss: {e}")
                continue
        
        logger.info(f"🛡️ Stop-loss summary: {results['orders_placed']} orders placed from {results['positions_processed']} positions")
        return results

    except Exception as e:
        logger.error(f"Error in stop-loss order placement: {e}")
        return results


async def execute_close_position(
    position: Position,
    db_manager: DatabaseManager,
    kalshi_client: KalshiClient,
    reason: str = "manual_close",
    total_capital: float = 100.0,
    urgency: str = "normal"
) -> bool:
    """
    Close an existing position (used for rebalancing, profit-taking, stop-loss).

    🚀 PHASE 4: Now uses enhanced closing with institutional-grade features!

    Args:
        position: Position to close
        db_manager: Database manager
        kalshi_client: Kalshi client
        reason: Reason for closing (for logging)
        total_capital: Total portfolio capital (for Phase 4 execution)
        urgency: Execution urgency level

    Returns:
        True if successfully closed, False otherwise
    """
    logger = get_trading_logger("position_closer")

    # 🚀 PHASE 4: Try enhanced close first!
    if ENHANCED_EXECUTION_AVAILABLE:
        try:
            logger.info("🚀 Using Phase 4 institutional-grade close")
            return await close_position_enhanced(
                position=position,
                db_manager=db_manager,
                kalshi_client=kalshi_client,
                reason=reason,
                total_capital=total_capital,
                urgency=urgency
            )
        except Exception as e:
            logger.warning(f"⚠️ Phase 4 close failed, falling back to standard: {e}")
            # Continue to standard close below

    try:
        import uuid

        # Get current market price
        market_info = await kalshi_client.get_market(position.market_id)

        if position.side.lower() == "yes":
            current_price = market_info.get('yes_price', 50) / 100
        else:
            current_price = market_info.get('no_price', 50) / 100

        # Try smart limit order first (better fill price)
        if hasattr(kalshi_client, 'place_smart_limit_order'):
            try:
                order_id = str(uuid.uuid4())
                response = await kalshi_client.place_smart_limit_order(
                    ticker=position.market_id,
                    client_order_id=order_id,
                    side=position.side,
                    action="sell",
                    count=position.quantity,
                    target_price=current_price,
                    max_slippage_pct=0.03  # Allow 3% slippage for closing
                )

                if response and 'order' in response:
                    logger.info(
                        f"✅ Position closed via smart limit: {position.market_id} "
                        f"(reason: {reason})"
                    )

                    # Update position status in database
                    await db_manager.update_position_status(position.id, "closed")

                    return True

            except Exception as e:
                logger.warning(f"Smart limit close failed, trying market order: {e}")

        # Fallback to regular limit order
        limit_price = current_price * 0.98  # 2% below current for quick fill
        limit_price = max(0.01, min(0.99, limit_price))

        success = await place_sell_limit_order(
            position=position,
            limit_price=limit_price,
            db_manager=db_manager,
            kalshi_client=kalshi_client
        )

        if success:
            logger.info(
                f"✅ Position closed via limit order: {position.market_id} "
                f"(reason: {reason})"
            )

            # Update position status
            await db_manager.update_position_status(position.id, "closed")

            return True

        return False

    except Exception as e:
        logger.error(f"Failed to close position {position.market_id}: {e}")
        return False