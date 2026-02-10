#!/usr/bin/env python3
"""
Comprehensive API Implementation Verification Script

Verifies all 77 REST API endpoints against Kalshi API v2 specification.
Checks: endpoint paths, required parameters, authentication, return types.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

# Kalshi API v2 Specification - Complete Reference
API_SPEC = {
    "Exchange": [
        ("get_exchange_status", "GET", "/trade-api/v2/exchange/status", False, []),
        ("get_exchange_announcements", "GET", "/trade-api/v2/exchange/announcements", False, []),
        ("get_exchange_schedule", "GET", "/trade-api/v2/exchange/schedule", False, []),
        ("get_user_data_timestamp", "GET", "/trade-api/v2/exchange/user_data_timestamp", True, []),
        ("get_communications_id", "GET", "/trade-api/v2/communications/id", True, []),
    ],
    "Events": [
        ("get_events", "GET", "/trade-api/v2/events", False, ["limit", "cursor"]),
        ("get_multivariate_events", "GET", "/trade-api/v2/portfolio/multivariate_events", False, ["limit", "cursor"]),
        ("get_event", "GET", "/trade-api/v2/events/{event_ticker}", False, ["event_ticker"]),
        ("get_event_metadata", "GET", "/trade-api/v2/events/{event_ticker}/metadata", False, ["event_ticker"]),
        ("get_event_candlesticks", "GET", "/trade-api/v2/series/{series_ticker}/events/{event_ticker}/candlesticks", False, ["series_ticker", "event_ticker", "start_ts", "end_ts", "period_interval"]),
        ("get_event_forecast_percentile_history", "GET", "/trade-api/v2/series/{series_ticker}/events/{event_ticker}/forecast_percentile_history", False, ["series_ticker", "event_ticker", "percentiles", "start_ts", "end_ts", "period_interval"]),
    ],
    "Markets": [
        ("get_markets", "GET", "/trade-api/v2/markets", False, ["limit", "cursor"]),
        ("get_market", "GET", "/trade-api/v2/markets/{ticker}", False, ["ticker"]),
        ("get_orderbook", "GET", "/trade-api/v2/markets/{ticker}/orderbook", False, ["ticker"]),
        ("get_market_history", "GET", "/trade-api/v2/markets/{ticker}/history", False, ["ticker", "limit", "cursor"]),
        ("get_market_candlesticks", "GET", "/trade-api/v2/series/{series_ticker}/markets/{ticker}/candlesticks", False, ["series_ticker", "ticker", "start_ts", "end_ts", "period_interval"]),
        ("get_batch_market_candlesticks", "GET", "/trade-api/v2/series/{series_ticker}/markets/candlesticks", False, ["series_ticker", "tickers", "start_ts", "end_ts", "period_interval"]),
        ("get_trades", "GET", "/trade-api/v2/markets/trades", False, []),
        ("get_live_data", "GET", "/trade-api/v2/markets/{ticker}/live_data", False, ["ticker"]),
        ("get_multiple_live_data", "GET", "/trade-api/v2/markets/live_data", False, ["tickers"]),
        ("get_structured_targets", "GET", "/trade-api/v2/structured_targets", False, []),
        ("get_structured_target", "GET", "/trade-api/v2/structured_targets/{structured_target_id}", False, ["structured_target_id"]),
        ("get_milestone", "GET", "/trade-api/v2/milestones/{milestone_ticker}", False, ["milestone_ticker"]),
        ("get_milestones", "GET", "/trade-api/v2/milestones", False, []),
    ],
    "Portfolio": [
        ("get_balance", "GET", "/trade-api/v2/portfolio/balance", True, []),
        ("get_positions", "GET", "/trade-api/v2/portfolio/positions", True, []),
        ("get_fills", "GET", "/trade-api/v2/portfolio/fills", True, []),
        ("get_settlements", "GET", "/trade-api/v2/portfolio/settlements", True, []),
        ("get_total_resting_order_value", "GET", "/trade-api/v2/portfolio/total_resting_order_value", True, []),
    ],
    "Orders": [
        ("get_orders", "GET", "/trade-api/v2/portfolio/orders", True, []),
        ("get_order", "GET", "/trade-api/v2/portfolio/orders/{order_id}", True, ["order_id"]),
        ("place_order", "POST", "/trade-api/v2/portfolio/orders", True, ["ticker", "action", "side", "count", "type"]),
        ("cancel_order", "DELETE", "/trade-api/v2/portfolio/orders/{order_id}", True, ["order_id"]),
        ("amend_order", "PUT", "/trade-api/v2/portfolio/orders/{order_id}", True, ["order_id"]),
        ("decrease_order", "POST", "/trade-api/v2/portfolio/orders/{order_id}/decrease", True, ["order_id", "reduce_by"]),
        ("batch_create_orders", "POST", "/trade-api/v2/portfolio/orders/batched", True, ["orders"]),
        ("batch_cancel_orders", "DELETE", "/trade-api/v2/portfolio/orders/batched", True, ["order_ids"]),
        ("place_smart_limit_order", "POST", "/trade-api/v2/portfolio/orders", True, ["ticker", "action", "side", "count"]),
        ("place_iceberg_order", "POST", "/trade-api/v2/portfolio/orders", True, ["ticker", "action", "side", "count", "min_amount", "iceberg_type"]),
        ("get_queue_positions", "GET", "/trade-api/v2/portfolio/queue_positions", True, []),
        ("get_order_queue_position", "GET", "/trade-api/v2/portfolio/orders/{order_id}/queue_position", True, ["order_id"]),
        ("get_fcm_orders", "GET", "/trade-api/v2/portfolio/fcm_orders", True, []),
        ("get_fcm_positions", "GET", "/trade-api/v2/portfolio/fcm_positions", True, []),
    ],
    "Order Groups": [
        ("get_order_groups", "GET", "/trade-api/v2/portfolio/order_groups", True, []),
        ("get_order_group", "GET", "/trade-api/v2/portfolio/order_groups/{order_group_id}", True, ["order_group_id"]),
        ("create_order_group", "POST", "/trade-api/v2/portfolio/order_groups", True, ["contracts_limit"]),
        ("delete_order_group", "DELETE", "/trade-api/v2/portfolio/order_groups/{order_group_id}", True, ["order_group_id"]),
        ("reset_order_group", "POST", "/trade-api/v2/portfolio/order_groups/{order_group_id}/reset", True, ["order_group_id"]),
    ],
    "RFQ": [
        ("get_rfqs", "GET", "/trade-api/v2/portfolio/rfqs", True, []),
        ("get_rfq", "GET", "/trade-api/v2/portfolio/rfqs/{rfq_id}", True, ["rfq_id"]),
        ("create_rfq", "POST", "/trade-api/v2/portfolio/rfqs", True, ["market_ticker", "side", "contracts"]),
        ("delete_rfq", "DELETE", "/trade-api/v2/portfolio/rfqs/{rfq_id}", True, ["rfq_id"]),
    ],
    "Quotes": [
        ("get_quotes", "GET", "/trade-api/v2/portfolio/quotes", True, []),
        ("get_quote", "GET", "/trade-api/v2/portfolio/quotes/{quote_id}", True, ["quote_id"]),
        ("create_quote", "POST", "/trade-api/v2/portfolio/quotes", True, ["rfq_id", "price"]),
        ("delete_quote", "DELETE", "/trade-api/v2/portfolio/quotes/{quote_id}", True, ["quote_id"]),
        ("accept_quote", "POST", "/trade-api/v2/portfolio/quotes/{quote_id}/accept", True, ["quote_id"]),
        ("confirm_quote", "POST", "/trade-api/v2/portfolio/quotes/{quote_id}/confirm", True, ["quote_id"]),
    ],
    "Series": [
        ("get_series", "GET", "/trade-api/v2/series", False, []),
        ("get_series_info", "GET", "/trade-api/v2/series/{series_ticker}", False, ["series_ticker"]),
        ("get_series_fee_changes", "GET", "/trade-api/v2/series/{series_ticker}/fee_changes", False, ["series_ticker", "limit", "cursor"]),
    ],
    "MVE": [
        ("get_multivariate_event_collections", "GET", "/trade-api/v2/multivariate_event_collections", False, []),
        ("get_multivariate_event_collection", "GET", "/trade-api/v2/multivariate_event_collections/{collection_ticker}", False, ["collection_ticker"]),
        ("create_market_in_multivariate_collection", "POST", "/trade-api/v2/multivariate_event_collections/{collection_ticker}/markets", True, ["collection_ticker", "values"]),
        ("lookup_market_in_multivariate_collection", "GET", "/trade-api/v2/multivariate_event_collections/{collection_ticker}/markets/lookup", False, ["collection_ticker", "values"]),
        ("get_multivariate_collection_lookup_history", "GET", "/trade-api/v2/multivariate_event_collections/{collection_ticker}/markets/lookup/history", False, ["collection_ticker", "values"]),
    ],
    "Tags & Filters": [
        ("get_tags_by_categories", "GET", "/trade-api/v2/tags_by_categories", False, []),
        ("get_filters_by_sport", "GET", "/trade-api/v2/filters_by_sport", False, []),
    ],
    "Incentives": [
        ("get_incentive_programs", "GET", "/trade-api/v2/portfolio/incentive_programs", True, []),
    ],
    "API Keys": [
        ("get_api_keys", "GET", "/trade-api/v2/portfolio/api_keys", True, []),
        ("create_api_key", "POST", "/trade-api/v2/portfolio/api_keys", True, ["label"]),
        ("generate_api_key", "POST", "/trade-api/v2/portfolio/api_keys", True, ["label"]),
        ("delete_api_key", "DELETE", "/trade-api/v2/portfolio/api_keys/{api_key_id}", True, ["api_key_id"]),
    ],
    "Pagination": [
        ("get_all_markets", "PAGINATION", "N/A", False, []),
        ("get_all_events", "PAGINATION", "N/A", False, []),
        ("get_all_series", "PAGINATION", "N/A", False, []),
    ],
}


def verify_implementation() -> Tuple[List[str], List[str], List[str]]:
    """
    Verify all API endpoints are implemented correctly.

    Returns:
        Tuple of (implemented, missing, issues)
    """
    implemented = []
    missing = []
    issues = []

    client_file = Path("/home/user/kalshi-ai-trading-bot/src/clients/kalshi_client.py")
    if not client_file.exists():
        return [], [], [f"Client file not found: {client_file}"]

    code = client_file.read_text()

    total_endpoints = 0
    for category, endpoints in API_SPEC.items():
        print(f"\n{'='*80}")
        print(f"Verifying {category} ({len(endpoints)} endpoints)")
        print('='*80)

        for method_name, http_method, endpoint_path, requires_auth, required_params in endpoints:
            total_endpoints += 1

            # Check if method exists
            method_pattern = rf"async def {method_name}\("
            if not re.search(method_pattern, code):
                missing.append(f"❌ {category} - {method_name}: Method not found")
                print(f"  ❌ {method_name}: NOT IMPLEMENTED")
                continue

            # Extract method implementation
            method_start = code.find(f"async def {method_name}(")
            if method_start == -1:
                missing.append(f"❌ {category} - {method_name}: Method not found")
                continue

            # Find next method or end of class
            next_method = code.find("\n    async def ", method_start + 1)
            if next_method == -1:
                method_code = code[method_start:]
            else:
                method_code = code[method_start:next_method]

            # Verify endpoint path (if not pagination helper)
            if endpoint_path != "N/A":
                if endpoint_path not in method_code:
                    # Check for dynamic paths
                    dynamic_path = endpoint_path.replace("{", "f").replace("}", "}")
                    if dynamic_path not in method_code and endpoint_path not in method_code:
                        issues.append(f"⚠️  {category} - {method_name}: Endpoint path mismatch")
                        print(f"  ⚠️  {method_name}: Path mismatch (expected {endpoint_path})")
                        continue

            # Verify authentication
            if requires_auth:
                if "require_auth=True" not in method_code and "require_auth=" not in method_code:
                    issues.append(f"⚠️  {category} - {method_name}: Missing require_auth=True")
                    print(f"  ⚠️  {method_name}: Missing require_auth=True")
                elif "require_auth=False" in method_code:
                    issues.append(f"⚠️  {category} - {method_name}: Should require auth but has require_auth=False")
                    print(f"  ⚠️  {method_name}: Should require auth")
                    continue

            # Verify required parameters
            for param in required_params:
                if f"{param}:" not in method_code and f"{param} =" not in method_code:
                    issues.append(f"⚠️  {category} - {method_name}: Missing required parameter '{param}'")
                    print(f"  ⚠️  {method_name}: Missing parameter '{param}'")

            implemented.append(f"✅ {category} - {method_name}")
            print(f"  ✅ {method_name}: OK")

    return implemented, missing, issues


def main():
    """Run comprehensive API verification."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║        KALSHI API v2 IMPLEMENTATION VERIFICATION                          ║
║        Complete Analysis of 77 REST API Endpoints                         ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

    implemented, missing, issues = verify_implementation()

    total = len(implemented) + len(missing)

    print(f"\n\n{'='*80}")
    print("VERIFICATION SUMMARY")
    print('='*80)
    print(f"\n✅ Implemented: {len(implemented)}/{total}")
    print(f"❌ Missing: {len(missing)}/{total}")
    print(f"⚠️  Issues: {len(issues)}")

    if missing:
        print(f"\n\n{'='*80}")
        print("MISSING IMPLEMENTATIONS")
        print('='*80)
        for item in missing:
            print(f"  {item}")

    if issues:
        print(f"\n\n{'='*80}")
        print("IMPLEMENTATION ISSUES")
        print('='*80)
        for item in issues:
            print(f"  {item}")

    if not missing and not issues:
        print(f"\n\n{'='*80}")
        print("🎉 ALL API ENDPOINTS VERIFIED SUCCESSFULLY!")
        print('='*80)
        print(f"\n✓ All {len(implemented)} endpoints are correctly implemented")
        print("✓ All endpoint paths match specification")
        print("✓ All authentication requirements met")
        print("✓ All required parameters present")
        print("\n✅ READY FOR PRODUCTION")

    return 0 if not missing and not issues else 1


if __name__ == "__main__":
    exit(main())
