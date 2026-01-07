"""
Quick Flip Scalping Strategy

This strategy implements rapid scalping by:
1. Identifying markets with potential for quick price movements
2. Buying contracts at low prices (1¢, 5¢, etc.)
3. Immediately placing sell limit orders for higher prices (2¢, 10¢, etc.)
4. Managing multiple concurrent positions across many markets

Key advantages:
- Low capital requirement per trade
- Quick turnover without long-term capital lock-up
- Limited downside risk per position
- Scalable across many markets simultaneously
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from src.clients.kalshi_client import KalshiClient
from src.clients.xai_client import XAIClient
from src.utils.database import DatabaseManager, Market, Position
from src.config.settings import settings
from src.utils.logging_setup import get_trading_logger
from src.jobs.execute import place_sell_limit_order


@dataclass
class QuickFlipOpportunity:
    """Represents a quick flip scalping opportunity."""
    market_id: str
    market_title: str
    side: str  # "YES" or "NO"
    entry_price: float  # Price to buy at (in cents)
    exit_price: float   # Price to sell at (in cents)
    quantity: int
    expected_profit: float  # Profit per contract if successful
    confidence_score: float  # How confident we are this will work (0-1)
    movement_indicator: str  # Why we think price will move
    max_hold_time: int  # Maximum time to hold before cutting losses (minutes)


@dataclass
class QuickFlipConfig:
    """Configuration for quick flip strategy."""
    min_entry_price: int = 1    # Minimum entry price in cents
    max_entry_price: int = 20   # Maximum entry price in cents
    min_profit_margin: float = 1.0  # Minimum profit margin (100% = double)
    max_position_size: int = 100    # Maximum contracts per position
    max_concurrent_positions: int = 50  # Maximum simultaneous positions
    capital_per_trade: float = 50.0    # Maximum capital per trade
    confidence_threshold: float = 0.6   # Minimum confidence to trade
    max_hold_minutes: int = 30         # Maximum hold time before exit


class QuickFlipScalpingStrategy:
    """
    Implements the quick flip scalping strategy.
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        kalshi_client: KalshiClient, 
        xai_client: XAIClient,
        config: Optional[QuickFlipConfig] = None
    ):
        self.db_manager = db_manager
        self.kalshi_client = kalshi_client
        self.xai_client = xai_client
        self.config = config or QuickFlipConfig()
        self.logger = get_trading_logger("quick_flip_scalping")
        
        # Track active positions for this strategy
        self.active_positions: Dict[str, Position] = {}
        self.pending_sells: Dict[str, dict] = {}  # Track pending sell orders
        
    async def identify_quick_flip_opportunities(
        self, 
        markets: List[Market],
        available_capital: float
    ) -> List[QuickFlipOpportunity]:
        """
        Identify markets suitable for quick flip scalping.
        
        Criteria:
        1. Low current prices (1¢-20¢ range)
        2. High volatility or recent movement
        3. AI confidence in directional movement
        4. Sufficient liquidity for entry/exit
        """
        opportunities = []
        
        self.logger.info(f"🔍 Analyzing {len(markets)} markets for quick flip opportunities")
        
        max_position_size_usd = getattr(settings.trading, "max_position_size_usd", None)
        max_position_size_pct = getattr(settings.trading, "max_position_size_pct", None)
        max_position_size_pct_value = None
        if max_position_size_pct is not None:
            max_position_size_pct_value = available_capital * (max_position_size_pct / 100)

        for market in markets:
            try:
                # Get current market data
                market_data = await self.kalshi_client.get_market(market.market_id)
                if not market_data:
                    continue
                
                market_info = market_data.get('market', {})
                yes_price = market_info.get('yes_ask', 0)
                no_price = market_info.get('no_ask', 0)
                
                # Check if prices are in our target range
                yes_opportunity = await self._evaluate_price_opportunity(
                    market, "YES", yes_price, market_info, max_position_size_usd, max_position_size_pct_value
                )
                no_opportunity = await self._evaluate_price_opportunity(
                    market, "NO", no_price, market_info, max_position_size_usd, max_position_size_pct_value
                )
                
                if yes_opportunity:
                    opportunities.append(yes_opportunity)
                if no_opportunity:
                    opportunities.append(no_opportunity)
                    
            except Exception as e:
                self.logger.error(f"Error analyzing market {market.market_id}: {e}")
                continue
        
        # Sort by expected profit and confidence
        opportunities.sort(
            key=lambda x: x.expected_profit * x.confidence_score, 
            reverse=True
        )
        
        # Limit by available capital and max concurrent positions
        max_positions = min(
            self.config.max_concurrent_positions,
            int(available_capital / self.config.capital_per_trade)
        )
        
        filtered_opportunities = opportunities[:max_positions]
        
        self.logger.info(
            f"🎯 Found {len(filtered_opportunities)} quick flip opportunities "
            f"(from {len(opportunities)} total analyzed)"
        )
        
        return filtered_opportunities
    
    async def _evaluate_price_opportunity(
        self,
        market: Market,
        side: str,
        current_price: int,
        market_info: dict,
        max_position_size_usd: Optional[float],
        max_position_size_pct_value: Optional[float]
    ) -> Optional[QuickFlipOpportunity]:
        """
        Evaluate if a specific side of a market presents a good quick flip opportunity.
        """
        if not current_price or current_price <= 0:
            return None
            
        # Check if price is in our target range
        if current_price < self.config.min_entry_price or current_price > self.config.max_entry_price:
            return None
        
        # Calculate potential exit price (at least min profit margin)
        min_exit_price = current_price * (1 + self.config.min_profit_margin)
        
        # Don't target prices above 95¢ (too close to ceiling)
        if min_exit_price > 95:
            return None
        
        # Use AI to assess movement probability and suggest exit price
        movement_analysis = await self._analyze_market_movement(market, side, current_price)
        
        if movement_analysis['confidence'] < self.config.confidence_threshold:
            return None

        proposed_trade_value = self.config.capital_per_trade
        if (
            max_position_size_usd is not None
            and max_position_size_pct_value is not None
            and proposed_trade_value > max_position_size_usd
            and proposed_trade_value > max_position_size_pct_value
        ):
            self.logger.info(
                "❌ Skipping quick flip for %s - trade $%.2f exceeds caps: %s%% ($%.2f) and USD cap $%.2f",
                market.market_id,
                proposed_trade_value,
                getattr(settings.trading, "max_position_size_pct", 0),
                max_position_size_pct_value,
                max_position_size_usd,
            )
            return None

        effective_trade_value = proposed_trade_value
        if max_position_size_usd is not None and effective_trade_value > max_position_size_usd:
            effective_trade_value = max_position_size_usd
        if max_position_size_pct_value is not None and effective_trade_value > max_position_size_pct_value:
            effective_trade_value = max_position_size_pct_value

        if effective_trade_value <= 0:
            return None

        if effective_trade_value < proposed_trade_value:
            self.logger.info(
                "⚠️ Capping quick flip trade size from $%.2f to $%.2f for %s",
                proposed_trade_value,
                effective_trade_value,
                market.market_id,
            )
        
        # Calculate position size
        quantity = min(
            self.config.max_position_size,
            int(effective_trade_value / (current_price / 100))
        )
        
        if quantity < 1:
            return None
        
        expected_profit = quantity * ((movement_analysis['target_price'] - current_price) / 100)
        
        return QuickFlipOpportunity(
            market_id=market.market_id,
            market_title=market.title,
            side=side,
            entry_price=current_price,
            exit_price=movement_analysis['target_price'],
            quantity=quantity,
            expected_profit=expected_profit,
            confidence_score=movement_analysis['confidence'],
            movement_indicator=movement_analysis['reason'],
            max_hold_time=self.config.max_hold_minutes
        )
    
    async def _analyze_market_movement(
        self, 
        market: Market, 
        side: str, 
        current_price: int
    ) -> dict:
        """
        Use AI to analyze potential for quick price movement.
        """
        try:
            # Create focused prompt for quick movement analysis
            prompt = f"""
QUICK SCALP ANALYSIS for {market.title}

Current {side} price: {current_price}¢
Market closes: {datetime.fromtimestamp(market.expiration_ts).strftime('%Y-%m-%d %H:%M')}

Analyze for IMMEDIATE (next 30 minutes) price movement potential:

1. Is there likely catalysts/news that could move price UP in next 30 min?
2. Current momentum/volatility indicators
3. What price could {side} realistically reach in 30 min?
4. Confidence level (0-1) for upward movement

Respond with:
TARGET_PRICE: [realistic price in cents]
CONFIDENCE: [0.0-1.0]
REASON: [brief explanation]
"""

            response = await self.xai_client.get_completion(
                prompt=prompt,
                max_tokens=3000,
                strategy="quick_flip_scalping",
                query_type="movement_prediction",
                market_id=market.market_id
            )
            
            # Check if AI response is None (API exhausted or failed)
            if response is None:
                self.logger.info(f"AI analysis unavailable for {market.market_id}, using conservative defaults")
                return {
                    'target_price': current_price + 2,  # Very conservative target
                    'confidence': 0.2,  # Low confidence
                    'reason': "AI analysis unavailable due to API limits"
                }
            
            # Parse response safely
            lines = response.strip().split('\n')
            target_price = current_price * 2  # Default fallback
            confidence = 0.5
            reason = "Default analysis"
            
            for line in lines:
                if 'TARGET_PRICE:' in line:
                    try:
                        target_price = float(line.split(':')[1].strip())
                    except (ValueError, IndexError):
                        pass
                elif 'CONFIDENCE:' in line:
                    try:
                        confidence = float(line.split(':')[1].strip())
                    except (ValueError, IndexError):
                        pass
                elif 'REASON:' in line:
                    reason = line.split(':', 1)[1].strip()
            
            # Ensure target price is reasonable
            target_price = max(current_price + 1, min(target_price, 95))
            
            return {
                'target_price': target_price,
                'confidence': confidence,
                'reason': reason
            }
            
        except Exception as e:
            self.logger.error(f"Error in movement analysis: {e}")
            return {
                'target_price': current_price * 2,
                'confidence': 0.3,
                'reason': f"Analysis failed: {e}"
            }
    
    async def execute_quick_flip_opportunities(
        self,
        opportunities: List[QuickFlipOpportunity]
    ) -> Dict:
        """
        Execute quick flip trades and immediately place sell orders.
        """
        results = {
            'positions_created': 0,
            'sell_orders_placed': 0,
            'total_capital_used': 0.0,
            'expected_profit': 0.0,
            'failed_executions': 0
        }
        
        self.logger.info(f"🚀 Executing {len(opportunities)} quick flip opportunities")
        
        for opportunity in opportunities:
            try:
                success = await self._execute_single_quick_flip(opportunity)
                
                if success:
                    results['positions_created'] += 1
                    results['total_capital_used'] += opportunity.quantity * (opportunity.entry_price / 100)
                    results['expected_profit'] += opportunity.expected_profit
                    
                    # Try to place sell order immediately
                    sell_success = await self._place_immediate_sell_order(opportunity)
                    if sell_success:
                        results['sell_orders_placed'] += 1
                else:
                    results['failed_executions'] += 1
                    
            except Exception as e:
                self.logger.error(f"Error executing quick flip for {opportunity.market_id}: {e}")
                results['failed_executions'] += 1
                continue
        
        self.logger.info(
            f"✅ Quick Flip Execution Summary: "
            f"{results['positions_created']} positions, "
            f"{results['sell_orders_placed']} sell orders, "
            f"${results['total_capital_used']:.0f} capital used"
        )
        
        return results
    
    async def _execute_single_quick_flip(self, opportunity: QuickFlipOpportunity) -> bool:
        """Execute a single quick flip trade."""
        try:
            # Create position object
            position = Position(
                market_id=opportunity.market_id,
                side=opportunity.side,
                quantity=opportunity.quantity,
                entry_price=opportunity.entry_price / 100,  # Convert to dollars
                live=False,  # Will be set to True after execution
                timestamp=datetime.now(),
                rationale=f"QUICK FLIP: {opportunity.movement_indicator} | "
                         f"Target: {opportunity.entry_price}¢→{opportunity.exit_price}¢",
                strategy="quick_flip_scalping"
            )
            
            # Add to database
            position_id = await self.db_manager.add_position(position)
            if position_id is None:
                self.logger.warning(f"Position already exists for {opportunity.market_id}")
                return False
            
            position.id = position_id
            
            # Execute the position
            from src.jobs.execute import execute_position
            live_mode = getattr(settings.trading, 'live_trading_enabled', False)
            
            success = await execute_position(
                position=position,
                live_mode=live_mode,
                db_manager=self.db_manager,
                kalshi_client=self.kalshi_client
            )
            
            if success:
                self.active_positions[opportunity.market_id] = position
                self.logger.info(
                    f"✅ Quick flip entry: {opportunity.side} {opportunity.quantity} "
                    f"at {opportunity.entry_price}¢ for {opportunity.market_id}"
                )
                return True
            else:
                self.logger.error(f"❌ Failed to execute quick flip for {opportunity.market_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing single quick flip: {e}")
            return False
    
    async def _place_immediate_sell_order(self, opportunity: QuickFlipOpportunity) -> bool:
        """
        Place sell limit order immediately after position is filled.
        """
        try:
            position = self.active_positions.get(opportunity.market_id)
            if not position:
                self.logger.error(f"No active position found for {opportunity.market_id}")
                return False
            
            # Place sell limit order at target price
            sell_price = opportunity.exit_price / 100  # Convert to dollars
            
            success = await place_sell_limit_order(
                position=position,
                limit_price=sell_price,
                db_manager=self.db_manager,
                kalshi_client=self.kalshi_client
            )
            
            if success:
                # Track the pending sell
                self.pending_sells[opportunity.market_id] = {
                    'position': position,
                    'target_price': sell_price,
                    'placed_at': datetime.now(),
                    'max_hold_until': datetime.now() + timedelta(minutes=opportunity.max_hold_time)
                }
                
                self.logger.info(
                    f"🎯 Sell order placed: {position.side} {position.quantity} "
                    f"at {opportunity.exit_price}¢ for {opportunity.market_id}"
                )
                return True
            else:
                self.logger.error(f"Failed to place sell order for {opportunity.market_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error placing immediate sell order: {e}")
            return False
    
    async def manage_active_positions(self) -> Dict:
        """
        Manage active quick flip positions:
        1. Check if sell orders have filled
        2. Cut losses on positions held too long
        3. Adjust sell prices if needed
        """
        results = {
            'positions_closed': 0,
            'orders_adjusted': 0,
            'losses_cut': 0,
            'total_pnl': 0.0
        }
        
        current_time = datetime.now()
        positions_to_remove = []
        
        for market_id, sell_info in self.pending_sells.items():
            try:
                position = sell_info['position']
                max_hold_until = sell_info['max_hold_until']
                
                # Check if we should cut losses (held too long)
                if current_time > max_hold_until:
                    self.logger.warning(
                        f"⏰ Quick flip held too long: {market_id}, cutting losses"
                    )
                    
                    # Place market order to exit immediately
                    cut_success = await self._cut_losses_market_order(position)
                    if cut_success:
                        results['losses_cut'] += 1
                        positions_to_remove.append(market_id)
                
                # TODO: Add logic to check if sell order filled
                # TODO: Add logic to adjust sell price if market moved against us
                
            except Exception as e:
                self.logger.error(f"Error managing position {market_id}: {e}")
                continue
        
        # Clean up closed positions
        for market_id in positions_to_remove:
            if market_id in self.active_positions:
                del self.active_positions[market_id]
            if market_id in self.pending_sells:
                del self.pending_sells[market_id]
        
        return results
    
    async def _cut_losses_market_order(self, position: Position) -> bool:
        """Place market order to immediately exit a position."""
        try:
            # Place market sell order to cut losses
            import uuid
            client_order_id = str(uuid.uuid4())
            
            order_params = {
                "ticker": position.market_id,
                "client_order_id": client_order_id,
                "side": position.side.lower(),
                "action": "sell",
                "count": position.quantity,
                "type": "market"
            }
            
            live_mode = getattr(settings.trading, 'live_trading_enabled', False)
            
            if live_mode:
                response = await self.kalshi_client.place_order(**order_params)
                
                if response and 'order' in response:
                    self.logger.info(
                        f"🛑 Loss cut order placed: {position.side} {position.quantity} "
                        f"MARKET SELL for {position.market_id}"
                    )
                    return True
                else:
                    self.logger.error(f"Failed to place loss cut order: {response}")
                    return False
            else:
                self.logger.info(
                    f"📝 SIMULATED loss cut: {position.side} {position.quantity} "
                    f"MARKET SELL for {position.market_id}"
                )
                return True
                
        except Exception as e:
            self.logger.error(f"Error cutting losses: {e}")
            return False


async def run_quick_flip_strategy(
    db_manager: DatabaseManager,
    kalshi_client: KalshiClient,
    xai_client: XAIClient,
    available_capital: float,
    config: Optional[QuickFlipConfig] = None
) -> Dict:
    """
    Main entry point for quick flip scalping strategy.
    """
    logger = get_trading_logger("quick_flip_main")
    
    try:
        logger.info("🎯 Starting Quick Flip Scalping Strategy")
        
        # Initialize strategy
        strategy = QuickFlipScalpingStrategy(
            db_manager, kalshi_client, xai_client, config
        )
        
        # Get available markets
        markets = await db_manager.get_eligible_markets(
            volume_min=100,  # Lower liquidity requirement for small positions
            max_days_to_expiry=365  # Accept any timeline for quick flips
        )
        
        if not markets:
            logger.warning("No markets available for quick flip analysis")
            return {'error': 'No markets available'}
        
        # Step 1: Identify opportunities
        opportunities = await strategy.identify_quick_flip_opportunities(
            markets, available_capital
        )
        
        if not opportunities:
            logger.info("No quick flip opportunities found")
            return {'opportunities_found': 0}
        
        # Step 2: Execute quick flips
        execution_results = await strategy.execute_quick_flip_opportunities(opportunities)
        
        # Step 3: Manage existing positions
        management_results = await strategy.manage_active_positions()
        
        # Combine results
        total_results = {
            **execution_results,
            **management_results,
            'opportunities_analyzed': len(opportunities),
            'strategy': 'quick_flip_scalping'
        }
        
        logger.info(
            f"🏁 Quick Flip Strategy Complete: "
            f"{execution_results['positions_created']} new positions, "
            f"${execution_results['total_capital_used']:.0f} capital used, "
            f"${execution_results['expected_profit']:.2f} expected profit"
        )
        
        return total_results
        
    except Exception as e:
        logger.error(f"Error in quick flip strategy: {e}")
        return {'error': str(e)} 
