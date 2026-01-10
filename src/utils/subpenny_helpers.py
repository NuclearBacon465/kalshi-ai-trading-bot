"""
Subpenny pricing helpers for Kalshi API.

CRITICAL: As of Jan 15, 2026, Kalshi removes cent-denominated price fields.
This module provides helpers to safely transition to *_dollars fields.

Per Kalshi API Changelog:
- Deprecated: yes_bid, yes_ask, no_bid, no_ask, last_price (in cents)
- Use instead: yes_bid_dollars, yes_ask_dollars, etc. (fixed-point strings)
- market_positions values are in centi-cents (divide by 10,000)
"""

from typing import Dict, Any, Optional


def get_price_dollars(data: Dict[str, Any], field: str, default: float = 0.0) -> float:
    """
    Get price in dollars, preferring *_dollars field over deprecated cent field.

    This function safely handles the transition from cent-based to dollar-based pricing.
    It will try the new *_dollars field first, then fall back to the old cent field.

    Args:
        data: Market, order, or trade data dict
        field: Base field name (e.g., 'yes_bid', 'last_price', 'yes_ask')
        default: Default value if neither field exists

    Returns:
        Price in dollars as float

    Examples:
        >>> market = {'yes_bid_dollars': '0.5500'}
        >>> get_price_dollars(market, 'yes_bid')
        0.55

        >>> market = {'yes_bid': 55}  # Old format (deprecated)
        >>> get_price_dollars(market, 'yes_bid')
        0.55

        >>> market = {}
        >>> get_price_dollars(market, 'yes_bid', default=0.5)
        0.5
    """
    # Try *_dollars field first (new format, preferred)
    dollars_field = f"{field}_dollars"
    if dollars_field in data and data[dollars_field] is not None:
        try:
            return float(data[dollars_field])
        except (ValueError, TypeError):
            pass

    # Fallback to cent field (deprecated, will be removed Jan 15, 2026)
    if field in data and data[field] is not None:
        try:
            return data[field] / 100.0
        except (ValueError, TypeError, ZeroDivisionError):
            pass

    return default


def convert_centi_cents_to_dollars(centi_cents: Optional[int]) -> float:
    """
    Convert centi-cents to dollars.

    Used for market_positions WebSocket channel values:
    - position_cost (in centi-cents)
    - realized_pnl (in centi-cents)
    - fees_paid (in centi-cents)

    Per Kalshi docs: "All monetary values are returned in centi-cents (1/10,000th of a dollar)"

    Args:
        centi_cents: Value in centi-cents (1/10,000 of a dollar)

    Returns:
        Value in dollars

    Examples:
        >>> convert_centi_cents_to_dollars(55000)
        5.5

        >>> convert_centi_cents_to_dollars(10000)
        1.0

        >>> convert_centi_cents_to_dollars(None)
        0.0
    """
    if centi_cents is None:
        return 0.0

    try:
        return centi_cents / 10000.0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def convert_dollars_to_cents(dollars: float) -> int:
    """
    Convert dollars to cents for order placement.

    NOTE: Kalshi currently requires prices in cents for order placement.
    This may change when subpenny pricing for orders is introduced.

    Args:
        dollars: Price in dollars

    Returns:
        Price in cents (rounded to nearest cent)

    Examples:
        >>> convert_dollars_to_cents(0.55)
        55

        >>> convert_dollars_to_cents(1.234)
        123
    """
    try:
        return int(round(dollars * 100))
    except (ValueError, TypeError):
        return 0


def get_spread_dollars(market: Dict[str, Any], side: str = 'yes') -> float:
    """
    Calculate bid-ask spread in dollars.

    Args:
        market: Market data dict
        side: 'yes' or 'no'

    Returns:
        Spread in dollars (ask - bid)

    Examples:
        >>> market = {'yes_bid_dollars': '0.5400', 'yes_ask_dollars': '0.5600'}
        >>> get_spread_dollars(market, 'yes')
        0.02
    """
    bid = get_price_dollars(market, f'{side}_bid')
    ask = get_price_dollars(market, f'{side}_ask')

    if bid > 0 and ask > 0:
        return ask - bid

    return 0.0


def get_mid_price_dollars(market: Dict[str, Any], side: str = 'yes') -> float:
    """
    Calculate mid-price (average of bid and ask) in dollars.

    Args:
        market: Market data dict
        side: 'yes' or 'no'

    Returns:
        Mid-price in dollars

    Examples:
        >>> market = {'yes_bid_dollars': '0.5400', 'yes_ask_dollars': '0.5600'}
        >>> get_mid_price_dollars(market, 'yes')
        0.55
    """
    bid = get_price_dollars(market, f'{side}_bid')
    ask = get_price_dollars(market, f'{side}_ask')

    if bid > 0 and ask > 0:
        return (bid + ask) / 2.0

    # Fallback to last price if bid/ask not available
    return get_price_dollars(market, 'last_price')


def format_price_for_display(dollars: float, decimals: int = 4) -> str:
    """
    Format price for display with appropriate decimal places.

    Subpenny pricing uses up to 4 decimal places.

    Args:
        dollars: Price in dollars
        decimals: Number of decimal places (default 4 for subpenny)

    Returns:
        Formatted price string

    Examples:
        >>> format_price_for_display(0.5523)
        '$0.5523'

        >>> format_price_for_display(1.2, decimals=2)
        '$1.20'
    """
    return f"${dollars:.{decimals}f}"


def is_using_subpenny_format(data: Dict[str, Any]) -> bool:
    """
    Check if data is using new subpenny format (*_dollars fields).

    Useful for logging/debugging transition from old to new format.

    Args:
        data: Market or order data dict

    Returns:
        True if using *_dollars fields, False if using old cent fields

    Examples:
        >>> is_using_subpenny_format({'yes_bid_dollars': '0.55'})
        True

        >>> is_using_subpenny_format({'yes_bid': 55})
        False
    """
    subpenny_fields = [
        'yes_bid_dollars',
        'yes_ask_dollars',
        'no_bid_dollars',
        'no_ask_dollars',
        'last_price_dollars'
    ]

    return any(field in data for field in subpenny_fields)


# Convenience mapping for common price fields
PRICE_FIELD_MAPPING = {
    # Market prices
    'yes_bid': 'yes_bid_dollars',
    'yes_ask': 'yes_ask_dollars',
    'no_bid': 'no_bid_dollars',
    'no_ask': 'no_ask_dollars',
    'last_price': 'last_price_dollars',

    # Order fees
    'taker_fees': 'taker_fees_dollars',
    'maker_fees': 'maker_fees_dollars',

    # Trade prices
    'yes_price': 'yes_price_dollars',
    'no_price': 'no_price_dollars',
}


def get_all_prices_dollars(market: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract all available prices from market data in dollars.

    Convenience function to get all prices at once.

    Args:
        market: Market data dict

    Returns:
        Dict with all available prices in dollars

    Examples:
        >>> market = {
        ...     'yes_bid_dollars': '0.5400',
        ...     'yes_ask_dollars': '0.5600',
        ...     'no_bid_dollars': '0.4400',
        ...     'no_ask_dollars': '0.4600'
        ... }
        >>> prices = get_all_prices_dollars(market)
        >>> prices['yes_bid']
        0.54
        >>> prices['yes_ask']
        0.56
    """
    prices = {}

    for old_field, new_field in PRICE_FIELD_MAPPING.items():
        prices[old_field] = get_price_dollars(market, old_field)

    # Add derived values
    if 'yes_bid' in prices and 'yes_ask' in prices:
        prices['yes_spread'] = get_spread_dollars(market, 'yes')
        prices['yes_mid'] = get_mid_price_dollars(market, 'yes')

    if 'no_bid' in prices and 'no_ask' in prices:
        prices['no_spread'] = get_spread_dollars(market, 'no')
        prices['no_mid'] = get_mid_price_dollars(market, 'no')

    return prices
