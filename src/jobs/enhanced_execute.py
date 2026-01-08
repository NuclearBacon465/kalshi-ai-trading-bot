"""
Enhanced Trade Execution with Phase 4 Technology

Uses ALL Phase 4 institutional-grade features:
- Order book microstructure analysis
- Adversarial trading detection
- Inventory risk management
- Smart order execution

This is the ULTIMATE execution engine.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict

from src.utils.database import DatabaseManager, Position
from src.utils.logging_setup import get_trading_logger
from src.utils.safety import enforce_kill_switch
from src.clients.kalshi_client import KalshiClient
from src.utils.health import is_safe_mode_active
from src.utils.notifications import get_notifier

# 🚀 PHASE 4: Import institutional-grade execution
from src.utils.smart_execution import SmartOrderExecutor, ExecutionDecision


async def execute_position_enhanced(
    position: Position,
    live_mode: bool,
    db_manager: DatabaseManager,
    kalshi_client: KalshiClient,
    total_capital: float = 100.0,
    urgency: str = "normal"
) -> bool:
    """
    Execute position using Phase 4 institutional-grade technology.

    Args:
        position: Position to execute
        live_mode: Live or paper trading
        db_manager: Database manager
        kalshi_client: Kalshi API client
        total_capital: Total portfolio capital (for risk assessment)
        urgency: "low", "normal", "high", "urgent"

    Returns:
        True if successful, False otherwise
    """
    logger = get_trading_logger("enhanced_execution")
    notifier = get_notifier()

    logger.info(f"🚀 PHASE 4 EXECUTION: {position.market_id} - {position.side} {position.quantity}")

    # Safety checks
    live_mode = enforce_kill_switch(live_mode, logger)

    if db_manager.is_safe_mode() or is_safe_mode_active():
        logger.warning("Safe mode active - skipping execution")
        if position.id:
            await db_manager.update_position_status(position.id, "voided")
        return False

    if not live_mode:
        logger.info("⚠️ Paper trading mode - simulating execution")
        # In paper mode, just mark as executed
        if position.id:
            await db_manager.update_position_to_live(position.id, position.entry_price)
        return True

    try:
        # 🧠 STEP 1: Create smart executor (integrates all Phase 4 features)
        executor = SmartOrderExecutor(kalshi_client, db_manager)

        logger.info("📊 Analyzing market conditions with Phase 4 technology...")

        # 🧠 STEP 2: Analyze and decide optimal execution strategy
        decision = await executor.analyze_and_decide(
            ticker=position.market_id,
            side=position.side,
            action="buy",  # Opening position
            quantity=position.quantity,
            target_price=position.entry_price,
            urgency=urgency,
            total_capital=total_capital
        )

        # 🧠 STEP 3: Check if we should execute
        if not decision.should_execute:
            logger.warning(f"❌ Execution cancelled: {decision.reasoning}")

            # Log why we skipped
            if decision.warnings:
                for warning in decision.warnings:
                    logger.warning(f"⚠️ {warning}")

            # Mark position as voided
            if position.id:
                await db_manager.update_position_status(position.id, "voided")

            # Notify user
            notifier.notify_trade_opened(
                market_id=position.market_id,
                side=position.side,
                quantity=0,
                entry_price=0,
                rationale=f"SKIPPED: {decision.reasoning}"
            )

            return False

        # 🧠 STEP 4: Log decision details
        logger.info(f"✅ Execution approved:")
        logger.info(f"   Method: {decision.execution_method}")
        logger.info(f"   Safety Score: {decision.safety_score:.1%}")
        logger.info(f"   Expected Fill: ${decision.expected_fill_price:.2f}")
        logger.info(f"   Expected Slippage: {decision.expected_slippage:.2%}")
        logger.info(f"   Chunks: {decision.split_into_chunks}")

        if decision.warnings:
            logger.info(f"   Warnings: {len(decision.warnings)}")
            for warning in decision.warnings:
                logger.warning(f"      - {warning}")

        logger.info(f"   Reasoning: {decision.reasoning}")

        # 🧠 STEP 5: Execute with smart execution engine
        logger.info(f"🎯 Executing with method: {decision.execution_method}")

        result = await executor.execute_with_decision(
            ticker=position.market_id,
            side=position.side,
            action="buy",
            decision=decision
        )

        # 🧠 STEP 6: Process result
        if result.success:
            logger.info(f"✅ ORDER FILLED!")
            logger.info(f"   Quantity: {result.filled_quantity}")
            logger.info(f"   Avg Price: ${result.average_fill_price:.2f}")
            logger.info(f"   Total Cost: ${result.total_cost:.2f}")
            logger.info(f"   Slippage: {result.slippage:.2%}")
            logger.info(f"   Time: {result.execution_time:.1f}s")
            logger.info(f"   Method: {result.method_used}")

            # Calculate vs expected
            slippage_diff = decision.expected_slippage - result.slippage
            if slippage_diff > 0:
                logger.info(f"   💰 SAVED: {slippage_diff:.2%} vs expected!")
            elif slippage_diff < 0:
                logger.warning(f"   📉 Extra slippage: {abs(slippage_diff):.2%}")

            # Update database
            if position.id:
                await db_manager.update_position_to_live(
                    position.id,
                    result.average_fill_price
                )

            # Notify success
            notifier.notify_order_filled(
                order_id=str(uuid.uuid4()),
                ticker=position.market_id,
                side=position.side,
                quantity=result.filled_quantity,
                price=result.average_fill_price
            )

            notifier.notify_trade_opened(
                market_id=position.market_id,
                side=position.side,
                quantity=result.filled_quantity,
                entry_price=result.average_fill_price,
                rationale=f"Phase 4 Execution: {result.method_used}"
            )

            # 🧠 STEP 7: Log execution statistics
            stats = executor.get_execution_stats()
            logger.info(f"📈 Executor Stats:")
            logger.info(f"   Total Orders: {stats['total_orders']}")
            logger.info(f"   Success Rate: {stats['success_rate']:.1%}")
            logger.info(f"   Avoided Toxic: {stats['avoided_toxic_trades']}")
            logger.info(f"   Avg Slippage Saved: {stats['avg_slippage_saved']:.2%}")

            return True

        else:
            # Execution failed
            logger.error(f"❌ Execution failed: {result.details}")

            if result.warnings_encountered:
                for warning in result.warnings_encountered:
                    logger.error(f"   ⚠️ {warning}")

            # Mark as failed
            if position.id:
                await db_manager.update_position_status(position.id, "failed")

            return False

    except Exception as e:
        logger.error(f"❌ Enhanced execution error: {e}", exc_info=True)

        # Fallback to basic execution if Phase 4 fails
        logger.warning("⚠️ Falling back to basic execution...")

        try:
            # Simple market order fallback
            client_order_id = str(uuid.uuid4())

            response = await kalshi_client.place_order(
                ticker=position.market_id,
                client_order_id=client_order_id,
                side=position.side.lower(),
                action="buy",
                count=position.quantity,
                type_="market"
            )

            if response and 'order' in response:
                logger.info("✅ Fallback execution successful")

                # Wait for fill
                await asyncio.sleep(2)

                # Get fills
                fills_response = await kalshi_client.get_fills(ticker=position.market_id)
                fills = fills_response.get('fills', [])

                our_fills = [f for f in fills if f.get('client_order_id') == client_order_id]

                if our_fills:
                    total_filled = sum(f.get('count', 0) for f in our_fills)
                    total_cost = sum(f.get('count', 0) * f.get('price', 0) / 100 for f in our_fills)
                    avg_price = total_cost / total_filled if total_filled > 0 else 0

                    if position.id:
                        await db_manager.update_position_to_live(position.id, avg_price)

                    return True

        except Exception as fallback_error:
            logger.error(f"❌ Fallback execution also failed: {fallback_error}")

        return False


async def close_position_enhanced(
    position: Position,
    db_manager: DatabaseManager,
    kalshi_client: KalshiClient,
    reason: str = "manual_close",
    total_capital: float = 100.0,
    urgency: str = "normal"
) -> bool:
    """
    Close position using Phase 4 technology.

    Args:
        position: Position to close
        db_manager: Database manager
        kalshi_client: Kalshi API client
        reason: Reason for closing
        total_capital: Total portfolio capital
        urgency: Urgency level

    Returns:
        True if successful
    """
    logger = get_trading_logger("enhanced_close")

    logger.info(f"🚀 PHASE 4 CLOSE: {position.market_id} - {position.quantity} contracts")

    try:
        # Create smart executor
        executor = SmartOrderExecutor(kalshi_client, db_manager)

        # Get current market price
        market_data = await kalshi_client.get_market(position.market_id)
        market_info = market_data.get('market', {})

        if position.side.lower() == 'yes':
            current_price = market_info.get('yes_price', 50) / 100
        else:
            current_price = market_info.get('no_price', 50) / 100

        # Analyze and decide
        decision = await executor.analyze_and_decide(
            ticker=position.market_id,
            side=position.side,
            action="sell",  # Closing position
            quantity=position.quantity,
            target_price=current_price,
            urgency=urgency,
            total_capital=total_capital
        )

        if not decision.should_execute:
            logger.warning(f"❌ Close cancelled: {decision.reasoning}")
            return False

        # Execute close
        result = await executor.execute_with_decision(
            ticker=position.market_id,
            side=position.side,
            action="sell",
            decision=decision
        )

        if result.success:
            logger.info(f"✅ Position closed: {result.filled_quantity} @ ${result.average_fill_price:.2f}")

            # Calculate P&L
            entry_value = position.quantity * position.entry_price
            exit_value = result.filled_quantity * result.average_fill_price
            pnl = exit_value - entry_value
            pnl_pct = (pnl / entry_value) if entry_value > 0 else 0

            logger.info(f"💰 P&L: ${pnl:.2f} ({pnl_pct:+.1%})")

            # Update database
            if position.id:
                await db_manager.update_position_status(position.id, "closed")

            return True
        else:
            logger.error(f"❌ Close failed: {result.details}")
            return False

    except Exception as e:
        logger.error(f"❌ Enhanced close error: {e}")
        return False


# Convenience function for getting optimal urgency based on conditions
def determine_urgency(
    position_pct: float,
    inventory_risk: float,
    safety_score: float
) -> str:
    """
    Determine optimal urgency level for execution.

    Args:
        position_pct: Position as % of portfolio
        inventory_risk: Inventory risk score (0-1)
        safety_score: Safety score (0-1)

    Returns:
        "low", "normal", "high", or "urgent"
    """
    # Urgent if inventory crisis
    if inventory_risk > 0.9 or position_pct > 0.25:
        return "urgent"

    # High if risky conditions
    if inventory_risk > 0.7 or position_pct > 0.20 or safety_score < 0.5:
        return "high"

    # Low if safe and patient trading
    if safety_score > 0.8 and inventory_risk < 0.3:
        return "low"

    # Normal for most cases
    return "normal"
