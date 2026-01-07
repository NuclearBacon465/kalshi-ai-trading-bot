"""
Enhanced evaluation system with cost monitoring and trading performance analysis.
"""

import asyncio
import aiosqlite
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from src.utils.database import DatabaseManager
from src.config.settings import settings
from src.utils.logging_setup import get_trading_logger

async def analyze_ai_costs(db_manager: DatabaseManager) -> Dict:
    """Analyze AI spending patterns and provide cost optimization recommendations."""
    logger = get_trading_logger("cost_analysis")
    
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    async with aiosqlite.connect(db_manager.db_path) as db:
        # Daily cost summary
        daily_costs = {}
        for date in [today, yesterday]:
            cursor = await db.execute("""
                SELECT total_ai_cost, analysis_count, decision_count 
                FROM daily_cost_tracking WHERE date = ?
            """, (date,))
            row = await cursor.fetchone()
            daily_costs[date] = {
                'cost': row[0] if row else 0.0,
                'analyses': row[1] if row else 0,
                'decisions': row[2] if row else 0
            }
        
        # Weekly cost trend
        cursor = await db.execute("""
            SELECT SUM(total_ai_cost), SUM(analysis_count), SUM(decision_count)
            FROM daily_cost_tracking WHERE date >= ?
        """, (week_ago,))
        weekly_stats = await cursor.fetchone()
        
        # Most expensive markets by analysis cost
        cursor = await db.execute("""
            SELECT market_id, COUNT(*) as analysis_count, SUM(cost_usd) as total_cost,
                   AVG(cost_usd) as avg_cost, analysis_type
            FROM market_analyses 
            WHERE DATE(analysis_timestamp) >= ?
            GROUP BY market_id
            ORDER BY total_cost DESC
            LIMIT 10
        """, (week_ago,))
        expensive_markets = await cursor.fetchall()
        
        # Analysis type breakdown
        cursor = await db.execute("""
            SELECT analysis_type, COUNT(*) as count, SUM(cost_usd) as total_cost
            FROM market_analyses 
            WHERE DATE(analysis_timestamp) >= ?
            GROUP BY analysis_type
        """, (week_ago,))
        analysis_breakdown = await cursor.fetchall()
    
    # Calculate cost efficiency metrics
    today_cost = daily_costs[today]['cost']
    today_decisions = daily_costs[today]['decisions']
    cost_per_decision = today_cost / max(1, today_decisions)
    
    weekly_cost = weekly_stats[0] if weekly_stats and weekly_stats[0] else 0.0
    weekly_analyses = weekly_stats[1] if weekly_stats and weekly_stats[1] else 0
    weekly_decisions = weekly_stats[2] if weekly_stats and weekly_stats[2] else 0
    
    # Generate recommendations
    recommendations = []
    
    if today_cost > settings.trading.daily_ai_budget * 0.8:
        recommendations.append(f"⚠️  Near daily budget limit: ${today_cost:.3f} / ${settings.trading.daily_ai_budget}")
    
    if cost_per_decision > settings.trading.max_ai_cost_per_decision:
        recommendations.append(f"💰 High cost per decision: ${cost_per_decision:.3f}")
    
    if weekly_cost > settings.trading.daily_ai_budget * 5:  # More than 5 days of budget in a week
        recommendations.append("📈 Weekly spending trending high - consider tighter controls")
    
    if weekly_analyses > weekly_decisions * 3:  # Too many analyses relative to decisions
        recommendations.append("🔄 High analysis-to-decision ratio - improve filtering")
    
    # Log comprehensive cost report
    logger.info(
        "AI Cost Analysis Report",
        today_cost=today_cost,
        yesterday_cost=daily_costs[yesterday]['cost'],
        weekly_cost=weekly_cost,
        cost_per_decision=cost_per_decision,
        weekly_analyses=weekly_analyses,
        weekly_decisions=weekly_decisions,
        budget_utilization=today_cost / settings.trading.daily_ai_budget,
        recommendations=recommendations
    )
    
    return {
        'daily_costs': daily_costs,
        'weekly_cost': weekly_cost,
        'cost_per_decision': cost_per_decision,
        'expensive_markets': expensive_markets,
        'analysis_breakdown': analysis_breakdown,
        'recommendations': recommendations
    }

async def analyze_trading_performance(db_manager: DatabaseManager) -> Dict:
    """Analyze trading performance and position management effectiveness."""
    logger = get_trading_logger("trading_performance")
    
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    rolling_window_days = 30
    rolling_window_start = (datetime.now() - timedelta(days=rolling_window_days)).strftime('%Y-%m-%d')
    
    async with aiosqlite.connect(db_manager.db_path) as db:
        # Overall P&L
        cursor = await db.execute("""
            SELECT COUNT(*) as total_trades, SUM(pnl) as total_pnl,
                   AVG(pnl) as avg_pnl, SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades
            FROM trade_logs WHERE DATE(exit_timestamp) >= ?
        """, (week_ago,))
        perf_stats = await cursor.fetchone()
        
        # Exit reason analysis
        cursor = await db.execute("""
            SELECT 
                CASE 
                    WHEN rationale LIKE '%market_resolution%' THEN 'market_resolution'
                    WHEN rationale LIKE '%stop_loss%' THEN 'stop_loss'
                    WHEN rationale LIKE '%take_profit%' THEN 'take_profit'
                    WHEN rationale LIKE '%time_based%' THEN 'time_based'
                    ELSE 'other'
                END as exit_reason,
                COUNT(*) as count,
                AVG(pnl) as avg_pnl
            FROM trade_logs 
            WHERE DATE(exit_timestamp) >= ?
            GROUP BY exit_reason
        """, (week_ago,))
        exit_reasons = await cursor.fetchall()
        
        # Current open positions analysis
        cursor = await db.execute("""
            SELECT COUNT(*) as open_positions,
                   AVG((julianday('now') - julianday(timestamp)) * 24) as avg_hours_held
            FROM positions WHERE status = 'open'
        """)
        position_stats = await cursor.fetchone()

        cursor = await db.execute("""
            SELECT pnl, entry_price, quantity, exit_timestamp
            FROM trade_logs
            WHERE DATE(exit_timestamp) >= ?
            ORDER BY exit_timestamp ASC
        """, (rolling_window_start,))
        rolling_trades = await cursor.fetchall()
    
    total_trades = perf_stats[0] if perf_stats and perf_stats[0] is not None else 0
    total_pnl = perf_stats[1] if perf_stats and perf_stats[1] is not None else 0.0
    winning_trades = perf_stats[3] if perf_stats and perf_stats[3] is not None else 0
    win_rate = (winning_trades / max(1, total_trades)) if total_trades > 0 else 0.0
    
    avg_pnl = perf_stats[2] if perf_stats and perf_stats[2] is not None else 0.0
    open_positions = position_stats[0] if position_stats and position_stats[0] is not None else 0
    avg_hours_held = position_stats[1] if position_stats and position_stats[1] is not None else 0.0

    rolling_metrics = _calculate_rolling_performance(rolling_trades)
    
    logger.info(
        "Trading Performance Report",
        total_trades=total_trades,
        total_pnl=total_pnl,
        win_rate=win_rate,
        avg_pnl=avg_pnl,
        open_positions=open_positions,
        avg_hours_held=avg_hours_held,
        rolling_window_days=rolling_window_days,
        rolling_win_rate=rolling_metrics["win_rate"],
        rolling_max_drawdown=rolling_metrics["max_drawdown"],
        rolling_sharpe=rolling_metrics["sharpe_ratio"],
        rolling_trades=rolling_metrics["total_trades"]
    )
    
    return {
        'total_trades': total_trades,
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'exit_reasons': exit_reasons,
        'position_stats': position_stats,
        'rolling_metrics': rolling_metrics
    }

def _calculate_rolling_performance(trades: List[tuple]) -> Dict[str, float]:
    """Calculate rolling win rate, max drawdown, and Sharpe ratio from recent trades."""
    total_trades = len(trades)
    if total_trades == 0:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0
        }

    wins = 0
    returns: List[float] = []
    equity_curve: List[float] = []
    cumulative_pnl = 0.0

    for pnl, entry_price, quantity, _exit_timestamp in trades:
        trade_pnl = pnl or 0.0
        if trade_pnl > 0:
            wins += 1
        notional = abs((entry_price or 0.0) * (quantity or 0))
        normalized_return = trade_pnl / max(1.0, notional)
        returns.append(normalized_return)
        cumulative_pnl += trade_pnl
        equity_curve.append(cumulative_pnl)

    win_rate = wins / max(1, total_trades)

    running_max = 0.0
    max_drawdown = 0.0
    for value in equity_curve:
        running_max = max(running_max, value)
        if running_max > 0:
            drawdown = (running_max - value) / running_max
            max_drawdown = max(max_drawdown, drawdown)

    mean_return = sum(returns) / max(1, len(returns))
    variance = sum((r - mean_return) ** 2 for r in returns) / max(1, len(returns) - 1)
    std_dev = variance ** 0.5 if variance > 0 else 0.0
    sharpe_ratio = 0.0
    if std_dev > 0:
        sharpe_ratio = (mean_return / std_dev) * (len(returns) ** 0.5)

    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio
    }

def _assess_live_readiness(rolling_metrics: Dict[str, float]) -> Tuple[bool, List[str]]:
    """Assess readiness for live trading based on rolling performance metrics."""
    min_trades = 25
    min_win_rate = 0.55
    min_sharpe = 1.0
    max_drawdown = 0.2

    reasons = []
    total_trades = int(rolling_metrics.get("total_trades", 0))
    win_rate = rolling_metrics.get("win_rate", 0.0)
    sharpe_ratio = rolling_metrics.get("sharpe_ratio", 0.0)
    rolling_drawdown = rolling_metrics.get("max_drawdown", 0.0)

    if total_trades < min_trades:
        reasons.append(f"Only {total_trades} trades in rolling window (min {min_trades})")
    if win_rate < min_win_rate:
        reasons.append(f"Win rate {win_rate:.1%} below {min_win_rate:.0%}")
    if sharpe_ratio < min_sharpe:
        reasons.append(f"Sharpe {sharpe_ratio:.2f} below {min_sharpe:.2f}")
    if rolling_drawdown > max_drawdown:
        reasons.append(f"Max drawdown {rolling_drawdown:.1%} above {max_drawdown:.0%}")

    return len(reasons) == 0, reasons

async def run_evaluation():
    """
    Enhanced evaluation job that analyzes both costs and trading performance.
    """
    logger = get_trading_logger("evaluation")
    logger.info("Starting enhanced evaluation job.")
    
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    try:
        # Analyze AI costs and efficiency
        cost_analysis = await analyze_ai_costs(db_manager)
        
        # Analyze trading performance
        performance_analysis = await analyze_trading_performance(db_manager)
        rolling_metrics = performance_analysis.get("rolling_metrics", {})
        ready_for_live, readiness_reasons = _assess_live_readiness(rolling_metrics)
        
        # Generate overall system health summary
        daily_cost = cost_analysis['daily_costs'][datetime.now().strftime('%Y-%m-%d')]['cost']
        budget_utilization = daily_cost / settings.trading.daily_ai_budget
        
        health_status = "🟢 HEALTHY"
        if budget_utilization > 0.9:
            health_status = "🔴 OVER BUDGET"
        elif budget_utilization > 0.7:
            health_status = "🟡 HIGH USAGE"
        
        logger.info(
            "System Health Summary",
            status=health_status,
            daily_budget_used=f"{budget_utilization:.1%}",
            total_recommendations=len(cost_analysis['recommendations']),
            open_positions=performance_analysis.get('position_stats', [0])[0] if performance_analysis.get('position_stats') else 0,
            ready_for_live=ready_for_live,
            live_readiness_reasons=readiness_reasons
        )

        health_score = max(
            0.0,
            min(
                100.0,
                100.0
                * (
                    0.5 * rolling_metrics.get("win_rate", 0.0)
                    + 0.3 * (1.0 - rolling_metrics.get("max_drawdown", 0.0))
                    + 0.2 * min(2.0, max(0.0, rolling_metrics.get("sharpe_ratio", 0.0))) / 2.0
                )
            )
        )

        async with aiosqlite.connect(db_manager.db_path) as db:
            await db.execute("""
                INSERT INTO analysis_reports
                (timestamp, health_score, critical_issues, warnings, action_items, report_file,
                 rolling_win_rate, rolling_max_drawdown, rolling_sharpe, ready_for_live)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                health_score,
                0,
                len(cost_analysis.get("recommendations", [])),
                0,
                None,
                rolling_metrics.get("win_rate", 0.0),
                rolling_metrics.get("max_drawdown", 0.0),
                rolling_metrics.get("sharpe_ratio", 0.0),
                int(ready_for_live)
            ))
            await db.commit()
        
        if not ready_for_live:
            logger.warning(
                "Live trading readiness check failed",
                reasons=readiness_reasons
            )
        
        # If costs are high, suggest immediate actions
        if budget_utilization > 0.8:
            logger.warning(
                "HIGH COST ALERT: Consider immediate actions",
                suggestions=[
                    "Increase analysis_cooldown_hours",
                    "Raise min_volume_for_ai_analysis threshold", 
                    "Enable skip_news_for_low_volume",
                    "Reduce max_analyses_per_market_per_day"
                ]
            )
    
    except Exception as e:
        logger.error("Error in evaluation job", error=str(e), exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_evaluation())
