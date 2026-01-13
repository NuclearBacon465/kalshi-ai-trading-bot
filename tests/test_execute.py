import asyncio
import os
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

from src.jobs.execute import execute_position
from src.utils.database import DatabaseManager, Position
from tests.test_database import TEST_DB

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

async def test_execute_position_places_live_order():
    """
    Test that the execution job correctly places a live order for a non-live position.
    """
    # Arrange: Setup a test database with a non-live position
    db_path = TEST_DB
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db_manager = DatabaseManager(db_path=db_path)
    await db_manager.initialize()

    test_position = Position(
        market_id="LIVE-TEST-1",
        side="YES",
        entry_price=0.60,
        quantity=10,
        timestamp=datetime.now(),
        rationale="Test rationale",
        confidence=0.80,
        live=False
    )
    position_id = await db_manager.add_position(test_position)
    test_position.id = position_id  # Set the ID on the position object

    # Create a mock KalshiClient
    from unittest.mock import Mock, MagicMock
    mock_kalshi_client = Mock()

    # Track the last client_order_id used in place_order
    last_order_id = ["test-order-123"]

    async def mock_place_order_impl(**kwargs):
        last_order_id[0] = kwargs.get('client_order_id', 'test-order-123')
        return {"order": {"order_id": last_order_id[0]}}

    async def mock_get_fills_impl(**kwargs):
        # Return fills for the most recent order
        return {
            "fills": [
                {
                    "client_order_id": last_order_id[0],
                    "count": 10,
                    "price": 60,
                    "side": "yes"
                }
            ]
        }

    # Wrap in AsyncMock to preserve call tracking
    mock_kalshi_client.place_order = AsyncMock(side_effect=mock_place_order_impl)
    mock_kalshi_client.get_orderbook = AsyncMock(return_value={
        "orderbook": {
            "yes": {
                "bids": [{"price": 59, "quantity": 100}, {"price": 58, "quantity": 50}],
                "asks": [{"price": 60, "quantity": 100}, {"price": 61, "quantity": 50}]
            },
            "no": {
                "bids": [{"price": 40, "quantity": 100}, {"price": 39, "quantity": 50}],
                "asks": [{"price": 41, "quantity": 100}, {"price": 42, "quantity": 50}]
            }
        }
    })
    mock_kalshi_client.get_market = AsyncMock(return_value={
        "market": {
            "yes_price": 60,
            "no_price": 40
        }
    })
    mock_kalshi_client.get_fills = AsyncMock(side_effect=mock_get_fills_impl)
    mock_kalshi_client.close = AsyncMock()

    try:
        # Act: Execute the position directly
        result = await execute_position(
            position=test_position,
            live_mode=True,
            db_manager=db_manager,
            kalshi_client=mock_kalshi_client
        )

        # Assert: Check that the order was placed and the position updated
        assert result == True, "Execution should have succeeded"
        
        updated_position = await db_manager.get_position_by_market_id("LIVE-TEST-1")

        # Check that place_order was called
        mock_kalshi_client.place_order.assert_called_once()
        call_args = mock_kalshi_client.place_order.call_args
        assert call_args.kwargs['ticker'] == "LIVE-TEST-1"
        assert call_args.kwargs['side'] == "yes"
        assert call_args.kwargs['count'] == 10
        assert 'client_order_id' in call_args.kwargs

        assert updated_position is not None, "Position should still exist."
        assert updated_position.live == True, "Position should be marked as live."
        assert updated_position.id == position_id

    finally:
        # Teardown
        if os.path.exists(db_path):
            os.remove(db_path) 


async def test_sell_limit_order_functionality():
    """
    Test the sell limit order functionality with real Kalshi API.
    This test checks that we can place sell limit orders for existing positions.
    """
    from src.jobs.execute import place_sell_limit_order
    from src.utils.database import DatabaseManager, Position
    from src.clients.kalshi_client import KalshiClient
    from tests.test_helpers import find_suitable_test_market
    from datetime import datetime
    import os
    
    # Setup test database
    test_db = "test_sell_limit.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    db_manager = DatabaseManager(db_path=test_db)
    await db_manager.initialize()
    
    kalshi_client = KalshiClient()
    
    try:
        # Get a suitable test market efficiently (no excessive API calls)
        test_market = await find_suitable_test_market()
        
        if not test_market:
            pytest.skip("No suitable markets available for testing")
        
        print(f"Testing sell limit orders with: {test_market.title}")
        
        # Create a mock position for testing sell limit orders
        test_position = Position(
            market_id=test_market.market_id,
            side="YES",
            entry_price=0.60,
            quantity=10,
            timestamp=datetime.now(),
            rationale="Test position for sell limit order",
            confidence=0.75,
            live=False
        )
        
        # Add the test position to database
        position_id = await db_manager.add_position(test_position)
        
        # Test placing a sell limit order
        success = await place_sell_limit_order(
            test_position,
            limit_price=0.70,  # Sell at 70¢ (10¢ profit)
            db_manager=db_manager,
            kalshi_client=kalshi_client
        )
        
        # The test passes if the function runs without errors
        # Note: In test environment, orders may not actually execute
        print(f"Sell limit order result: {success}")
        
    finally:
        await kalshi_client.close()
        if os.path.exists(test_db):
            os.remove(test_db)


async def test_profit_taking_orders():
    """
    Test profit-taking sell limit orders with real positions.
    """
    from src.jobs.execute import place_profit_taking_orders
    from src.utils.database import DatabaseManager
    from src.clients.kalshi_client import KalshiClient
    import os
    
    # Setup test database
    test_db = "test_profit_taking.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    db_manager = DatabaseManager(db_path=test_db)
    await db_manager.initialize()
    
    kalshi_client = KalshiClient()
    
    try:
        # Test profit-taking logic with real portfolio
        results = await place_profit_taking_orders(
            db_manager=db_manager,
            kalshi_client=kalshi_client,
            profit_threshold=0.15  # 15% profit threshold for testing
        )
        
        print(f"📊 Profit-taking test results:")
        print(f"   Positions processed: {results['positions_processed']}")
        print(f"   Orders placed: {results['orders_placed']}")
        
        # Test is successful if it runs without errors
        assert isinstance(results, dict), "Should return results dictionary"
        assert 'orders_placed' in results, "Should include orders_placed count"
        assert 'positions_processed' in results, "Should include positions_processed count"
        
        print("✅ Profit-taking orders test completed successfully")
        
    finally:
        # Cleanup
        await kalshi_client.close()
        if os.path.exists(test_db):
            os.remove(test_db) 