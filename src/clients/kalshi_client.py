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


class KalshiAPIError(Exception):
    """Custom exception for Kalshi API errors."""
    pass


class KalshiClient(TradingLoggerMixin):
    """
    Kalshi API client for automated trading.
    Handles authentication, market data retrieval, and trade execution.
    """
    
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
            private_key_path: Path to private key file
            max_retries: Maximum number of retries for failed requests
            backoff_factor: Factor for exponential backoff
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
            path: Request path
        
        Returns:
            Base64 encoded signature
        """
        # Create message to sign: timestamp + method + path
        message = timestamp + method.upper() + path
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
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                last_exception = e
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
                self.logger.warning(f"Request failed with general exception. Retrying...", error=str(e), endpoint=endpoint)
                sleep_time = self.backoff_factor * (2 ** attempt)
                await asyncio.sleep(sleep_time)
        
        raise KalshiAPIError(f"API request failed after {self.max_retries} retries: {last_exception}")
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        return await self._make_authenticated_request("GET", "/trade-api/v2/portfolio/balance")
    
    async def get_positions(self, ticker: Optional[str] = None) -> Dict[str, Any]:
        """Get portfolio positions."""
        params = {}
        if ticker:
            params["ticker"] = ticker
        return await self._make_authenticated_request("GET", "/trade-api/v2/portfolio/positions", params=params)
    
    async def get_fills(self, ticker: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Get order fills.""" 
        params = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        return await self._make_authenticated_request("GET", "/trade-api/v2/portfolio/fills", params=params)
    
    async def get_orders(self, ticker: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """Get orders."""
        params = {}
        if ticker:
            params["ticker"] = ticker
        if status:
            params["status"] = status
        return await self._make_authenticated_request("GET", "/trade-api/v2/portfolio/orders", params=params)
    
    async def get_markets(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
        tickers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get markets data.
        
        Args:
            limit: Maximum number of markets to return
            cursor: Pagination cursor
            event_ticker: Filter by event ticker
            series_ticker: Filter by series ticker
            status: Filter by market status
            tickers: List of specific tickers to fetch
        
        Returns:
            Markets data
        """
        params = {"limit": limit}
        
        if cursor:
            params["cursor"] = cursor
        if event_ticker:
            params["event_ticker"] = event_ticker
        if series_ticker:
            params["series_ticker"] = series_ticker
        if status:
            params["status"] = status
        if tickers:
            params["tickers"] = ",".join(tickers)
        
        return await self._make_authenticated_request(
            "GET", "/trade-api/v2/markets", params=params, require_auth=True
        )
    
    async def get_market(self, ticker: str) -> Dict[str, Any]:
        """Get specific market data."""
        return await self._make_authenticated_request(
            "GET", f"/trade-api/v2/markets/{ticker}", require_auth=False
        )
    
    async def get_orderbook(self, ticker: str, depth: int = 100) -> Dict[str, Any]:
        """
        Get market orderbook.
        
        Args:
            ticker: Market ticker
            depth: Orderbook depth
        
        Returns:
            Orderbook data
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
        expiration_ts: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Place a trading order.
        
        Args:
            ticker: Market ticker
            client_order_id: Unique client order ID
            side: "yes" or "no"
            action: "buy" or "sell"
            count: Number of contracts
            type_: Order type ("market" or "limit")
            yes_price: Yes price in cents (for limit orders)
            no_price: No price in cents (for limit orders)
            expiration_ts: Order expiration timestamp
        
        Returns:
            Order response
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
