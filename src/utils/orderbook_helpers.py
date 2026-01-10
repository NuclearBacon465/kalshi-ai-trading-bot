"""
Orderbook analysis utilities for Kalshi API.

Per Kalshi Reference docs: "Kalshi's orderbook only returns bids, not asks.
This is because in binary prediction markets, there's a reciprocal relationship
between YES and NO positions."

Key Insight:
- A YES BID at price X = NO ASK at price (100 - X)
- A NO BID at price Y = YES ASK at price (100 - Y)

This module provides helpers to work with this structure.
"""

from typing import Dict, Any, List, Tuple, Optional


class OrderbookAnalyzer:
    """
    Analyze Kalshi orderbooks and calculate derived values.

    Per Kalshi Reference: orderbook arrays are [price, quantity] tuples,
    sorted by price in ascending order. The highest bid (best bid) is the
    last element in each array.
    """

    def __init__(self, orderbook_data: Dict[str, Any]):
        """
        Initialize orderbook analyzer.

        Args:
            orderbook_data: Response from get_orderbook() endpoint

        Example:
            orderbook = await client.get_orderbook("KXHIGHNY-24JAN01-T60")
            analyzer = OrderbookAnalyzer(orderbook)
            best_prices = analyzer.get_best_prices()
        """
        self.orderbook = orderbook_data.get('orderbook', {})
        self.yes_bids = self.orderbook.get('yes', [])  # [[price, qty], ...]
        self.no_bids = self.orderbook.get('no', [])    # [[price, qty], ...]

    def get_best_prices(self) -> Dict[str, Optional[int]]:
        """
        Get best bid and implied ask prices for both sides.

        Returns:
            Dict with best_yes_bid, best_yes_ask, best_no_bid, best_no_ask (in cents)

        Example:
            >>> prices = analyzer.get_best_prices()
            >>> print(f"Best YES: bid={prices['best_yes_bid']}¢, ask={prices['best_yes_ask']}¢")
        """
        result = {
            'best_yes_bid': None,
            'best_yes_ask': None,
            'best_no_bid': None,
            'best_no_ask': None
        }

        # Best bids are the last (highest) elements
        if self.yes_bids:
            result['best_yes_bid'] = self.yes_bids[-1][0]
            # Per Kalshi Reference: NO ASK = 100 - YES BID
            result['best_no_ask'] = 100 - result['best_yes_bid']

        if self.no_bids:
            result['best_no_bid'] = self.no_bids[-1][0]
            # Per Kalshi Reference: YES ASK = 100 - NO BID
            result['best_yes_ask'] = 100 - result['best_no_bid']

        return result

    def get_spread(self) -> Dict[str, Optional[int]]:
        """
        Calculate bid-ask spreads for both sides.

        Returns:
            Dict with yes_spread and no_spread (in cents)

        Example:
            >>> spreads = analyzer.get_spread()
            >>> print(f"YES spread: {spreads['yes_spread']}¢")
        """
        prices = self.get_best_prices()

        yes_spread = None
        if prices['best_yes_bid'] is not None and prices['best_yes_ask'] is not None:
            yes_spread = prices['best_yes_ask'] - prices['best_yes_bid']

        no_spread = None
        if prices['best_no_bid'] is not None and prices['best_no_ask'] is not None:
            no_spread = prices['best_no_ask'] - prices['best_no_bid']

        return {
            'yes_spread': yes_spread,
            'no_spread': no_spread
        }

    def calculate_depth(self, depth_cents: int = 5) -> Dict[str, int]:
        """
        Calculate total volume within X cents of best bid.

        Per Kalshi Reference: "Calculate total volume within X cents of best bid"

        Args:
            depth_cents: Distance from best bid to include (default: 5¢)

        Returns:
            Dict with yes_depth and no_depth (total contracts)

        Example:
            >>> depth = analyzer.calculate_depth(depth_cents=5)
            >>> print(f"YES depth within 5¢: {depth['yes_depth']} contracts")
        """
        yes_depth = 0
        no_depth = 0

        # YES side depth (iterate backwards from best bid)
        if self.yes_bids:
            best_yes = self.yes_bids[-1][0]  # Last element is highest
            for price, quantity in reversed(self.yes_bids):
                if best_yes - price <= depth_cents:
                    yes_depth += quantity
                else:
                    break

        # NO side depth (iterate backwards from best bid)
        if self.no_bids:
            best_no = self.no_bids[-1][0]  # Last element is highest
            for price, quantity in reversed(self.no_bids):
                if best_no - price <= depth_cents:
                    no_depth += quantity
                else:
                    break

        return {
            'yes_depth': yes_depth,
            'no_depth': no_depth
        }

    def get_total_liquidity(self) -> Dict[str, int]:
        """
        Get total contracts available across entire orderbook.

        Returns:
            Dict with yes_liquidity and no_liquidity (total contracts)
        """
        yes_liquidity = sum(qty for _, qty in self.yes_bids) if self.yes_bids else 0
        no_liquidity = sum(qty for _, qty in self.no_bids) if self.no_bids else 0

        return {
            'yes_liquidity': yes_liquidity,
            'no_liquidity': no_liquidity
        }

    def find_execution_price(self, side: str, contracts: int) -> Optional[float]:
        """
        Estimate average execution price for a market order.

        Args:
            side: "yes" or "no"
            contracts: Number of contracts to buy/sell

        Returns:
            Average execution price in cents (None if insufficient liquidity)

        Example:
            >>> avg_price = analyzer.find_execution_price("yes", 100)
            >>> print(f"Avg price for 100 YES contracts: {avg_price:.2f}¢")
        """
        if side.lower() == "yes":
            bids = self.yes_bids
        elif side.lower() == "no":
            bids = self.no_bids
        else:
            raise ValueError(f"Invalid side: {side}. Must be 'yes' or 'no'")

        if not bids:
            return None

        remaining = contracts
        total_cost = 0

        # Walk backwards from best bid (highest price)
        for price, quantity in reversed(bids):
            take = min(remaining, quantity)
            total_cost += price * take
            remaining -= take

            if remaining <= 0:
                break

        if remaining > 0:
            # Insufficient liquidity
            return None

        return total_cost / contracts

    def get_price_levels(self, side: str, num_levels: int = 10) -> List[Tuple[int, int]]:
        """
        Get top N price levels for a side.

        Args:
            side: "yes" or "no"
            num_levels: Number of levels to return (from best bid downward)

        Returns:
            List of (price, quantity) tuples

        Example:
            >>> levels = analyzer.get_price_levels("yes", 5)
            >>> for price, qty in levels:
            >>>     print(f"  {price}¢: {qty} contracts")
        """
        if side.lower() == "yes":
            bids = self.yes_bids
        elif side.lower() == "no":
            bids = self.no_bids
        else:
            raise ValueError(f"Invalid side: {side}. Must be 'yes' or 'no'")

        # Return top N levels (from end of list, which has highest bids)
        return list(reversed(bids[-num_levels:]))


def display_orderbook_summary(orderbook_data: Dict[str, Any]) -> str:
    """
    Generate human-readable orderbook summary.

    Args:
        orderbook_data: Response from get_orderbook() endpoint

    Returns:
        Formatted string with orderbook analysis

    Example:
        >>> orderbook = await client.get_orderbook("KXHIGHNY-24JAN01-T60")
        >>> print(display_orderbook_summary(orderbook))
    """
    analyzer = OrderbookAnalyzer(orderbook_data)
    prices = analyzer.get_best_prices()
    spreads = analyzer.get_spread()
    depth = analyzer.calculate_depth(5)
    liquidity = analyzer.get_total_liquidity()

    lines = [
        "=" * 60,
        "ORDERBOOK SUMMARY",
        "=" * 60,
        "",
        "Best Prices:",
        f"  YES: Bid {prices['best_yes_bid']}¢ | Ask {prices['best_yes_ask']}¢ (spread: {spreads['yes_spread']}¢)",
        f"  NO:  Bid {prices['best_no_bid']}¢ | Ask {prices['best_no_ask']}¢ (spread: {spreads['no_spread']}¢)",
        "",
        "Market Depth (within 5¢ of best):",
        f"  YES: {depth['yes_depth']} contracts",
        f"  NO:  {depth['no_depth']} contracts",
        "",
        "Total Liquidity:",
        f"  YES: {liquidity['yes_liquidity']} contracts",
        f"  NO:  {liquidity['no_liquidity']} contracts",
        "",
        "=" * 60
    ]

    return "\n".join(lines)


# Convenience functions for one-liners

def get_best_yes_bid(orderbook_data: Dict[str, Any]) -> Optional[int]:
    """Get best YES bid price (highest YES bid)."""
    yes_bids = orderbook_data.get('orderbook', {}).get('yes', [])
    return yes_bids[-1][0] if yes_bids else None


def get_best_yes_ask(orderbook_data: Dict[str, Any]) -> Optional[int]:
    """Get implied YES ask price (100 - best NO bid)."""
    no_bids = orderbook_data.get('orderbook', {}).get('no', [])
    return 100 - no_bids[-1][0] if no_bids else None


def get_best_no_bid(orderbook_data: Dict[str, Any]) -> Optional[int]:
    """Get best NO bid price (highest NO bid)."""
    no_bids = orderbook_data.get('orderbook', {}).get('no', [])
    return no_bids[-1][0] if no_bids else None


def get_best_no_ask(orderbook_data: Dict[str, Any]) -> Optional[int]:
    """Get implied NO ask price (100 - best YES bid)."""
    yes_bids = orderbook_data.get('orderbook', {}).get('yes', [])
    return 100 - yes_bids[-1][0] if yes_bids else None


def calculate_yes_spread(orderbook_data: Dict[str, Any]) -> Optional[int]:
    """Calculate YES spread (ask - bid)."""
    bid = get_best_yes_bid(orderbook_data)
    ask = get_best_yes_ask(orderbook_data)
    return ask - bid if bid is not None and ask is not None else None


def calculate_no_spread(orderbook_data: Dict[str, Any]) -> Optional[int]:
    """Calculate NO spread (ask - bid)."""
    bid = get_best_no_bid(orderbook_data)
    ask = get_best_no_ask(orderbook_data)
    return ask - bid if bid is not None and ask is not None else None
