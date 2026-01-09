# COMPREHENSIVE KALSHI API IMPLEMENTATION AUDIT

**Date:** 2026-01-09
**Status:** CRITICAL FIXES REQUIRED

---

## 🚨 CRITICAL ISSUES FOUND

### 1. **WebSocket Subscribe Format is WRONG** ❌

**Current Implementation:**
```python
message = {
    "type": "subscribe",
    "channel": "ticker",
    "params": {
        "tickers": [ticker]
    }
}
```

**Correct Format (Per Official Docs):**
```python
message = {
    "cmd": "subscribe",
    "params": {
        "channels": ["ticker"],
        "market_tickers": [ticker]
    }
}
```

**Impact:** This is WHY WebSocket returns HTTP 400! Wrong command format!

**Files to Fix:**
- `src/clients/kalshi_websocket.py` (lines 133-139, 159-163, 181-187)

---

### 2. **WebSocket URL Incorrect** ❌

**Current:** `wss://api.elections.kalshi.com/trade-api/ws/v2`
**Correct:** `wss://api.elections.kalshi.com` (NO /trade-api/ws/v2 in URL!)

**Per Docs:** "WSS wss://api.elections.kalshi.com"

**Auth Path:** Still use `/trade-api/ws/v2` for signature, but NOT in WebSocket URL

**Files to Fix:**
- `src/clients/kalshi_websocket.py` (line 43)

---

### 3. **Missing WebSocket Channels** ⚠️

Currently implemented:
- ✅ `ticker`
- ✅ `orderbook_delta`
- ✅ `fill`
- ✅ `trade`

**Missing Channels:**
- ❌ `market_positions` - Real-time position updates (authenticated)
- ❌ `market_lifecycle_v2` - Market state changes
- ❌ `communications` - RFQ/quote notifications
- ❌ `multivariate` - Multivariate lookups

**Impact:** Missing critical data streams for portfolio tracking and market events

---

### 4. **Subpenny Pricing NOT Implemented** ❌

**BREAKING CHANGE:** Cent fields removed January 15, 2026 (6 DAYS!)

**Deprecated Fields (Must Stop Using):**
- `yes_bid`, `yes_ask`, `no_bid`, `no_ask` → Use `*_dollars` versions
- `last_price` → Use `last_price_dollars`
- `tick_size` → Use `price_level_structure`
- `notional_value`, `liquidity` → Use `*_dollars` versions

**Must Use:**
- `yes_bid_dollars`, `yes_ask_dollars`
- `no_bid_dollars`, `no_ask_dollars`
- `last_price_dollars`
- `taker_fees_dollars`, `maker_fees_dollars`
- `yes_price_dollars`, `no_price_dollars`

**Files Using Deprecated Fields (16 files!):**
```
beast_mode_bot.py
src/utils/adversarial_detection.py
src/utils/price_history.py
src/clients/xai_client.py
src/jobs/ingest.py
src/strategies/portfolio_optimization.py
src/strategies/quick_flip_scalping.py
src/utils/websocket_manager.py
src/strategies/market_making.py
test_live_trading_deep.py
test_your_actual_setup.py
test_deep_validation.py
tests/test_direct_order_placement.py
tests/test_helpers.py
tests/test_live_order_execution.py
tests/test_real_order_placement.py
```

---

### 5. **Missing REST API Endpoints** ⚠️

**Not Implemented:**
- ❌ `GET /portfolio/settlements` - For settled positions (required since Dec 11, 2025)
- ❌ `GET /events/multivariate` - Multivariate events (required since Nov 6, 2025)
- ❌ `GET /markets/candlesticks` - Batch candlesticks (Nov 27, 2025)
- ❌ `GET /portfolio/orders/queue_positions` - Queue positions (Aug 1, 2025)

**Impact:** GET /portfolio/positions only returns UNSETTLED positions now

---

### 6. **Deprecated REST Fields Still Used** ⚠️

**Will be removed January 8, 2026 (TOMORROW!):**
- `category` field in Market responses
- `risk_limit_cents` field in Market responses

**Must Remove Usage Of:**
- Any code checking `market['category']`
- Any code using `market['risk_limit_cents']`

---

### 7. **WebSocket List Subscriptions Not Implemented** ⚠️

**Missing Command:**
```python
{
    "cmd": "list_subscriptions"
}
```

**Response:**
```python
{
    "type": "subscriptions",
    "sid": "subscription_id",
    "subscriptions": [
        {
            "channel": "ticker",
            "market_tickers": ["TICKER1", "TICKER2"]
        }
    ]
}
```

**Use Case:** Debug what channels are active, verify subscriptions

---

### 8. **WebSocket Unsubscribe Not Implemented** ⚠️

**Missing Command:**
```python
{
    "cmd": "unsubscribe",
    "params": {
        "channels": ["ticker"],
        "market_tickers": [ticker]
    }
}
```

**Impact:** Can't stop receiving data, wasting bandwidth

---

### 9. **Market Positions Values in Centi-Cents** ⚠️

**Per Docs:** Values in `market_positions` WebSocket channel are in **centi-cents** (divide by 10,000):
- `position_cost` → Divide by 10,000
- `realized_pnl` → Divide by 10,000
- `fees_paid` → Divide by 10,000

**Not Currently Handled:** No code to convert centi-cents to dollars

---

### 10. **Missing MVE Filter Support** ⚠️

**GET /markets now supports `mve_filter` parameter:**
- `"only"` - Only multivariate events
- `"exclude"` - Exclude multivariate events
- Omit - All events (default)

**Not implemented in `get_markets()` method**

---

## 📊 PRIORITY FIXES

### Priority 1: CRITICAL (Fix Today)
1. ✅ Fix WebSocket URL
2. ✅ Fix WebSocket subscribe command format
3. ✅ Test WebSocket connection (should work after fixes)

### Priority 2: URGENT (Fix This Week)
4. ⚠️ Implement subpenny pricing (`*_dollars` fields)
5. ⚠️ Remove deprecated field usage
6. ⚠️ Add GET /portfolio/settlements endpoint
7. ⚠️ Add missing WebSocket channels

### Priority 3: IMPORTANT (Fix This Month)
8. ⚠️ Add WebSocket list_subscriptions command
9. ⚠️ Add WebSocket unsubscribe command
10. ⚠️ Add GET /events/multivariate endpoint
11. ⚠️ Add mve_filter support
12. ⚠️ Handle centi-cents conversion

---

## 🔧 IMPLEMENTATION PLAN

### Step 1: Fix WebSocket Connection (IMMEDIATE)

**File:** `src/clients/kalshi_websocket.py`

**Changes:**
```python
# Line 43: Fix WebSocket URL
self.ws_url = "wss://api.elections.kalshi.com"

# Lines 133-139: Fix subscribe_ticker
message = {
    "cmd": "subscribe",
    "params": {
        "channels": ["ticker"],
        "market_tickers": [ticker]
    }
}

# Lines 159-163: Fix subscribe_fills
message = {
    "cmd": "subscribe",
    "params": {
        "channels": ["fill"]
    }
}

# Lines 181-187: Fix subscribe_orderbook
message = {
    "cmd": "subscribe",
    "params": {
        "channels": ["orderbook_delta"],
        "market_tickers": [ticker]
    }
}
```

### Step 2: Add Missing WebSocket Channels

**Add methods:**
```python
async def subscribe_market_positions(self, tickers: Optional[List[str]] = None):
    """Subscribe to real-time position updates."""
    message = {
        "cmd": "subscribe",
        "params": {
            "channels": ["market_positions"]
        }
    }
    if tickers:
        message["params"]["market_tickers"] = tickers
    await self.websocket.send(json.dumps(message))

async def subscribe_market_lifecycle(self, tickers: Optional[List[str]] = None):
    """Subscribe to market state changes."""
    message = {
        "cmd": "subscribe",
        "params": {
            "channels": ["market_lifecycle_v2"]
        }
    }
    if tickers:
        message["params"]["market_tickers"] = tickers
    await self.websocket.send(json.dumps(message))

async def list_subscriptions(self):
    """List all active subscriptions."""
    message = {"cmd": "list_subscriptions"}
    await self.websocket.send(json.dumps(message))

async def unsubscribe(self, channels: List[str], tickers: Optional[List[str]] = None):
    """Unsubscribe from channels."""
    message = {
        "cmd": "unsubscribe",
        "params": {
            "channels": channels
        }
    }
    if tickers:
        message["params"]["market_tickers"] = tickers
    await self.websocket.send(json.dumps(message))
```

### Step 3: Implement Subpenny Pricing Helper

**Create:** `src/utils/subpenny_helpers.py`

```python
"""
Subpenny pricing helpers for Kalshi API.
Handles conversion between cents and dollars formats.
"""

def get_price_dollars(market: dict, field: str, default: float = 0.0) -> float:
    """
    Get price in dollars, preferring *_dollars field over deprecated cent field.

    Args:
        market: Market data dict
        field: Base field name (e.g., 'yes_bid', 'last_price')
        default: Default value if neither field exists

    Returns:
        Price in dollars as float
    """
    # Try *_dollars field first (new format)
    dollars_field = f"{field}_dollars"
    if dollars_field in market:
        value = market[dollars_field]
        return float(value) if value is not None else default

    # Fallback to cent field (deprecated)
    if field in market:
        value = market[field]
        return (value / 100.0) if value is not None else default

    return default


def convert_centi_cents_to_dollars(centi_cents: int) -> float:
    """
    Convert centi-cents to dollars.
    Used for market_positions WebSocket values.

    Args:
        centi_cents: Value in centi-cents (1/10,000 of a dollar)

    Returns:
        Value in dollars
    """
    return centi_cents / 10000.0
```

### Step 4: Update All Price Usage

**Pattern to Replace:**
```python
# OLD (deprecated)
yes_bid = market['yes_bid'] / 100.0

# NEW (subpenny-safe)
from src.utils.subpenny_helpers import get_price_dollars
yes_bid = get_price_dollars(market, 'yes_bid')
```

### Step 5: Add Missing REST Endpoints

**File:** `src/clients/kalshi_client.py`

```python
async def get_settlements(
    self,
    limit: int = 100,
    cursor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get settled positions.

    Args:
        limit: Number of settlements to return
        cursor: Pagination cursor

    Returns:
        Settlements data
    """
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor

    return await self._make_authenticated_request(
        "GET",
        "/trade-api/v2/portfolio/settlements",
        params=params
    )


async def get_multivariate_events(
    self,
    series_ticker: Optional[str] = None,
    limit: int = 200
) -> Dict[str, Any]:
    """
    Get multivariate events (combos).

    Args:
        series_ticker: Filter by series
        limit: Number of events to return

    Returns:
        Multivariate events data
    """
    params = {"limit": limit}
    if series_ticker:
        params["series_ticker"] = series_ticker

    return await self._make_authenticated_request(
        "GET",
        "/trade-api/v2/events/multivariate",
        params=params
    )
```

---

## 🧪 TESTING PLAN

### Test 1: WebSocket Connection (After Fixes)
```bash
python -c "
import asyncio
from src.clients.kalshi_websocket import KalshiWebSocketClient

async def test():
    ws = KalshiWebSocketClient()
    connected = await ws.connect()
    print(f'Connected: {connected}')

    # Should work now!
    await ws.subscribe_ticker('KXBTC-24JAN15-T45000')
    await asyncio.sleep(5)

asyncio.run(test())
"
```

### Test 2: Subpenny Pricing
```bash
python -c "
import asyncio
from src.clients.kalshi_client import KalshiClient
from src.utils.subpenny_helpers import get_price_dollars

async def test():
    client = KalshiClient()
    markets = await client.get_markets(limit=1, status='open')

    if markets['markets']:
        market = markets['markets'][0]

        # Test subpenny helper
        yes_bid = get_price_dollars(market, 'yes_bid')
        yes_ask = get_price_dollars(market, 'yes_ask')

        print(f'Yes Bid: ${yes_bid:.4f}')
        print(f'Yes Ask: ${yes_ask:.4f}')

        # Check if using new format
        if 'yes_bid_dollars' in market:
            print('✅ Using subpenny format')
        else:
            print('⚠️ Still using cent format (deprecated)')

asyncio.run(test())
"
```

### Test 3: Settlements Endpoint
```bash
python -c "
import asyncio
from src.clients.kalshi_client import KalshiClient

async def test():
    client = KalshiClient()
    settlements = await client.get_settlements(limit=10)
    print(f'Settlements: {len(settlements.get(\"settlements\", []))}')

asyncio.run(test())
"
```

---

## 📈 SUCCESS CRITERIA

- ✅ WebSocket connects without HTTP 400
- ✅ Can subscribe to ticker, fill, orderbook channels
- ✅ Can list subscriptions
- ✅ Can unsubscribe from channels
- ✅ All 16 files updated to use `*_dollars` fields
- ✅ No usage of deprecated `category` or `risk_limit_cents`
- ✅ GET /portfolio/settlements works
- ✅ Subpenny helper functions tested
- ✅ All tests pass with new format

---

## ⚠️ BREAKING CHANGES TIMELINE

- **January 8, 2026 (TOMORROW):** `category`, `risk_limit_cents` removed
- **January 15, 2026 (6 DAYS):** All cent-denominated price fields removed

**URGENT ACTION REQUIRED!**
