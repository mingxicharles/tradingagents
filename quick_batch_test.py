"""
Quick batch test example

Usage:
    python quick_batch_test.py              # Run first 5 tests
    python quick_batch_test.py --all        # Run all tests
    python quick_batch_test.py --max 10     # Run 10 tests
    python quick_batch_test.py --verbose    # Show details
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from batch_test import run_batch_test


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick batch test")
    parser.add_argument("--max", type=int, default=5, help="Max tests (default: 5)")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--symbol", type=str, help="Filter by symbol")
    
    args = parser.parse_args()
    
    max_tests = None if args.all else args.max
    
    print(f"\nRunning batch test (max: {max_tests or 'all'})")
    
    await run_batch_test(
        max_tests=max_tests,
        verbose=args.verbose,
        symbol=args.symbol,
        save_results=True
    )


if __name__ == "__main__":
    asyncio.run(main())


