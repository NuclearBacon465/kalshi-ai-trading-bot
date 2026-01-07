"""
Trade Execution Job

This job takes a position and executes it as a trade.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict

from src.utils.database import DatabaseManager, Position
from src.config.settings import settings
from src.utils.logging_setup import get_trading_logger
from src.clients.kalshi_client import KalshiClient, KalshiAPIError

async def execute_position(
    position: Position, 
    live_mode: bool, 
    db_manager: DatabaseManager, 
    kalshi_client: KalshiClient
) -> bool:
    """
    Executes a single trade position.
    
    Args:
        position: The position to execute.
        live_mode: Whether to execute a live or simulated trade.
        db_manager: The database manager instance.
        kalshi_client: The Kalshi client instance.
        
    Returns:
        True if execution was successful, False otherwise.
    """
    logger = get_trading_logger("trade_execution")
    logger.info(f"Executing position for market: {position.market_id}")

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

    if live_mode:
        try:
            client_order_id = str(uuid.uuid4())
            order_response = await kalshi_client.place_order(
                ticker=position.market_id,
                client_order_id=client_order_id,
                side=position.side.lower(),
                action="buy",
                count=position.quantity,
                type_="market"
            )
            
            fills = await fetch_fills_with_backoff(position.market_id, client_order_id)
            average_fill_price, total_filled = calculate_average_fill_price(fills, position.side)

            if average_fill_price is not None and total_filled >= position.quantity:
                await db_manager.update_position_to_live(position.id, average_fill_price)
                logger.info(
                    "Successfully placed LIVE order for %s. Order ID: %s",
                    position.market_id,
                    order_response.get("order", {}).get("order_id")
                )
                return True

            logger.warning(
                "Order for %s not fully filled (filled %s/%s). Marking position pending.",
                position.market_id,
                total_filled,
                position.quantity
            )
            await db_manager.update_position_status(position.id, "pending")
            return False

        except KalshiAPIError as e:
            logger.error(f"Failed to place LIVE order: {e}")
            await db_manager.update_position_status(position.id, "voided")  # order failed; don't count as open exposure
            return False
    else:
        # Simulate the trade
        await db_manager.update_position_to_live(position.id, position.entry_price)
        logger.info(f"Successfully placed SIMULATED order for {position.market_id}")
        return True


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
                        # Calculate stop-loss sell price
                        stop_price = position.entry_price * (1 + stop_loss_threshold * 1.1)  # Slightly more aggressive
                        stop_price = max(0.01, stop_price)  # Ensure price is at least 1¢
                        
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
