"""
Kalshi API client for trading operations.
Handles authentication, market data, and trade execution.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlencode

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from src.config.settings import settings
from src.utils.logging_setup import TradingLoggerMixin
from src.utils.health import record_failure


class KalshiAPIError(Exception):
    """Custom exception for Kalshi API errors."""
    pass


class KalshiClient(TradingLoggerMixin):
    """
    Kalshi API client for automated trading.
    Handles authentication, market data retrieval, and trade execution.

    Rate Limits (per Kalshi Reference docs):
    - Basic tier: 20 read/sec, 10 write/sec (default on signup)
    - Advanced tier: 30 read/sec, 30 write/sec (via typeform)
    - Premier tier: 100 read/sec, 100 write/sec (3.75% volume + technical review)
    - Prime tier: 400 read/sec, 400 write/sec (7.5% volume + technical review)

    Write-limited endpoints:
    - CreateOrder, CancelOrder, AmendOrder, DecreaseOrder
    - BatchCreateOrders (each order = 1 transaction)
    - BatchCancelOrders (each cancel = 0.2 transactions)
    """

    _rate_semaphore = asyncio.Semaphore(5)
    _rate_lock = asyncio.Lock()
    _last_request_ts = 0.0
    _min_request_interval = 0.35  # ~2.86 req/sec (conservative for Basic tier)

    def __init__(
        self,
        api_key: Optional[str] = None,
        private_key_path: str = "kalshi_private_key",
        max_retries: int = 5,
        backoff_factor: float = 0.5
    ):
        """
        Initialize Kalshi client.

        Args:
            api_key: Kalshi API key (Key ID from the API key generation)
            private_key_path: Path to private key file (SECURITY: Store securely, never expose)
            max_retries: Maximum number of retries for failed requests
            backoff_factor: Factor for exponential backoff

        Note:
            Per Kalshi Quick Start docs: Despite the 'elections' subdomain,
            api.elections.kalshi.com provides access to ALL Kalshi markets
            (economics, climate, technology, entertainment, etc.)
        """
        self.api_key = api_key or settings.api.kalshi_api_key
        self.base_url = settings.api.kalshi_base_url
        self.private_key_path = private_key_path
        self.private_key = None
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        # Load private key lazily on first authenticated request
        
        # HTTP client with timeouts
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
        
        self.logger.info("Kalshi client initialized", api_key_length=len(self.api_key) if self.api_key else 0)

    async def _acquire_rate_limit(self) -> None:
        """Acquire shared rate limit slot to reduce 429s."""
        await KalshiClient._rate_semaphore.acquire()
        try:
            async with KalshiClient._rate_lock:
                now = time.monotonic()
                elapsed = now - KalshiClient._last_request_ts
                wait_time = KalshiClient._min_request_interval - elapsed
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                KalshiClient._last_request_ts = time.monotonic()
        except Exception:
            KalshiClient._rate_semaphore.release()
            raise
    
    def _load_private_key(self) -> None:
        """Load private key from file."""
        try:
            if self.private_key is not None:
                return
            private_key_path = Path(self.private_key_path)
            if not private_key_path.exists():
                raise KalshiAPIError(f"Private key file not found: {self.private_key_path}")
            
            with open(private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
            self.logger.info("Private key loaded successfully")
        except Exception as e:
            self.logger.error("Failed to load private key", error=str(e))
            raise KalshiAPIError(f"Failed to load private key: {e}")
    
    def _sign_request(self, timestamp: str, method: str, path: str) -> str:
        """
        Sign request using RSA PSS signing method as per Kalshi API docs.

        Args:
            timestamp: Request timestamp in milliseconds
            method: HTTP method
            path: Request path (query parameters will be stripped automatically)

        Returns:
            Base64 encoded signature
        """
        # CRITICAL: Strip query parameters before signing (per Kalshi Quick Start docs)
        # "Important: Use the path without query parameters. For /portfolio/orders?limit=5,
        # sign only /trade-api/v2/portfolio/orders"
        path_without_query = path.split('?')[0]

        # Create message to sign: timestamp + method + path
        message = timestamp + method.upper() + path_without_query
        message_bytes = message.encode('utf-8')
        
        try:
            # Sign using RSA PSS as per Kalshi documentation
            signature = self.private_key.sign(
                message_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH
                ),
                hashes.SHA256()
            )
            
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            self.logger.error("Failed to sign request", error=str(e))
            raise KalshiAPIError(f"Failed to sign request: {e}")
    
    async def _make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Kalshi API with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON request body
            require_auth: Whether authentication is required
        
        Returns:
            API response data
        """
        # Prepare request
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add authentication headers if required
        if require_auth:
            if self.private_key is None:
                self._load_private_key()
            # Get current timestamp in milliseconds
            timestamp = str(int(time.time() * 1000))
            
            # Create signature
            signature = self._sign_request(timestamp, method, endpoint)
            
            headers.update({
                "KALSHI-ACCESS-KEY": self.api_key,
                "KALSHI-ACCESS-TIMESTAMP": timestamp,
                "KALSHI-ACCESS-SIGNATURE": signature
            })
        
        # Prepare body
        body = None
        if json_data:
            body = json.dumps(json_data, separators=(',', ':'))
        
        # Add query parameters to URL if present
        if params:
            query_string = urlencode(params)
            url = f"{url}?{query_string}"
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(
                    "Making API request",
                    method=method,
                    endpoint=endpoint,
                    has_auth=require_auth,
                    attempt=attempt + 1
                )
                
                # Add delay between requests to prevent 429s (Basic tier: 10 writes/sec)
                await asyncio.sleep(0.1)  # 100ms delay = max 10 requests/second
                
                response = await self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    content=body if body else None
                )

                # Per Kalshi Quick Start: raise_for_status() handles all 2xx codes including
                # 201 (order creation success) and 200 (general success)
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                record_failure("kalshi")
                # Rate limit (429) or server errors (5xx) are worth retrying
                if e.response.status_code == 429 or e.response.status_code >= 500:
                    sleep_time = self.backoff_factor * (2 ** attempt)
                    self.logger.warning(
                        f"API request failed with status {e.response.status_code}. Retrying in {sleep_time:.2f}s...",
                        endpoint=endpoint,
                        attempt=attempt + 1
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    # Don't retry on other client errors (e.g., 400, 401, 404)
                    error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                    self.logger.error("API request failed without retry", error=error_msg, endpoint=endpoint)
                    raise KalshiAPIError(error_msg)
            except Exception as e:
                last_exception = e
                record_failure("kalshi")
                self.logger.warning(f"Request failed with general exception. Retrying...", error=str(e), endpoint=endpoint)
                sleep_time = self.backoff_factor * (2 ** attempt)
                await asyncio.sleep(sleep_time)
        
        raise KalshiAPIError(f"API request failed after {self.max_retries} retries: {last_exception}")
    
    async def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance and portfolio value.

        Per Kalshi API: Returns balance (available for trading) and portfolio_value
        (current value of all positions). Both values in cents.

        Returns:
            Dict with:
            - balance: Available balance in cents (amount available for trading)
            - portfolio_value: Portfolio value in cents (current value of all positions)
            - updated_ts: Unix timestamp of last balance update

        Example:
            result = await client.get_balance()
            balance_dollars = result['balance'] / 100
            portfolio_dollars = result['portfolio_value'] / 100
            print(f"Available: ${balance_dollars:.2f}, Portfolio: ${portfolio_dollars:.2f}")
        """
        return await self._make_authenticated_request("GET", "/trade-api/v2/portfolio/balance")
    
    async def get_positions(
        self,
        ticker: Optional[str] = None,
        event_ticker: Optional[str] = None,
        count_filter: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get portfolio positions.

        Per Kalshi API: Returns current positions (both market-level and
        event-level aggregated positions). Includes market_positions and
        event_positions arrays.

        Args:
            ticker: Filter by market ticker
            event_ticker: Filter by event ticker (comma-separated list, max 10)
            count_filter: Restrict to positions with non-zero values in these fields
                         (comma-separated: "position", "total_traded")
            limit: Number of results per page (default 100, max 1000)
            cursor: Pagination cursor

        Returns:
            Dict with:
            - market_positions: Array of market-level positions
            - event_positions: Array of event-level positions
            - cursor: Pagination cursor for next page

        Example:
            # Get all positions
            result = await client.get_positions()
            for pos in result.get('market_positions', []):
                print(f"{pos['ticker']}: {pos['position']} contracts")

            # Get only positions with actual contracts
            result = await client.get_positions(count_filter="position")

            # Get positions for specific market
            result = await client.get_positions(ticker="KXHIGHNY-24JAN01-T60")
        """
        params = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if count_filter:
            params["count_filter"] = count_filter
        if cursor:
            params["cursor"] = cursor
        return await self._make_authenticated_request("GET", "/trade-api/v2/portfolio/positions", params=params)
    
    async def get_fills(
        self,
        ticker: Optional[str] = None,
        order_id: Optional[str] = None,
        min_ts: Optional[int] = None,
        max_ts: Optional[int] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get order fills (executed trades).

        Per Kalshi API: Returns fill history with execution prices, quantities,
        fees, and timestamps.

        Args:
            ticker: Filter by market ticker
            order_id: Filter by specific order ID
            min_ts: Filter fills after this Unix timestamp
            max_ts: Filter fills before this Unix timestamp
            limit: Number of results per page (default 100, max 200)
            cursor: Pagination cursor

        Returns:
            Dict with:
            - fills: Array of fill objects with trade details
            - cursor: Pagination cursor for next page

        Example:
            # Get recent fills
            result = await client.get_fills(limit=10)
            for fill in result['fills']:
                print(f"{fill['ticker']}: {fill['count']} @ {fill['yes_price']}¢")

            # Get fills for specific market
            result = await client.get_fills(ticker="KXHIGHNY-24JAN01-T60")
        """
        params = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if order_id:
            params["order_id"] = order_id
        if min_ts:
            params["min_ts"] = min_ts
        if max_ts:
            params["max_ts"] = max_ts
        if cursor:
            params["cursor"] = cursor
        return await self._make_authenticated_request("GET", "/trade-api/v2/portfolio/fills", params=params)

    async def get_settlements(
        self,
        ticker: Optional[str] = None,
        event_ticker: Optional[str] = None,
        min_ts: Optional[int] = None,
        max_ts: Optional[int] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get settlement history for resolved markets.

        Per Kalshi API: Returns settlements with ticker, market_result (yes/no),
        counts, costs, revenue, and settlement timestamp.

        Args:
            ticker: Filter by market ticker
            event_ticker: Filter by event ticker (comma-separated list, max 10)
            min_ts: Filter settlements after this Unix timestamp
            max_ts: Filter settlements before this Unix timestamp
            limit: Number of results per page (default 100, max 200)
            cursor: Pagination cursor

        Returns:
            Dict with:
            - settlements: Array of settlement objects
            - cursor: Pagination cursor for next page

        Example:
            # Get recent settlements
            result = await client.get_settlements(limit=10)
            for settlement in result['settlements']:
                print(f"{settlement['ticker']}: {settlement['market_result']}")
                print(f"  Revenue: ${settlement['revenue']/100:.2f}")
        """
        params = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if min_ts:
            params["min_ts"] = min_ts
        if max_ts:
            params["max_ts"] = max_ts
        if cursor:
            params["cursor"] = cursor

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/portfolio/settlements",
            params=params
        )

    async def get_total_resting_order_value(self) -> Dict[str, Any]:
        """
        Get total value of all resting orders across all markets.

        Per Kalshi API: Returns the total value, in cents, of resting orders.
        Only intended for FCM members (rare). If uncertain, likely doesn't apply.

        Returns:
            Dict with:
            - total_resting_order_value: Total value of resting orders in cents

        Example:
            result = await client.get_total_resting_order_value()
            value_dollars = result['total_resting_order_value'] / 100
            print(f"Capital in open orders: ${value_dollars:.2f}")
        """
        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/portfolio/summary/total_resting_order_value"
        )

    async def get_orders(
        self,
        ticker: Optional[str] = None,
        event_ticker: Optional[str] = None,
        min_ts: Optional[int] = None,
        max_ts: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get orders with filtering and pagination.

        Per Kalshi API: Returns orders array with pagination support.
        Restricts to orders with status: resting, canceled, or executed.

        Args:
            ticker: Filter by market ticker
            event_ticker: Filter by event ticker (comma-separated list, max 10)
            min_ts: Filter items after this Unix timestamp
            max_ts: Filter items before this Unix timestamp
            status: Filter by status (resting, canceled, executed)
            limit: Number of results per page (default 100, max 200)
            cursor: Pagination cursor from previous response

        Returns:
            Dict with:
            - orders: Array of order objects
            - cursor: Pagination cursor for next page

        Example:
            # Get all resting orders
            result = await client.get_orders(status="resting", limit=50)
            for order in result['orders']:
                print(f"Order {order['order_id']}: {order['ticker']}")
        """
        params = {"limit": min(limit, 200)}  # Enforce max limit

        if ticker:
            params["ticker"] = ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if min_ts:
            params["min_ts"] = min_ts
        if max_ts:
            params["max_ts"] = max_ts
        if status:
            params["status"] = status
        if cursor:
            params["cursor"] = cursor

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/portfolio/orders",
            params=params
        )

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get a single order by ID.

        Per Kalshi API: Endpoint for getting a single order.

        Args:
            order_id: Order ID to retrieve

        Returns:
            Dict with order object containing all order fields

        Example:
            order = await client.get_order("order-uuid-123")
            print(f"Status: {order['order']['status']}")
            print(f"Fill count: {order['order']['fill_count']}")
        """
        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/portfolio/orders/{order_id}"
        )
    
    async def get_markets(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        min_created_ts: Optional[int] = None,
        max_created_ts: Optional[int] = None,
        max_close_ts: Optional[int] = None,
        min_close_ts: Optional[int] = None,
        min_settled_ts: Optional[int] = None,
        max_settled_ts: Optional[int] = None,
        status: Optional[str] = None,
        tickers: Optional[List[str]] = None,
        mve_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get markets data with filtering and pagination.

        Per Kalshi API: Timestamp filters are mutually exclusive:
        - min/max_created_ts compatible with: unopened, open, empty status
        - min/max_close_ts compatible with: closed, empty status
        - min/max_settled_ts compatible with: settled, empty status

        Args:
            limit: Number of results per page (1-1000, default 100)
            cursor: Pagination cursor
            event_ticker: Filter by event ticker (comma-separated, max 10)
            series_ticker: Filter by series ticker
            min_created_ts: Filter markets created after this Unix timestamp
            max_created_ts: Filter markets created before this Unix timestamp
            max_close_ts: Filter markets closing before this Unix timestamp
            min_close_ts: Filter markets closing after this Unix timestamp
            min_settled_ts: Filter markets settled after this Unix timestamp
            max_settled_ts: Filter markets settled before this Unix timestamp
            status: Filter by status (unopened, open, paused, closed, settled)
            tickers: List of specific market tickers (comma-separated)
            mve_filter: Filter multivariate events ('only' or 'exclude')

        Returns:
            Dict with:
            - markets: Array of market objects
            - cursor: Pagination cursor

        Example:
            # Get open markets
            markets = await client.get_markets(status="open", limit=50)

            # Get markets closing in next 24h
            import time
            tomorrow = int(time.time()) + 86400
            closing_soon = await client.get_markets(
                max_close_ts=tomorrow,
                status="open"
            )
        """
        params = {"limit": limit}

        if cursor:
            params["cursor"] = cursor
        if event_ticker:
            params["event_ticker"] = event_ticker
        if series_ticker:
            params["series_ticker"] = series_ticker
        if min_created_ts:
            params["min_created_ts"] = min_created_ts
        if max_created_ts:
            params["max_created_ts"] = max_created_ts
        if max_close_ts:
            params["max_close_ts"] = max_close_ts
        if min_close_ts:
            params["min_close_ts"] = min_close_ts
        if min_settled_ts:
            params["min_settled_ts"] = min_settled_ts
        if max_settled_ts:
            params["max_settled_ts"] = max_settled_ts
        if status:
            params["status"] = status
        if tickers:
            params["tickers"] = ",".join(tickers)
        if mve_filter:
            params["mve_filter"] = mve_filter

        return await self._make_authenticated_request(
            "GET", "/trade-api/v2/markets", params=params, require_auth=True
        )
    
    async def get_market(self, ticker: str) -> Dict[str, Any]:
        """Get specific market data."""
        return await self._make_authenticated_request(
            "GET", f"/trade-api/v2/markets/{ticker}", require_auth=False
        )

    async def get_events(
        self,
        limit: int = 200,
        cursor: Optional[str] = None,
        with_nested_markets: bool = False,
        with_milestones: bool = False,
        status: Optional[str] = None,
        series_ticker: Optional[str] = None,
        min_close_ts: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get events (excludes multivariate events).

        IMPORTANT: As of Nov 6, 2025, this endpoint EXCLUDES multivariate events.
        Use get_multivariate_events() for combo markets.

        Args:
            limit: Number of results per page (1-200, default 200)
            cursor: Pagination cursor
            with_nested_markets: Include markets array within each event (default false)
            with_milestones: Include related milestones (default false)
            status: Filter by status (open, closed, settled)
            series_ticker: Filter by series ticker
            min_close_ts: Filter events with at least one market closing after this timestamp

        Returns:
            Dict with:
            - events: Array of event objects
            - cursor: Pagination cursor
            - milestones: Array of milestone objects (if with_milestones=true)

        Example:
            # Get open events with nested markets
            events = await client.get_events(
                status="open",
                with_nested_markets=True
            )
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if with_nested_markets:
            params["with_nested_markets"] = "true"
        if with_milestones:
            params["with_milestones"] = "true"
        if status:
            params["status"] = status
        if series_ticker:
            params["series_ticker"] = series_ticker
        if min_close_ts:
            params["min_close_ts"] = min_close_ts

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/events",
            params=params,
            require_auth=False
        )

    async def get_multivariate_events(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        series_ticker: Optional[str] = None,
        collection_ticker: Optional[str] = None,
        with_nested_markets: bool = False
    ) -> Dict[str, Any]:
        """
        Get multivariate events (combo markets).

        Per Kalshi API: Added Nov 6, 2025. These are excluded from get_events().
        Multivariate events are dynamically created from collections.

        Args:
            limit: Number of results per page (1-200, default 100)
            cursor: Pagination cursor
            series_ticker: Filter by series ticker
            collection_ticker: Filter by collection ticker (cannot use with series_ticker)
            with_nested_markets: Include markets array within each event (default false)

        Returns:
            Dict with:
            - events: Array of multivariate event objects
            - cursor: Pagination cursor

        Example:
            # Get multivariate events for a collection
            events = await client.get_multivariate_events(
                collection_ticker="ELECTION-2024",
                with_nested_markets=True
            )
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if series_ticker:
            params["series_ticker"] = series_ticker
        if collection_ticker:
            params["collection_ticker"] = collection_ticker
        if with_nested_markets:
            params["with_nested_markets"] = "true"

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/events/multivariate",
            params=params,
            require_auth=False
        )

    async def get_event(
        self,
        event_ticker: str,
        with_nested_markets: bool = False
    ) -> Dict[str, Any]:
        """
        Get a single event by ticker.

        Per Kalshi API: Returns event details and optionally nested markets.

        Args:
            event_ticker: Event ticker
            with_nested_markets: Include markets within event object (default false)
                               If false, markets returned as separate top-level field

        Returns:
            Dict with:
            - event: Event object
            - markets: Array of market objects (if with_nested_markets=false)

        Example:
            # Get event with nested markets
            event_data = await client.get_event(
                "EVENT-TICKER",
                with_nested_markets=True
            )
        """
        params = {}
        if with_nested_markets:
            params["with_nested_markets"] = "true"

        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/events/{event_ticker}",
            params=params,
            require_auth=False
        )

    async def get_event_metadata(self, event_ticker: str) -> Dict[str, Any]:
        """
        Get metadata for an event.

        Per Kalshi API: Returns image URLs, settlement sources, and market details.

        Args:
            event_ticker: Event ticker

        Returns:
            Dict with:
            - image_url: Event image path
            - market_details: Array with market-specific metadata (image_url, color_code)
            - settlement_sources: Array of {name, url} settlement source objects
            - featured_image_url: Featured market image path
            - competition: Event competition (nullable)
            - competition_scope: Event scope based on competition (nullable)

        Example:
            metadata = await client.get_event_metadata("EVENT-TICKER")
            print(f"Image: {metadata['image_url']}")
            for source in metadata['settlement_sources']:
                print(f"Source: {source['name']} - {source['url']}")
        """
        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/events/{event_ticker}/metadata",
            require_auth=False
        )

    async def get_orderbook(self, ticker: str, depth: int = 0) -> Dict[str, Any]:
        """
        Get market orderbook.

        Per Kalshi API: Returns yes bids and no bids only (no asks).
        Binary markets use reciprocal relationship: YES BID at X = NO ASK at (100-X).

        Args:
            ticker: Market ticker
            depth: Orderbook depth (0 or negative = all levels, 1-100 = specific depth)
                  Default: 0 (all levels)

        Returns:
            Dict with orderbook containing:
            - yes: Array of [price, quantity] pairs (bids only)
            - no: Array of [price, quantity] pairs (bids only)
            - yes_dollars: Array of [price_str, quantity] with subpenny precision
            - no_dollars: Array of [price_str, quantity] with subpenny precision

        Example:
            # Get full orderbook
            book = await client.get_orderbook("MARKET-TICKER")

            # Get top 10 levels
            book = await client.get_orderbook("MARKET-TICKER", depth=10)
        """
        params = {"depth": depth}
        return await self._make_authenticated_request(
            "GET", f"/trade-api/v2/markets/{ticker}/orderbook", params=params, require_auth=False
        )
    
    async def get_market_history(
        self,
        ticker: str,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get market price history.
        
        Args:
            ticker: Market ticker
            start_ts: Start timestamp
            end_ts: End timestamp
            limit: Number of records to return
        
        Returns:
            Price history data
        """
        params = {"limit": limit}
        if start_ts:
            params["start_ts"] = start_ts
        if end_ts:
            params["end_ts"] = end_ts
        
        return await self._make_authenticated_request(
            "GET", f"/trade-api/v2/markets/{ticker}/history", params=params, require_auth=False
        )

    async def get_market_candlesticks(
        self,
        series_ticker: str,
        ticker: str,
        start_ts: int,
        end_ts: int,
        period_interval: int
    ) -> Dict[str, Any]:
        """
        Get candlestick data for a specific market.

        Per Kalshi API: Returns OHLC data for yes_bid, yes_ask, and price.

        Args:
            series_ticker: Series containing the market
            ticker: Market ticker
            start_ts: Start timestamp (Unix seconds)
            end_ts: End timestamp (Unix seconds)
            period_interval: Candlestick period in minutes (1, 60, or 1440)

        Returns:
            Dict with:
            - ticker: Market ticker
            - candlesticks: Array of candlestick objects with:
                - end_period_ts: Period end timestamp
                - yes_bid: {open, low, high, close} in cents and dollars
                - yes_ask: {open, low, high, close} in cents and dollars
                - price: {open, low, high, close, mean, previous, min, max}
                - volume: Trading volume
                - open_interest: Open interest

        Example:
            # Get hourly candlesticks for last 24h
            import time
            end = int(time.time())
            start = end - 86400
            candles = await client.get_market_candlesticks(
                series_ticker="SERIES",
                ticker="MARKET-TICKER",
                start_ts=start,
                end_ts=end,
                period_interval=60  # 1 hour
            )
        """
        params = {
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": period_interval
        }

        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/series/{series_ticker}/markets/{ticker}/candlesticks",
            params=params,
            require_auth=False
        )

    async def get_batch_market_candlesticks(
        self,
        market_tickers: List[str],
        start_ts: int,
        end_ts: int,
        period_interval: int,
        include_latest_before_start: bool = False
    ) -> Dict[str, Any]:
        """
        Get candlestick data for multiple markets in a single request.

        Per Kalshi API: Max 100 tickers per request, returns up to 10,000 total candlesticks.

        Args:
            market_tickers: List of market tickers (max 100)
            start_ts: Start timestamp (Unix seconds)
            end_ts: End timestamp (Unix seconds)
            period_interval: Candlestick period in minutes (>= 1)
            include_latest_before_start: Prepend synthetic candlestick from before start_ts
                                        (default false)

        Returns:
            Dict with:
            - markets: Array of {market_ticker, candlesticks} objects

        Example:
            # Get daily candlesticks for multiple markets
            candles = await client.get_batch_market_candlesticks(
                market_tickers=["MARKET-1", "MARKET-2", "MARKET-3"],
                start_ts=start,
                end_ts=end,
                period_interval=1440  # 1 day
            )
        """
        if len(market_tickers) > 100:
            raise ValueError("Maximum 100 market tickers allowed")

        params = {
            "market_tickers": ",".join(market_tickers),
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": period_interval
        }
        if include_latest_before_start:
            params["include_latest_before_start"] = "true"

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/markets/candlesticks",
            params=params,
            require_auth=False
        )

    async def get_event_candlesticks(
        self,
        series_ticker: str,
        event_ticker: str,
        start_ts: int,
        end_ts: int,
        period_interval: int
    ) -> Dict[str, Any]:
        """
        Get aggregated candlestick data across all markets in an event.

        Per Kalshi API: Returns candlesticks for each market in the event.

        Args:
            series_ticker: Series containing the event
            event_ticker: Event ticker
            start_ts: Start timestamp (Unix seconds)
            end_ts: End timestamp (Unix seconds)
            period_interval: Period in minutes (1, 60, or 1440)

        Returns:
            Dict with:
            - market_tickers: Array of market tickers in the event
            - market_candlesticks: Array of candlestick arrays (one per market)
            - adjusted_end_ts: Adjusted end timestamp if results exceed limit

        Example:
            candles = await client.get_event_candlesticks(
                series_ticker="PRES",
                event_ticker="EVENT-TICKER",
                start_ts=start,
                end_ts=end,
                period_interval=60
            )
        """
        params = {
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": period_interval
        }

        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/series/{series_ticker}/events/{event_ticker}/candlesticks",
            params=params,
            require_auth=False
        )

    async def get_trades(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        ticker: Optional[str] = None,
        min_ts: Optional[int] = None,
        max_ts: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get all trades across all markets with filtering.

        Per Kalshi API: Returns completed transactions between users.

        Args:
            limit: Number of results per page (1-1000, default 100)
            cursor: Pagination cursor
            ticker: Filter by market ticker
            min_ts: Filter trades after this Unix timestamp
            max_ts: Filter trades before this Unix timestamp

        Returns:
            Dict with:
            - trades: Array of trade objects with:
                - trade_id: Unique trade identifier
                - ticker: Market ticker
                - price, count: Trade price and quantity
                - yes_price, no_price: Prices in cents
                - yes_price_dollars, no_price_dollars: Prices in dollars
                - taker_side: Which side was taker (yes/no)
                - created_time: Trade timestamp
            - cursor: Pagination cursor

        Example:
            # Get recent trades for a market
            trades = await client.get_trades(
                ticker="MARKET-TICKER",
                limit=50
            )
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if ticker:
            params["ticker"] = ticker
        if min_ts:
            params["min_ts"] = min_ts
        if max_ts:
            params["max_ts"] = max_ts

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/markets/trades",
            params=params,
            require_auth=False
        )

    async def get_event_forecast_percentile_history(
        self,
        series_ticker: str,
        event_ticker: str,
        percentiles: List[int],
        start_ts: int,
        end_ts: int,
        period_interval: int
    ) -> Dict[str, Any]:
        """
        Get historical forecast data at specific percentiles for an event.

        Per Kalshi API: Returns raw and formatted forecast numbers over time.

        Args:
            series_ticker: Series containing the event
            event_ticker: Event ticker
            percentiles: Array of percentile values (0-10000, max 10 values)
            start_ts: Start timestamp (Unix seconds)
            end_ts: End timestamp (Unix seconds)
            period_interval: Period in minutes (0=5-second intervals, 1, 60, or 1440)

        Returns:
            Dict with:
            - forecast_history: Array of forecast data points with:
                - event_ticker: Event ticker
                - end_period_ts: Period end timestamp
                - period_interval: Period interval in minutes
                - percentile_points: Array of {percentile, raw_numerical_forecast,
                                             numerical_forecast, formatted_forecast}

        Example:
            # Get median (50th percentile) forecast history
            forecasts = await client.get_event_forecast_percentile_history(
                series_ticker="PRES",
                event_ticker="EVENT-TICKER",
                percentiles=[5000],  # 50th percentile
                start_ts=start,
                end_ts=end,
                period_interval=60
            )
        """
        if len(percentiles) > 10:
            raise ValueError("Maximum 10 percentile values allowed")
        for p in percentiles:
            if not 0 <= p <= 10000:
                raise ValueError(f"Percentile {p} out of range (0-10000)")

        params = {
            "percentiles": ",".join(str(p) for p in percentiles),
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": period_interval
        }

        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/series/{series_ticker}/events/{event_ticker}/forecast_percentile_history",
            params=params,
            require_auth=True
        )

    async def get_live_data(
        self,
        data_type: str,
        milestone_id: str
    ) -> Dict[str, Any]:
        """
        Get live data for a specific milestone.

        Per Kalshi API: Returns real-time data for milestones.

        Args:
            data_type: Type of live data
            milestone_id: Milestone ID

        Returns:
            Dict with:
            - live_data: Object containing:
                - type: Data type
                - details: Type-specific details
                - milestone_id: Milestone ID

        Example:
            live_data = await client.get_live_data(
                data_type="election",
                milestone_id="milestone-123"
            )
        """
        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/live_data/{data_type}/milestone/{milestone_id}",
            require_auth=False
        )

    async def get_multiple_live_data(
        self,
        milestone_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Get live data for multiple milestones.

        Per Kalshi API: Batch endpoint for retrieving multiple live data objects.

        Args:
            milestone_ids: Array of milestone IDs (max 100)

        Returns:
            Dict with:
            - live_datas: Array of live data objects

        Example:
            live_data = await client.get_multiple_live_data(
                milestone_ids=["milestone-1", "milestone-2", "milestone-3"]
            )
        """
        if len(milestone_ids) > 100:
            raise ValueError("Maximum 100 milestone IDs allowed")

        params = {
            "milestone_ids": milestone_ids
        }

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/live_data/batch",
            params=params,
            require_auth=False
        )

    async def place_order(
        self,
        ticker: str,
        client_order_id: str,
        side: str,
        action: str,
        count: int,
        type_: str = "market",
        yes_price: Optional[int] = None,
        no_price: Optional[int] = None,
        expiration_ts: Optional[int] = None,
        order_group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place a trading order.

        Args:
            ticker: Market ticker
            client_order_id: Unique client order ID (CRITICAL for deduplication -
                           per Kalshi Quick Start: prevents accidental double orders
                           on network issues. Use UUID4 for uniqueness)
            side: "yes" or "no"
            action: "buy" or "sell"
            count: Number of contracts
            type_: Order type ("market" or "limit")
            yes_price: Yes price in cents (1-99, per Kalshi Quick Start)
            no_price: No price in cents (1-99, per Kalshi Quick Start)
            expiration_ts: Order expiration timestamp
            order_group_id: Optional order group ID for risk management
                          (see create_order_group for details)

        Returns:
            Order response (HTTP 201 on success per Kalshi Quick Start)

        Example:
            # Create order with order group for risk management
            group = await client.create_order_group(contracts_limit=100)
            order = await client.place_order(
                ticker="MARKET-TICKER",
                client_order_id=str(uuid.uuid4()),
                side="yes",
                action="buy",
                count=10,
                type_="limit",
                yes_price=55,
                order_group_id=group['order_group_id']
            )
        """
        order_data = {
            "ticker": ticker,
            "client_order_id": client_order_id,
            "side": side,
            "action": action,
            "count": count,
            "type": type_
        }

        if yes_price is not None:
            order_data["yes_price"] = yes_price
        if no_price is not None:
            order_data["no_price"] = no_price
        if expiration_ts:
            order_data["expiration_ts"] = expiration_ts
        if order_group_id:
            order_data["order_group_id"] = order_group_id
        
        # --- Sanitize + enforce Kalshi API requirements ---
        # 1. Validate and convert count to integer
        try:
            count_int = int(order_data["count"])
        except Exception:
            raise ValueError(f"Invalid count for order: {order_data['count']}")
        if count_int < 1:
            raise ValueError(f"Order count must be >= 1 (got {count_int})")
        order_data["count"] = count_int

        order_type = order_data["type"]
        side_l = order_data["side"].lower()
        action_l = order_data["action"].lower()

        # 2. Validate side and action values
        if side_l not in ["yes", "no"]:
            raise ValueError(f"Invalid side: {side_l}. Must be 'yes' or 'no'")
        if action_l not in ["buy", "sell"]:
            raise ValueError(f"Invalid action: {action_l}. Must be 'buy' or 'sell'")
        if order_type not in ["market", "limit"]:
            raise ValueError(f"Invalid order type: {order_type}. Must be 'market' or 'limit'")

        # Ensure side and action are lowercase for Kalshi API
        order_data["side"] = side_l
        order_data["action"] = action_l

        # 3. Validate prices if provided (must be 1-99 cents)
        def validate_price(price: int, price_name: str) -> int:
            if not isinstance(price, int):
                raise ValueError(f"{price_name} must be an integer (cents)")
            if price < 1 or price > 99:
                raise ValueError(f"{price_name} must be between 1-99 cents (got {price})")
            return price

        if "yes_price" in order_data and order_data["yes_price"] is not None:
            order_data["yes_price"] = validate_price(order_data["yes_price"], "yes_price")
        if "no_price" in order_data and order_data["no_price"] is not None:
            order_data["no_price"] = validate_price(order_data["no_price"], "no_price")

        # 4. Handle LIMIT orders
        if order_type == "limit":
            if side_l == "yes" and "yes_price" not in order_data:
                raise ValueError("Limit YES orders require yes_price")
            if side_l == "no" and "no_price" not in order_data:
                raise ValueError("Limit NO orders require no_price")

        # 5. Handle MARKET orders (both BUY and SELL!)
        if order_type == "market":
            if action_l == "buy":
                # For market BUY orders, set the side-specific price to max (99¢)
                if side_l == "yes" and "yes_price" not in order_data:
                    order_data["yes_price"] = 99  # Max willing to pay for YES
                elif side_l == "no" and "no_price" not in order_data:
                    order_data["no_price"] = 99  # Max willing to pay for NO

                # Set buy_max_cost for additional safety
                if "buy_max_cost" not in order_data:
                    order_data["buy_max_cost"] = count_int * 99

            elif action_l == "sell":
                # ⚠️ CRITICAL FIX: Market SELL orders also need prices!
                # For market SELL orders, set the side-specific price to min (1¢) to sell fast
                if side_l == "yes" and "yes_price" not in order_data:
                    order_data["yes_price"] = 1  # Min willing to accept for YES
                elif side_l == "no" and "no_price" not in order_data:
                    order_data["no_price"] = 1  # Min willing to accept for NO

        # 🔧 CRITICAL FIX: ALL orders require time_in_force (official Kalshi API requires full string)
        if "time_in_force" not in order_data:
            order_data["time_in_force"] = "good_till_canceled"  # Official Kalshi API value

        # DEBUG: Log the exact order data being sent
        self.logger.info(f"📤 Sending order to Kalshi API: {order_data}")

        return await self._make_authenticated_request(
            "POST", "/trade-api/v2/portfolio/orders", json_data=order_data
        )
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        return await self._make_authenticated_request(
            "DELETE", f"/trade-api/v2/portfolio/orders/{order_id}"
        )
    
    async def get_trades(
        self,
        ticker: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get trade history.
        
        Args:
            ticker: Filter by ticker
            limit: Maximum number of trades to return
            cursor: Pagination cursor
        
        Returns:
            Trades data
        """
        params = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if cursor:
            params["cursor"] = cursor
        
        return await self._make_authenticated_request(
            "GET", "/trade-api/v2/portfolio/trades", params=params
        )
    
    async def place_smart_limit_order(
        self,
        ticker: str,
        client_order_id: str,
        side: str,
        action: str,
        count: int,
        target_price: Optional[float] = None,
        max_slippage_pct: float = 0.02
    ) -> Dict[str, Any]:
        """
        Place a smart limit order with optimal pricing.

        Automatically calculates limit price based on current market price
        with configurable slippage tolerance for better fills.

        Args:
            ticker: Market ticker
            client_order_id: Unique order ID
            side: "yes" or "no"
            action: "buy" or "sell"
            count: Number of contracts
            target_price: Target price in dollars (0.01-0.99), if None uses current market
            max_slippage_pct: Maximum slippage tolerance (default 2%)

        Returns:
            Order response

        Benefits:
            - Better fills (save 1-3 cents per contract)
            - Reduce slippage costs
            - Capture spread when market making
        """
        try:
            # Get current market price if no target provided
            if target_price is None:
                market_info = await self.get_market(ticker)
                if side.lower() == "yes":
                    current_price = market_info.get('yes_price', 50) / 100
                else:
                    current_price = market_info.get('no_price', 50) / 100
                target_price = current_price

            # Calculate limit price with slippage tolerance
            if action.lower() == "buy":
                # For buying: willing to pay slightly more to ensure fill
                limit_price = target_price * (1 + max_slippage_pct)
            else:
                # For selling: willing to accept slightly less
                limit_price = target_price * (1 - max_slippage_pct)

            # Clamp to valid range
            limit_price = max(0.01, min(0.99, limit_price))
            limit_price_cents = int(limit_price * 100)

            # Place limit order
            order_data = {
                "ticker": ticker,
                "client_order_id": client_order_id,
                "side": side,
                "action": action,
                "count": count,
                "type": "limit"
            }

            if side.lower() == "yes":
                order_data["yes_price"] = limit_price_cents
            else:
                order_data["no_price"] = limit_price_cents

            # Add time_in_force
            order_data["time_in_force"] = "good_till_canceled"

            self.logger.info(
                f"📊 Smart limit order: {action.upper()} {count} {side.upper()} "
                f"at {limit_price_cents}¢ (target: {int(target_price*100)}¢, "
                f"slippage: {max_slippage_pct:.1%})"
            )

            return await self._make_authenticated_request(
                "POST", "/trade-api/v2/portfolio/orders", json_data=order_data
            )

        except Exception as e:
            self.logger.error(f"Smart limit order failed, falling back to market order: {e}")
            # Fallback to market order if limit order fails
            return await self.place_order(
                ticker=ticker,
                client_order_id=client_order_id,
                side=side,
                action=action,
                count=count,
                type_="market"
            )

    async def place_iceberg_order(
        self,
        ticker: str,
        side: str,
        action: str,
        total_count: int,
        chunk_size: int = 5,
        delay_seconds: float = 2.0
    ) -> list:
        """
        Place large order in smaller chunks to reduce market impact.

        Useful for large positions to avoid moving the market against you.

        Args:
            ticker: Market ticker
            side: "yes" or "no"
            action: "buy" or "sell"
            total_count: Total contracts to trade
            chunk_size: Contracts per chunk (default 5)
            delay_seconds: Delay between chunks (default 2s)

        Returns:
            List of order responses

        Benefits:
            - Reduce market impact on large orders
            - Better average fill price
            - Avoid alerting other traders to large position
        """
        import uuid

        orders = []
        remaining = total_count

        self.logger.info(
            f"🔪 Iceberg order: {total_count} contracts in chunks of {chunk_size}"
        )

        while remaining > 0:
            chunk = min(chunk_size, remaining)

            try:
                order_id = str(uuid.uuid4())
                response = await self.place_smart_limit_order(
                    ticker=ticker,
                    client_order_id=order_id,
                    side=side,
                    action=action,
                    count=chunk
                )

                orders.append(response)
                remaining -= chunk

                self.logger.info(
                    f"✅ Iceberg chunk placed: {chunk} contracts "
                    f"({total_count - remaining}/{total_count} complete)"
                )

                if remaining > 0:
                    await asyncio.sleep(delay_seconds)

            except Exception as e:
                self.logger.error(f"Iceberg chunk failed: {e}")
                # Continue with remaining chunks even if one fails
                break

        return orders

    # ============================================================================
    # BATCH OPERATIONS (Added per Kalshi API docs - Nov 14, 2025)
    # ============================================================================

    async def batch_create_orders(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple orders in a single request.

        Per Kalshi API: Available to all users as of Nov 14, 2025.
        Rate limit friendly - counts as single request.

        Args:
            orders: List of order dictionaries, each with:
                - ticker: str
                - client_order_id: str
                - side: "yes" or "no"
                - action: "buy" or "sell"
                - count: int
                - type: "market" or "limit"
                - yes_price/no_price: Optional[int]
                - expiration_ts: Optional[int]

        Returns:
            Response with created orders and any errors

        Example:
            orders = [
                {"ticker": "MARKET1", "client_order_id": "id1", "side": "yes",
                 "action": "buy", "count": 10, "type": "market"},
                {"ticker": "MARKET2", "client_order_id": "id2", "side": "no",
                 "action": "buy", "count": 5, "type": "market"}
            ]
            result = await client.batch_create_orders(orders)
        """
        return await self._make_authenticated_request(
            "POST",
            "/trade-api/v2/portfolio/orders/batched",
            json_data={"orders": orders}
        )

    async def batch_cancel_orders(self, order_ids: List[str]) -> Dict[str, Any]:
        """
        Cancel multiple orders in a single request.

        Per Kalshi API: Available to all users as of Dec 1, 2025.
        Much more efficient than canceling one by one.

        Args:
            order_ids: List of order IDs to cancel

        Returns:
            Response with cancellation results

        Example:
            result = await client.batch_cancel_orders([
                "order-id-1",
                "order-id-2",
                "order-id-3"
            ])
        """
        return await self._make_authenticated_request(
            "DELETE",
            "/trade-api/v2/portfolio/orders/batched",
            json_data={"ids": order_ids}
        )

    # ============================================================================
    # ORDER AMENDMENTS (Added per Kalshi API docs)
    # ============================================================================

    async def amend_order(
        self,
        order_id: str,
        ticker: str,
        side: str,
        action: str,
        client_order_id: str,
        updated_client_order_id: str,
        yes_price: Optional[int] = None,
        no_price: Optional[int] = None,
        yes_price_dollars: Optional[str] = None,
        no_price_dollars: Optional[str] = None,
        count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Amend an existing order's price and/or quantity.

        Per Kalshi API: Endpoint for amending the max number of fillable contracts
        and/or price in an existing order. Max fillable contracts is
        remaining_count + fill_count.

        More efficient than cancel+replace, maintains better queue position priority.

        Args:
            order_id: Order ID to amend
            ticker: Market ticker (required)
            side: "yes" or "no" (required)
            action: "buy" or "sell" (required)
            client_order_id: Original client-specified order ID (required)
            updated_client_order_id: New client-specified order ID (required)
            yes_price: Updated yes price in cents (1-99)
            no_price: Updated no price in cents (1-99)
            yes_price_dollars: Updated yes price in fixed-point dollars
            no_price_dollars: Updated no price in fixed-point dollars
            count: Updated quantity (max fillable contracts)

        Returns:
            Dict with:
            - old_order: The order before amendment
            - order: The order after amendment

        Note:
            - Exactly one of yes_price, no_price, yes_price_dollars, no_price_dollars
              must be provided
            - Can only amend resting limit orders

        Example:
            result = await client.amend_order(
                order_id="order-123",
                ticker="MARKET-TICKER",
                side="yes",
                action="buy",
                client_order_id="original-id",
                updated_client_order_id="new-id",
                yes_price=55,
                count=15
            )
            print(f"Old price: {result['old_order']['yes_price']}")
            print(f"New price: {result['order']['yes_price']}")
        """
        amend_data = {
            "ticker": ticker,
            "side": side,
            "action": action,
            "client_order_id": client_order_id,
            "updated_client_order_id": updated_client_order_id
        }

        # Exactly one price field must be provided (per API docs)
        price_fields = [yes_price, no_price, yes_price_dollars, no_price_dollars]
        if sum(x is not None for x in price_fields) != 1:
            raise ValueError(
                "Exactly one of yes_price, no_price, yes_price_dollars, "
                "or no_price_dollars must be provided"
            )

        if yes_price is not None:
            amend_data["yes_price"] = yes_price
        if no_price is not None:
            amend_data["no_price"] = no_price
        if yes_price_dollars is not None:
            amend_data["yes_price_dollars"] = yes_price_dollars
        if no_price_dollars is not None:
            amend_data["no_price_dollars"] = no_price_dollars

        if count is not None:
            amend_data["count"] = count

        return await self._make_authenticated_request(
            "POST",
            f"/trade-api/v2/portfolio/orders/{order_id}/amend",
            json_data=amend_data
        )

    async def decrease_order(
        self,
        order_id: str,
        reduce_by: Optional[int] = None,
        reduce_to: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Decrease the number of contracts in an existing order.

        Per Kalshi API: This is the only kind of edit available on order quantity.
        Cancelling an order is equivalent to decreasing an order amount to zero.

        Maintains better queue position than cancel+replace with lower quantity.

        Args:
            order_id: Order ID to decrease
            reduce_by: Amount to reduce quantity by (must be >= 1)
            reduce_to: Target quantity to reduce to (must be >= 0)

        Returns:
            Dict with updated order object

        Note:
            Exactly one of reduce_by or reduce_to must be provided.

        Examples:
            # Reduce by 3 contracts (if currently 10 → becomes 7)
            await client.decrease_order("order-123", reduce_by=3)

            # Reduce to exactly 5 contracts
            await client.decrease_order("order-123", reduce_to=5)

            # Cancel order completely (reduce to 0)
            await client.decrease_order("order-123", reduce_to=0)
        """
        if (reduce_by is None and reduce_to is None) or \
           (reduce_by is not None and reduce_to is not None):
            raise ValueError("Exactly one of reduce_by or reduce_to must be provided")

        decrease_data = {}
        if reduce_by is not None:
            if reduce_by < 1:
                raise ValueError("reduce_by must be >= 1")
            decrease_data["reduce_by"] = reduce_by
        if reduce_to is not None:
            if reduce_to < 0:
                raise ValueError("reduce_to must be >= 0")
            decrease_data["reduce_to"] = reduce_to

        return await self._make_authenticated_request(
            "POST",
            f"/trade-api/v2/portfolio/orders/{order_id}/decrease",
            json_data=decrease_data
        )

    # ============================================================================
    # ORDER GROUPS (Risk Management - API Part 3)
    # ============================================================================

    async def get_order_groups(self) -> Dict[str, Any]:
        """
        Get all order groups for the authenticated user.

        Per Kalshi API: Order groups allow setting a contracts_limit. When the
        limit is hit, all orders in the group are auto-canceled and no new orders
        can be placed until reset.

        Returns:
            Dict with order_groups array containing:
            - id: Order group ID
            - is_auto_cancel_enabled: Whether auto-cancel is active

        Example:
            groups = await client.get_order_groups()
            for group in groups['order_groups']:
                print(f"Group {group['id']}: auto-cancel={group['is_auto_cancel_enabled']}")
        """
        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/portfolio/order_groups"
        )

    async def create_order_group(self, contracts_limit: int) -> Dict[str, Any]:
        """
        Create a new order group with a contracts limit.

        Per Kalshi API: When the limit is hit, all orders in the group are
        cancelled and no new orders can be placed until reset.

        Useful for risk management - limit total position exposure across
        multiple markets.

        Args:
            contracts_limit: Maximum contracts that can be matched (>= 1)

        Returns:
            Dict with order_group_id

        Example:
            # Create group with max 100 contracts
            result = await client.create_order_group(contracts_limit=100)
            group_id = result['order_group_id']

            # Use in orders
            await client.place_order(
                ...,
                order_group_id=group_id
            )
        """
        if contracts_limit < 1:
            raise ValueError("contracts_limit must be >= 1")

        return await self._make_authenticated_request(
            "POST",
            "/trade-api/v2/portfolio/order_groups/create",
            json_data={"contracts_limit": contracts_limit}
        )

    async def get_order_group(self, order_group_id: str) -> Dict[str, Any]:
        """
        Get details for a single order group.

        Per Kalshi API: Retrieves all order IDs and auto-cancel status.

        Args:
            order_group_id: Order group ID

        Returns:
            Dict with:
            - is_auto_cancel_enabled: Whether auto-cancel is active
            - orders: List of order IDs in this group

        Example:
            group = await client.get_order_group("group-123")
            print(f"Auto-cancel: {group['is_auto_cancel_enabled']}")
            print(f"Orders: {group['orders']}")
        """
        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/portfolio/order_groups/{order_group_id}"
        )

    async def delete_order_group(self, order_group_id: str) -> Dict[str, Any]:
        """
        Delete an order group and cancel all orders within it.

        Per Kalshi API: This permanently removes the group.

        Args:
            order_group_id: Order group ID to delete

        Returns:
            Empty dict on success

        Example:
            await client.delete_order_group("group-123")
        """
        return await self._make_authenticated_request(
            "DELETE",
            f"/trade-api/v2/portfolio/order_groups/{order_group_id}"
        )

    async def reset_order_group(self, order_group_id: str) -> Dict[str, Any]:
        """
        Reset the order group's matched contracts counter to zero.

        Per Kalshi API: Allows new orders to be placed again after the limit
        was hit.

        Useful for daily/periodic risk limit resets.

        Args:
            order_group_id: Order group ID to reset

        Returns:
            Empty dict on success

        Example:
            # Reset daily at market open
            await client.reset_order_group("group-123")
            # Can now place new orders up to contracts_limit again
        """
        return await self._make_authenticated_request(
            "PUT",
            f"/trade-api/v2/portfolio/order_groups/{order_group_id}/reset",
            json_data={}
        )

    # ============================================================================
    # API KEYS MANAGEMENT (API Part 4)
    # ============================================================================

    async def get_api_keys(self) -> Dict[str, Any]:
        """
        Get all API keys for the authenticated user.

        Per Kalshi API: Returns list of API keys with their IDs, names, scopes,
        and creation timestamps. Does NOT return the private keys (security).

        Returns:
            Dict with api_keys array containing:
            - api_key_id: Unique key identifier
            - name: User-provided key name
            - scopes: List of permission scopes
            - created_at: Creation timestamp

        Example:
            result = await client.get_api_keys()
            for key in result['api_keys']:
                print(f"Key: {key['name']} (ID: {key['api_key_id']})")
                print(f"  Scopes: {', '.join(key['scopes'])}")
        """
        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/api_keys"
        )

    async def create_api_key(
        self,
        name: str,
        public_key: str,
        scopes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key using your own RSA public key.

        Per Kalshi API: You provide your own RSA public key pair. Kalshi stores
        the public key and you keep the private key secure for signing requests.

        Args:
            name: Descriptive name for the key (e.g., "Trading Bot Production")
            public_key: Your RSA public key in PEM format
            scopes: List of permission scopes (e.g., ["read", "write"]).
                   If 'write' is included, 'read' must also be included.
                   Defaults to full access (['read', 'write']) if not provided.

        Returns:
            Dict with:
            - api_key_id: The created key's ID (use in KALSHI-ACCESS-KEY header)

        Example:
            # Generate RSA key pair first
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization

            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            public_key_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()

            # Create API key (defaults to full access)
            result = await client.create_api_key(
                name="My Trading Bot",
                public_key=public_key_pem
            )
            print(f"API Key ID: {result['api_key_id']}")
        """
        if not name:
            raise ValueError("name cannot be empty")
        if not public_key:
            raise ValueError("public_key cannot be empty")

        json_data = {
            "name": name,
            "public_key": public_key
        }

        # Only include scopes if provided (API defaults to ['read', 'write'])
        if scopes is not None:
            json_data["scopes"] = scopes

        return await self._make_authenticated_request(
            "POST",
            "/trade-api/v2/api_keys",
            json_data=json_data
        )

    async def generate_api_key(
        self,
        name: str,
        scopes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a new API key with Kalshi creating the key pair.

        Per Kalshi API: Kalshi generates both public and private keys. The private
        key is returned ONCE and never stored. Save it immediately.

        WARNING: The private_key is returned only once. Store it securely!

        Args:
            name: Descriptive name for the key
            scopes: List of permission scopes (e.g., ["read", "write"]).
                   If 'write' is included, 'read' must also be included.
                   Defaults to full access (['read', 'write']) if not provided.

        Returns:
            Dict with:
            - api_key_id: The key ID (use in KALSHI-ACCESS-KEY header)
            - private_key: RSA private key in PEM format (SAVE THIS!)

        Example:
            # Generate key with default full access
            result = await client.generate_api_key(
                name="Auto-Generated Bot Key"
            )

            # CRITICAL: Save private key immediately!
            with open("private_key.pem", "w") as f:
                f.write(result['private_key'])

            print(f"API Key ID: {result['api_key_id']}")
            print("⚠️  Private key saved to private_key.pem - keep secure!")
        """
        if not name:
            raise ValueError("name cannot be empty")

        json_data = {"name": name}

        # Only include scopes if provided (API defaults to ['read', 'write'])
        if scopes is not None:
            json_data["scopes"] = scopes

        return await self._make_authenticated_request(
            "POST",
            "/trade-api/v2/api_keys/generate",
            json_data=json_data
        )

    async def delete_api_key(self, api_key_id: str) -> Dict[str, Any]:
        """
        Delete an API key, immediately revoking access.

        Per Kalshi API: Permanently removes the key. Any requests using this
        key will fail with 401 Unauthorized.

        Args:
            api_key_id: The API key ID to delete

        Returns:
            Empty dict on success

        Example:
            await client.delete_api_key("your-api-key-id")
            print("API key revoked successfully")
        """
        if not api_key_id:
            raise ValueError("api_key_id cannot be empty")

        return await self._make_authenticated_request(
            "DELETE",
            f"/trade-api/v2/api_keys/{api_key_id}"
        )

    # ============================================================================
    # SEARCH & DISCOVERY (API Part 4)
    # ============================================================================

    async def get_tags_by_categories(self) -> Dict[str, Any]:
        """
        Get all tags grouped by series categories.

        Per Kalshi API: Returns hierarchical tag structure for filtering markets
        by topic categories (e.g., Politics, Economics, Sports).

        Returns:
            Dict with:
            - tags_by_categories: Mapping of series categories to their associated tags

        Example:
            result = await client.get_tags_by_categories()
            for category, tags in result['tags_by_categories'].items():
                print(f"{category}: {', '.join(tags)}")
        """
        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/search/tags_by_categories",
            require_auth=False
        )

    async def get_filters_by_sport(self) -> Dict[str, Any]:
        """
        Get sport-specific filter options.

        Per Kalshi API: Returns available filters organized by sport, including
        scopes and competitions, plus ordered list of sports for display.

        Returns:
            Dict with:
            - filters_by_sports: Mapping of sports to their filter details
            - sport_ordering: Ordered list of sports for display

        Example:
            result = await client.get_filters_by_sport()
            for sport in result['sport_ordering']:
                filters = result['filters_by_sports'].get(sport, {})
                print(f"{sport}: {filters}")
        """
        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/search/filters_by_sport",
            require_auth=False
        )

    # ============================================================================
    # SERIES OPERATIONS (Added per Kalshi API docs)
    # ============================================================================

    async def get_series(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_product_metadata: bool = False,
        include_volume: bool = False,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all series (market categories/templates).

        Per Kalshi API: Series represent templates for recurring events
        (e.g., "Monthly Jobs Report", "Weekly Initial Jobless Claims").

        Args:
            category: Filter by category
            tags: Filter by tags (e.g., ["Politics", "Sports"])
            include_product_metadata: Include product metadata (default false)
            include_volume: Include total volume traded (default false)
            limit: Maximum number of series to return (default 100)
            cursor: Pagination cursor

        Returns:
            Dict with:
            - series: Array of series objects

        Example:
            # Get politics series with volume data
            series = await client.get_series(
                category="Politics",
                include_volume=True
            )
        """
        params = {}
        if category:
            params["category"] = category
        if tags:
            # Per Oct 13, 2025 fix: tags are comma-separated
            params["tags"] = ",".join(tags)
        if include_product_metadata:
            params["include_product_metadata"] = "true"
        if include_volume:
            params["include_volume"] = "true"
        if limit:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/series",
            params=params,
            require_auth=False
        )

    async def get_series_info(
        self,
        series_ticker: str,
        include_volume: bool = False
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific series.

        Args:
            series_ticker: Series ticker (e.g., "PRES")
            include_volume: Include total volume across all events (Jan 6, 2026+)

        Returns:
            Series details including markets
        """
        params = {}
        if include_volume:
            params["include_volume"] = "true"

        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/series/{series_ticker}",
            params=params,
            require_auth=False
        )

    async def get_series_fee_changes(
        self,
        series_ticker: Optional[str] = None,
        show_historical: bool = False
    ) -> Dict[str, Any]:
        """
        Get scheduled fee changes for series.

        Per Kalshi API: Added Sept 21, 2025.
        Useful for anticipating fee structure changes.

        Args:
            series_ticker: Filter to specific series
            show_historical: Include past fee changes (default: only future)

        Returns:
            Fee change schedule

        Example:
            # Get upcoming fee changes for all series
            changes = await client.get_series_fee_changes()

            # Get all fee changes (past and future) for PRES series
            pres_changes = await client.get_series_fee_changes(
                series_ticker="PRES",
                show_historical=True
            )
        """
        params = {}
        if series_ticker:
            params["series_ticker"] = series_ticker
        if show_historical:
            params["show_historical"] = "true"

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/series/fee_changes",
            params=params,
            require_auth=False
        )

    # ============================================================================
    # ORDER QUEUE POSITIONS (Added per Kalshi API docs - Aug 1, 2025)
    # ============================================================================

    async def get_queue_positions(
        self,
        market_tickers: Optional[List[str]] = None,
        event_ticker: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get queue positions for multiple resting limit orders.

        Shows where your orders are in the queue (important for fill priority).

        Args:
            market_tickers: Filter by market tickers
            event_ticker: Filter by event

        Returns:
            Queue positions for your orders

        Note: Must specify either market_tickers OR event_ticker.
        """
        params = {}
        if market_tickers:
            params["market_tickers"] = ",".join(market_tickers)
        if event_ticker:
            params["event_ticker"] = event_ticker

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/portfolio/orders/queue_positions",
            params=params
        )

    async def get_order_queue_position(self, order_id: str) -> Dict[str, Any]:
        """
        Get queue position for a specific resting order.

        Args:
            order_id: Order ID to check

        Returns:
            Queue position and details
        """
        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/portfolio/orders/{order_id}/queue_position"
        )

    # ============================================================================
    # EXCHANGE STATUS (Added per Kalshi API docs)
    # ============================================================================

    async def get_exchange_status(self) -> Dict[str, Any]:
        """
        Get current exchange operational status.

        Per Kalshi API docs: Check if exchange and trading are active.

        Returns:
            Dict with:
            - exchange_active (bool): False during maintenance
            - trading_active (bool): True during trading hours
            - exchange_estimated_resume_time (str|None): Estimated downtime end

        Example:
            status = await client.get_exchange_status()
            if status['trading_active']:
                print("Trading is open!")
        """
        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/exchange/status",
            require_auth=False
        )

    async def get_exchange_announcements(self) -> Dict[str, Any]:
        """
        Get all exchange-wide announcements.

        Per Kalshi API docs: Returns announcements array with type, message,
        delivery_time, and status fields.

        Returns:
            Dict with announcements array

        Example:
            result = await client.get_exchange_announcements()
            for announcement in result['announcements']:
                print(f"{announcement['type']}: {announcement['message']}")
        """
        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/exchange/announcements",
            require_auth=False
        )

    async def get_exchange_schedule(self) -> Dict[str, Any]:
        """
        Get exchange trading schedule.

        Per Kalshi API docs: Returns standard_hours (daily schedule) and
        maintenance_windows (planned downtime).

        Returns:
            Dict with schedule object containing:
            - standard_hours: Daily trading hours by weekday
            - maintenance_windows: Scheduled maintenance periods

        Example:
            schedule = await client.get_exchange_schedule()
            print(f"Maintenance windows: {schedule['schedule']['maintenance_windows']}")
        """
        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/exchange/schedule",
            require_auth=False
        )

    async def get_user_data_timestamp(self) -> Dict[str, Any]:
        """
        Get timestamp when user data was last validated.

        Per Kalshi API docs: "There is typically a short delay before exchange
        events are reflected in the API endpoints. Whenever possible, combine API
        responses to PUT/POST/DELETE requests with websocket data to obtain the
        most accurate view of the exchange state."

        This endpoint shows when data from GetBalance, GetOrders, GetFills,
        and GetPositions was last updated.

        Returns:
            Dict with:
            - as_of_time (str): ISO 8601 timestamp of last data validation

        Example:
            result = await client.get_user_data_timestamp()
            print(f"Data freshness: {result['as_of_time']}")
        """
        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/exchange/user_data_timestamp",
            require_auth=True  # This requires auth (user-specific data)
        )

    # ========================================================================
    # Pagination Helpers (per Kalshi Reference: Understanding Pagination)
    # ========================================================================

    async def get_all_markets(
        self,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
        max_items: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Auto-paginate through all markets.

        Per Kalshi Reference docs: "cursor-based pagination to efficiently navigate
        through large datasets."

        Args:
            event_ticker: Filter by event ticker
            series_ticker: Filter by series ticker
            status: Filter by market status
            max_items: Maximum total items to fetch (None = unlimited)

        Returns:
            List of all markets

        Example:
            # Get all open markets for a series
            markets = await client.get_all_markets(
                series_ticker="KXHIGHNY",
                status="open"
            )
        """
        all_markets = []
        cursor = None
        page_count = 0

        while True:
            page_count += 1
            result = await self.get_markets(
                limit=100,
                cursor=cursor,
                event_ticker=event_ticker,
                series_ticker=series_ticker,
                status=status
            )

            markets = result.get('markets', [])
            all_markets.extend(markets)

            self.logger.debug(
                f"Pagination: Fetched page {page_count}, "
                f"{len(markets)} markets, total: {len(all_markets)}"
            )

            # Check stopping conditions
            if max_items and len(all_markets) >= max_items:
                return all_markets[:max_items]

            cursor = result.get('cursor')
            if not cursor:
                break

        return all_markets

    async def get_all_events(
        self,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
        max_items: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Auto-paginate through all events.

        Args:
            series_ticker: Filter by series ticker
            status: Filter by status
            max_items: Maximum total items to fetch (None = unlimited)

        Returns:
            List of all events
        """
        all_events = []
        cursor = None

        while True:
            result = await self.get_events(
                series_ticker=series_ticker,
                status=status,
                limit=200,
                cursor=cursor
            )

            events = result.get('events', [])
            all_events.extend(events)

            if max_items and len(all_events) >= max_items:
                return all_events[:max_items]

            cursor = result.get('cursor')
            if not cursor:
                break

        return all_events

    async def get_all_series(
        self,
        tags: Optional[List[str]] = None,
        max_items: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Auto-paginate through all series.

        Args:
            tags: Filter by tags
            max_items: Maximum total items to fetch (None = unlimited)

        Returns:
            List of all series
        """
        all_series = []
        cursor = None

        while True:
            result = await self.get_series(
                limit=100,
                cursor=cursor,
                tags=tags
            )

            series = result.get('series', [])
            all_series.extend(series)

            if max_items and len(all_series) >= max_items:
                return all_series[:max_items]

            cursor = result.get('cursor')
            if not cursor:
                break

        return all_series

    # ============================================================================
    # INCENTIVE PROGRAMS (API Part 6)
    # ============================================================================

    async def get_incentive_programs(
        self,
        status: Optional[str] = None,
        incentive_type: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List incentive programs (rewards for trading activity).

        Per Kalshi API: Incentives are rewards programs for trading activity
        on specific markets.

        Args:
            status: Filter by status (all, active, upcoming, closed, paid_out)
                   Default: all
            incentive_type: Filter by type (all, liquidity, volume)
                          Default: all
            limit: Number of results per page (1-10000, default 100)
            cursor: Pagination cursor

        Returns:
            Dict with:
            - incentive_programs: Array of incentive objects with:
                - id: Program identifier
                - market_ticker: Associated market
                - incentive_type: Type (liquidity/volume)
                - start_date, end_date: Program duration
                - period_reward: Reward amount
                - paid_out: Whether rewards have been distributed
                - discount_factor_bps: Discount factor in basis points
                - target_size: Target size for program
            - next_cursor: Pagination cursor

        Example:
            # Get active liquidity incentive programs
            programs = await client.get_incentive_programs(
                status="active",
                incentive_type="liquidity"
            )
        """
        params = {}
        if status:
            params["status"] = status
        if incentive_type:
            params["type"] = incentive_type
        if limit:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/incentive_programs",
            params=params,
            require_auth=False
        )

    # ============================================================================
    # FCM ENDPOINTS (API Part 6) - FCM Members Only
    # ============================================================================

    async def get_fcm_orders(
        self,
        subtrader_id: str,
        cursor: Optional[str] = None,
        event_ticker: Optional[str] = None,
        ticker: Optional[str] = None,
        min_ts: Optional[int] = None,
        max_ts: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get orders filtered by subtrader ID (FCM members only).

        Per Kalshi API: Requires FCM member access level.

        Args:
            subtrader_id: Specific subtrader ID (required for FCM members)
            cursor: Pagination cursor
            event_ticker: Filter by event ticker (comma-separated, max 10)
            ticker: Filter by market ticker
            min_ts: Filter orders after this Unix timestamp
            max_ts: Filter orders before this Unix timestamp
            status: Filter by status (resting, canceled, executed)
            limit: Number of results per page (1-1000, default 100)

        Returns:
            Dict with:
            - orders: Array of order objects
            - cursor: Pagination cursor

        Example:
            # Get orders for a subtrader
            orders = await client.get_fcm_orders(
                subtrader_id="subtrader-123",
                status="resting"
            )

        Note:
            This endpoint is only available to FCM members.
        """
        params = {"subtrader_id": subtrader_id}
        if cursor:
            params["cursor"] = cursor
        if event_ticker:
            params["event_ticker"] = event_ticker
        if ticker:
            params["ticker"] = ticker
        if min_ts:
            params["min_ts"] = min_ts
        if max_ts:
            params["max_ts"] = max_ts
        if status:
            params["status"] = status
        if limit:
            params["limit"] = limit

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/fcm/orders",
            params=params,
            require_auth=True
        )

    async def get_fcm_positions(
        self,
        subtrader_id: str,
        ticker: Optional[str] = None,
        event_ticker: Optional[str] = None,
        count_filter: Optional[str] = None,
        settlement_status: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get positions filtered by subtrader ID (FCM members only).

        Per Kalshi API: Requires FCM member access level.

        Args:
            subtrader_id: Specific subtrader ID (required for FCM members)
            ticker: Filter by market ticker
            event_ticker: Filter by event ticker
            count_filter: Restrict to positions with non-zero values (comma-separated)
            settlement_status: Filter by settlement status (all, unsettled, settled)
                             Default: unsettled
            limit: Number of results per page (1-1000, default 100)
            cursor: Pagination cursor

        Returns:
            Dict with:
            - market_positions: Array of market-level positions
            - event_positions: Array of event-level positions
            - cursor: Pagination cursor

        Example:
            # Get positions for a subtrader
            positions = await client.get_fcm_positions(
                subtrader_id="subtrader-123",
                settlement_status="unsettled"
            )

        Note:
            This endpoint is only available to FCM members.
        """
        params = {"subtrader_id": subtrader_id}
        if ticker:
            params["ticker"] = ticker
        if event_ticker:
            params["event_ticker"] = event_ticker
        if count_filter:
            params["count_filter"] = count_filter
        if settlement_status:
            params["settlement_status"] = settlement_status
        if limit:
            params["limit"] = limit
        if cursor:
            params["cursor"] = cursor

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/fcm/positions",
            params=params,
            require_auth=True
        )

    # ============================================================================
    # STRUCTURED TARGETS (API Part 6)
    # ============================================================================

    async def get_structured_targets(
        self,
        target_type: Optional[str] = None,
        competition: Optional[str] = None,
        page_size: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List structured targets with filtering.

        Per Kalshi API: Structured targets represent structured data for events.

        Args:
            target_type: Filter by structured target type
            competition: Filter by competition
            page_size: Number of items per page (1-2000, default 100)
            cursor: Pagination cursor

        Returns:
            Dict with:
            - structured_targets: Array of structured target objects with:
                - id: Target identifier
                - name: Target name
                - type: Target type
                - details: Type-specific details object
                - source_id: Source identifier
                - last_updated_ts: Last update timestamp
            - cursor: Pagination cursor

        Example:
            # Get structured targets for a competition
            targets = await client.get_structured_targets(
                competition="NFL",
                page_size=50
            )
        """
        params = {"page_size": page_size}
        if target_type:
            params["type"] = target_type
        if competition:
            params["competition"] = competition
        if cursor:
            params["cursor"] = cursor

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/structured_targets",
            params=params,
            require_auth=False
        )

    async def get_structured_target(
        self,
        structured_target_id: str
    ) -> Dict[str, Any]:
        """
        Get a specific structured target by ID.

        Per Kalshi API: Returns detailed information about a structured target.

        Args:
            structured_target_id: Structured target ID

        Returns:
            Dict with:
            - structured_target: Structured target object

        Example:
            target = await client.get_structured_target("target-123")
            print(f"Target: {target['structured_target']['name']}")
        """
        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/structured_targets/{structured_target_id}",
            require_auth=False
        )

    # ============================================================================
    # MILESTONES (API Part 6)
    # ============================================================================

    async def get_milestone(
        self,
        milestone_id: str
    ) -> Dict[str, Any]:
        """
        Get a specific milestone by ID.

        Per Kalshi API: Returns detailed information about a milestone.

        Args:
            milestone_id: Milestone ID

        Returns:
            Dict with:
            - milestone: Milestone object with:
                - id: Milestone identifier
                - category: Milestone category
                - type: Milestone type
                - start_date: Start date (RFC3339)
                - end_date: End date (RFC3339, nullable)
                - related_event_tickers: Array of related event tickers
                - primary_event_tickers: Array of primary event tickers
                - title: Milestone title
                - notification_message: Notification message
                - details: Type-specific details object
                - source_id: Source identifier
                - last_updated_ts: Last update timestamp

        Example:
            milestone = await client.get_milestone("milestone-123")
            print(f"Milestone: {milestone['milestone']['title']}")
        """
        return await self._make_authenticated_request(
            "GET",
            f"/trade-api/v2/milestones/{milestone_id}",
            require_auth=False
        )

    async def get_milestones(
        self,
        limit: int,
        minimum_start_date: Optional[str] = None,
        category: Optional[str] = None,
        competition: Optional[str] = None,
        source_id: Optional[str] = None,
        milestone_type: Optional[str] = None,
        related_event_ticker: Optional[str] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List milestones with filtering and pagination.

        Per Kalshi API: Milestones represent significant events or dates.

        Args:
            limit: Number of results per page (1-500, required)
            minimum_start_date: Minimum start date filter (RFC3339 timestamp)
            category: Filter by milestone category
            competition: Filter by competition
            source_id: Filter by source ID
            milestone_type: Filter by milestone type
            related_event_ticker: Filter by related event ticker
            cursor: Pagination cursor

        Returns:
            Dict with:
            - milestones: Array of milestone objects
            - cursor: Pagination cursor

        Example:
            # Get upcoming election milestones
            milestones = await client.get_milestones(
                limit=50,
                category="election",
                minimum_start_date="2024-01-01T00:00:00Z"
            )
        """
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")

        params = {"limit": limit}
        if minimum_start_date:
            params["minimum_start_date"] = minimum_start_date
        if category:
            params["category"] = category
        if competition:
            params["competition"] = competition
        if source_id:
            params["source_id"] = source_id
        if milestone_type:
            params["type"] = milestone_type
        if related_event_ticker:
            params["related_event_ticker"] = related_event_ticker
        if cursor:
            params["cursor"] = cursor

        return await self._make_authenticated_request(
            "GET",
            "/trade-api/v2/milestones",
            params=params,
            require_auth=False
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
        self.logger.info("Kalshi client closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
