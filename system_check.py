#!/usr/bin/env python3
"""
Comprehensive System Check for Kalshi AI Trading Bot

This script verifies that all components are properly installed and configured.
Run this before starting the bot to ensure everything is ready.

Usage:
    python system_check.py              # Basic check
    python system_check.py --detailed   # Detailed check with component tests
    python system_check.py --fix        # Attempt to fix issues
"""

import sys
import asyncio
import argparse
from pathlib import Path
from typing import Tuple, List, Dict


class SystemChecker:
    """Comprehensive system checker for the trading bot."""

    def __init__(self, detailed: bool = False, fix: bool = False):
        self.detailed = detailed
        self.fix = fix
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def print_header(self, text: str):
        """Print a formatted header."""
        print(f"\n{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}\n")

    def print_check(self, name: str, passed: bool, message: str = ""):
        """Print a check result."""
        status = "✅" if passed else "❌"
        print(f"{status} {name:<40} {message}")
        if not passed:
            self.issues.append(f"{name}: {message}")

    def print_warning(self, name: str, message: str):
        """Print a warning."""
        print(f"⚠️  {name:<40} {message}")
        self.warnings.append(f"{name}: {message}")

    def check_python_version(self) -> bool:
        """Check Python version compatibility."""
        version = sys.version_info
        required_major = 3
        required_minor = 10

        compatible = version.major == required_major and version.minor >= required_minor

        self.print_check(
            "Python Version",
            compatible,
            f"{version.major}.{version.minor}.{version.micro}" +
            ("" if compatible else f" (requires >={required_major}.{required_minor})")
        )
        return compatible

    def check_platform(self) -> bool:
        """Check platform compatibility."""
        platform = sys.platform
        supported = platform in ['darwin', 'linux', 'win32']

        platform_names = {
            'darwin': 'macOS',
            'linux': 'Linux',
            'win32': 'Windows'
        }

        self.print_check(
            "Platform",
            supported,
            platform_names.get(platform, platform)
        )
        return supported

    def check_dependencies(self) -> Tuple[bool, Dict[str, bool]]:
        """Check all required dependencies."""
        required_deps = {
            # Core
            'httpx': 'HTTP client',
            'aiohttp': 'Async HTTP',
            'aiosqlite': 'Async SQLite',
            'cryptography': 'API authentication',

            # AI/ML
            'openai': 'OpenAI/xAI client',
            'pandas': 'Data analysis',
            'numpy': 'Numerical computing',
            'scipy': 'Scientific computing',

            # Config
            'pydantic': 'Data validation',
            'dotenv': 'Environment variables',
            'structlog': 'Logging',

            # Web
            'flask': 'Dashboard'
        }

        optional_deps = {
            'websockets': 'Real-time data (300x faster)',
            'anthropic': 'Claude API',
            'pytest': 'Testing framework'
        }

        results = {}
        all_required_ok = True

        print("Required Dependencies:")
        for dep, desc in required_deps.items():
            try:
                # Special case for dotenv
                if dep == 'dotenv':
                    __import__('dotenv')
                else:
                    __import__(dep)
                results[dep] = True
                self.print_check(f"  {dep}", True, desc)
            except ImportError:
                results[dep] = False
                all_required_ok = False
                self.print_check(f"  {dep}", False, f"{desc} - MISSING")

        print("\nOptional Dependencies:")
        for dep, desc in optional_deps.items():
            try:
                __import__(dep)
                results[dep] = True
                self.print_check(f"  {dep}", True, desc)
            except ImportError:
                results[dep] = False
                self.print_warning(f"  {dep}", f"{desc} - Not installed (optional)")

        return all_required_ok, results

    def check_configuration(self) -> bool:
        """Check configuration files."""
        config_files = {
            '.env': 'Environment variables',
            'src/config/settings.py': 'Settings configuration',
            'requirements.txt': 'Dependencies list'
        }

        all_ok = True
        for file, desc in config_files.items():
            exists = Path(file).exists()
            self.print_check(f"  {file}", exists, desc)
            if not exists:
                all_ok = False

        return all_ok

    def check_api_keys(self) -> bool:
        """Check if API keys are configured."""
        try:
            from dotenv import load_dotenv
            import os
            load_dotenv()

            keys = {
                'KALSHI_EMAIL': 'Kalshi account',
                'KALSHI_PASSWORD': 'Kalshi password',
                'XAI_API_KEY': 'xAI Grok API'
            }

            all_ok = True
            for key, desc in keys.items():
                value = os.getenv(key)
                has_key = value is not None and len(value) > 0

                if has_key:
                    masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
                    self.print_check(f"  {key}", True, f"{desc} ({masked})")
                else:
                    self.print_check(f"  {key}", False, f"{desc} - NOT SET")
                    all_ok = False

            return all_ok

        except Exception as e:
            self.print_check("API Keys", False, f"Error checking: {e}")
            return False

    async def check_database(self) -> bool:
        """Check database initialization."""
        try:
            from src.utils.database import DatabaseManager

            db = DatabaseManager()
            await db.initialize()

            # Try a simple query
            import aiosqlite
            async with aiosqlite.connect(db.db_path) as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM markets")
                count = await cursor.fetchone()
                market_count = count[0] if count else 0

            self.print_check("Database", True, f"Initialized ({market_count} markets)")
            return True

        except Exception as e:
            self.print_check("Database", False, f"Error: {e}")
            return False

    async def check_kalshi_api(self) -> bool:
        """Check Kalshi API connectivity."""
        try:
            from src.clients.kalshi_client import KalshiClient
            from src.config.settings import settings

            if not settings.kalshi_email or not settings.kalshi_password:
                self.print_warning("Kalshi API", "Credentials not configured")
                return False

            client = KalshiClient()

            # Try to get balance
            balance_response = await client.get_balance()
            balance = balance_response.get('balance', 0) / 100

            self.print_check("Kalshi API", True, f"Connected (Balance: ${balance:.2f})")
            await client.close()
            return True

        except Exception as e:
            self.print_check("Kalshi API", False, f"Error: {e}")
            return False

    async def check_xai_api(self) -> bool:
        """Check xAI API connectivity."""
        try:
            from src.config.settings import settings
            import httpx

            if not settings.xai_api_key:
                self.print_warning("xAI API", "API key not configured")
                return False

            # Quick API test
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.x.ai/v1/models",
                    headers={"Authorization": f"Bearer {settings.xai_api_key}"},
                    timeout=10.0
                )

                if response.status_code == 200:
                    models = response.json().get('data', [])
                    model_count = len(models)
                    self.print_check("xAI API", True, f"Connected ({model_count} models available)")
                    return True
                else:
                    self.print_check("xAI API", False, f"HTTP {response.status_code}")
                    return False

        except Exception as e:
            self.print_check("xAI API", False, f"Error: {e}")
            return False

    def check_phases(self) -> Dict[str, bool]:
        """Check which phases are available."""
        phases = {}

        # Phase 1: Core
        try:
            from src.jobs.decide import make_decision_for_market
            from src.jobs.execute import execute_position
            phases['phase1'] = True
            self.print_check("Phase 1 (Core)", True, "Decision + Execution")
        except:
            phases['phase1'] = False
            self.print_check("Phase 1 (Core)", False, "Not available")

        # Phase 2: Advanced Position Sizing
        try:
            from src.utils.advanced_position_sizing import AdvancedPositionSizer
            phases['phase2'] = True
            self.print_check("Phase 2 (Advanced)", True, "Position Sizing + Correlation")
        except:
            phases['phase2'] = False
            self.print_check("Phase 2 (Advanced)", False, "Not available")

        # Phase 3: Real-time Data
        try:
            from src.utils.price_history import PriceHistoryTracker
            from src.utils.websocket_manager import WebSocketManager
            phases['phase3'] = True
            self.print_check("Phase 3 (Real-time)", True, "WebSocket + Price History")
        except:
            phases['phase3'] = False
            self.print_warning("Phase 3 (Real-time)", "WebSocket not available (optional)")

        # Phase 4: Institutional Execution
        try:
            from src.utils.smart_execution import SmartOrderExecutor
            from src.jobs.enhanced_execute import execute_position_enhanced
            phases['phase4'] = True
            self.print_check("Phase 4 (Institutional)", True, "Smart Execution + Order Book Analysis")
        except:
            phases['phase4'] = False
            self.print_check("Phase 4 (Institutional)", False, "Not available")

        return phases

    async def run_full_check(self):
        """Run full system check."""
        self.print_header("KALSHI AI TRADING BOT - SYSTEM CHECK")

        # Basic checks
        self.print_header("1. PLATFORM & PYTHON")
        python_ok = self.check_python_version()
        platform_ok = self.check_platform()

        # Dependencies
        self.print_header("2. DEPENDENCIES")
        deps_ok, dep_results = self.check_dependencies()

        # Configuration
        self.print_header("3. CONFIGURATION")
        config_ok = self.check_configuration()

        # API Keys
        self.print_header("4. API KEYS")
        keys_ok = self.check_api_keys()

        # Phases
        self.print_header("5. TRADING SYSTEM PHASES")
        phases = self.check_phases()

        # Detailed checks (async)
        if self.detailed:
            self.print_header("6. DETAILED CHECKS (Async)")

            db_ok = await self.check_database()
            kalshi_ok = await self.check_kalshi_api()
            xai_ok = await self.check_xai_api()

        # Summary
        self.print_header("SUMMARY")

        basic_ok = python_ok and platform_ok and deps_ok and config_ok

        if basic_ok and keys_ok:
            print("✅ System is READY for trading!")
            print(f"\n   Phases Available: {sum(phases.values())}/4")
            for phase, available in phases.items():
                status = "✅" if available else "❌"
                print(f"     {status} {phase.upper()}")
        else:
            print("❌ System has issues that need to be fixed:")
            for issue in self.issues:
                print(f"   • {issue}")

        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} warnings:")
            for warning in self.warnings[:5]:  # Show first 5
                print(f"   • {warning}")

        print(f"\n{'='*70}\n")

        if self.fix and self.issues:
            print("🔧 Attempting to fix issues...\n")
            self.attempt_fixes()

    def attempt_fixes(self):
        """Attempt to fix common issues."""
        print("Auto-fix not yet implemented.")
        print("Please manually install missing dependencies:")
        print("  pip install -r requirements.txt")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive system check for Kalshi AI Trading Bot"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Run detailed checks including API connectivity"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix issues automatically"
    )

    args = parser.parse_args()

    checker = SystemChecker(detailed=args.detailed, fix=args.fix)
    await checker.run_full_check()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 System check interrupted by user")
    except Exception as e:
        print(f"\n\n❌ System check error: {e}")
        import traceback
        traceback.print_exc()
