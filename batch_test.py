"""
Batch Test Script for Trading Analysis

Runs the LLM controller on each row of the CSV file and evaluates accuracy
by comparing predictions with actual next-day price movements.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))

from tradingagents.controller import LLMController
from tradingagents.agents import build_agents
from tradingagents.llm import build_llm_client
from tradingagents.models import AnalysisRequest
from tradingagents.config_api import validate_api_setup
from tradingagents.dataflows.csv_data_loader import get_csv_loader


def evaluate_decision(recommendation: str, actual_return: float, threshold: float = 0.5) -> dict:
    """
    Evaluate if the decision was correct
    
    Args:
        recommendation: BUY/SELL/HOLD
        actual_return: Actual return percentage
        threshold: Minimum return % to consider significant
        
    Returns:
        Dictionary with evaluation results
    """
    actual_direction = "UP" if actual_return > threshold else "DOWN" if actual_return < -threshold else "FLAT"
    
    # Determine if prediction was correct
    if recommendation == "BUY":
        correct = actual_return > 0
        strong_correct = actual_return > threshold
    elif recommendation == "SELL":
        correct = actual_return < 0
        strong_correct = actual_return < -threshold
    else:  # HOLD
        correct = abs(actual_return) <= threshold
        strong_correct = correct
    
    return {
        "correct": correct,
        "strong_correct": strong_correct,
        "actual_direction": actual_direction,
        "actual_return": actual_return,
        "prediction": recommendation
    }


async def run_single_test(controller, test_case, verbose=False):
    """Run test for a single row"""
    
    symbol = test_case['symbol']
    date = str(test_case['date'])
    actual_return = test_case['actual_return']
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"Testing: {symbol} on {date}")
        print(f"Current Price: ${test_case['close']:.2f}")
        print(f"Next Day Price: ${test_case['next_close']:.2f}")
        print(f"Actual Return: {actual_return:+.2f}%")
        print(f"{'='*70}")
    
    # Create request
    request = AnalysisRequest(
        symbol=symbol,
        horizon="1d",
        trade_date=date,
        market_context=f"Analyzing {symbol} on {date}"
    )
    
    try:
        # Run analysis
        decision, trajectory = await controller.analyze(request)
        
        # Evaluate
        evaluation = evaluate_decision(
            decision.recommendation,
            actual_return
        )
        
        result = {
            "symbol": symbol,
            "date": date,
            "current_price": test_case['close'],
            "next_price": test_case['next_close'],
            "actual_return": actual_return,
            "prediction": decision.recommendation,
            "confidence": decision.confidence,
            "correct": evaluation["correct"],
            "strong_correct": evaluation["strong_correct"],
            "rationale": decision.rationale[:200] if decision.rationale else ""  # Truncate
        }
        
        if verbose:
            print(f"\nPrediction: {decision.recommendation} (confidence: {decision.confidence:.2%})")
            print(f"Result: {'[CORRECT]' if evaluation['correct'] else '[WRONG]'}")
            print(f"Rationale: {decision.rationale[:150]}...")
        
        return result
        
    except Exception as e:
        print(f"\n[ERROR] Error testing {symbol} on {date}: {str(e)}")
        return {
            "symbol": symbol,
            "date": date,
            "error": str(e),
            "correct": False,
            "strong_correct": False
        }


async def run_batch_test(
    csv_path=None,
    symbol=None,
    max_tests=None,
    verbose=False,
    save_results=True
):
    """
    Run batch testing on CSV data
    
    Args:
        csv_path: Path to CSV file
        symbol: Filter by symbol (None for all)
        max_tests: Maximum number of tests to run
        verbose: Print detailed output
        save_results: Save results to file
    """
    
    print("\n" + "="*70)
    print("BATCH TESTING: LLM TRADING ANALYSIS")
    print("="*70)
    
    # Validate API
    is_valid, message = validate_api_setup()
    if not is_valid:
        print(f"\n[ERROR] API not configured: {message}")
        return None
    
    print(f"[OK] API configured\n")
    
    # Load CSV data
    print("Loading CSV data...")
    loader = get_csv_loader(csv_path)
    test_cases = loader.get_test_cases(symbol=symbol, max_cases=max_tests)
    
    print(f"[OK] Found {len(test_cases)} test cases")
    if symbol:
        print(f"  Filtered by symbol: {symbol}")
    if max_tests:
        print(f"  Limited to: {max_tests} tests")
    print()
    
    # Build controller
    print("Initializing LLM Controller...")
    llm_client = build_llm_client()
    
    # Use CSV data loader for agents
    from tradingagents.dataflows.csv_data_loader import (
        get_stock_price_data_csv,
        get_technical_indicators_csv,
        get_company_info_csv,
        get_recent_news_csv
    )
    
    # Manually create agents with CSV data tools
    from tradingagents.agents.simple_agent import (
        create_news_agent,
        create_technical_agent,
        create_fundamental_agent
    )
    
    agents = {
        "news": create_news_agent(llm_client, [get_recent_news_csv, get_stock_price_data_csv]),
        "technical": create_technical_agent(llm_client, [get_stock_price_data_csv, get_technical_indicators_csv]),
        "fundamental": create_fundamental_agent(llm_client, [get_company_info_csv, get_stock_price_data_csv])
    }
    
    controller = LLMController(
        llm_client=llm_client,
        agents=agents,
        verbose=False  # Individual test verbosity
    )
    
    print("[OK] Controller initialized\n")
    
    # Run tests
    print(f"Running {len(test_cases)} tests...")
    print("-" * 70)
    
    results = []
    for idx, test_case in test_cases.iterrows():
        result = await run_single_test(controller, test_case, verbose=verbose)
        results.append(result)
        
        if not verbose:
            # Show progress
            status = "[OK]" if result.get("correct", False) else "[X]"
            print(f"{status} {result['symbol']} {result['date']} - {result.get('prediction', 'ERROR')}", end="")
            if result.get('actual_return'):
                print(f" (actual: {result['actual_return']:+.2f}%)")
            else:
                print()
    
    print("-" * 70)
    
    # Calculate statistics
    print("\n" + "="*70)
    print("BATCH TEST RESULTS")
    print("="*70)
    
    total_tests = len(results)
    successful_tests = [r for r in results if "error" not in r]
    failed_tests = [r for r in results if "error" in r]
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Successful: {len(successful_tests)}")
    print(f"Failed: {len(failed_tests)}")
    
    if len(successful_tests) > 0:
        correct = sum(1 for r in successful_tests if r["correct"])
        strong_correct = sum(1 for r in successful_tests if r["strong_correct"])
        
        accuracy = (correct / len(successful_tests)) * 100
        strong_accuracy = (strong_correct / len(successful_tests)) * 100
        
        print(f"\n{'Metric':<30} {'Value':<15}")
        print("-" * 45)
        print(f"{'Overall Accuracy:':<30} {accuracy:.1f}%")
        print(f"{'Strong Accuracy (>0.5%):':<30} {strong_accuracy:.1f}%")
        
        # Breakdown by prediction type
        buy_results = [r for r in successful_tests if r["prediction"] == "BUY"]
        sell_results = [r for r in successful_tests if r["prediction"] == "SELL"]
        hold_results = [r for r in successful_tests if r["prediction"] == "HOLD"]
        
        if buy_results:
            buy_acc = (sum(1 for r in buy_results if r["correct"]) / len(buy_results)) * 100
            print(f"{'BUY Accuracy:':<30} {buy_acc:.1f}% ({len(buy_results)} cases)")
        
        if sell_results:
            sell_acc = (sum(1 for r in sell_results if r["correct"]) / len(sell_results)) * 100
            print(f"{'SELL Accuracy:':<30} {sell_acc:.1f}% ({len(sell_results)} cases)")
        
        if hold_results:
            hold_acc = (sum(1 for r in hold_results if r["correct"]) / len(hold_results)) * 100
            print(f"{'HOLD Accuracy:':<30} {hold_acc:.1f}% ({len(hold_results)} cases)")
        
        # Average confidence
        avg_confidence = sum(r["confidence"] for r in successful_tests) / len(successful_tests)
        print(f"{'Average Confidence:':<30} {avg_confidence:.1%}")
        
        # Confidence vs accuracy
        high_conf = [r for r in successful_tests if r["confidence"] > 0.7]
        if high_conf:
            high_conf_acc = (sum(1 for r in high_conf if r["correct"]) / len(high_conf)) * 100
            print(f"{'High Confidence (>70%) Acc:':<30} {high_conf_acc:.1f}% ({len(high_conf)} cases)")
    
    # Save results
    if save_results and results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("batch_test_results")
        output_dir.mkdir(exist_ok=True)
        
        results_file = output_dir / f"batch_test_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "test_config": {
                    "csv_path": str(csv_path) if csv_path else "default",
                    "symbol": symbol,
                    "max_tests": max_tests,
                    "total_tests": total_tests,
                    "timestamp": timestamp
                },
                "summary": {
                    "accuracy": accuracy if successful_tests else 0,
                    "strong_accuracy": strong_accuracy if successful_tests else 0,
                    "total": total_tests,
                    "successful": len(successful_tests),
                    "failed": len(failed_tests)
                },
                "results": results
            }, f, indent=2, default=str)
        
        print(f"\n[OK] Results saved to: {results_file}")
    
    print("\n" + "="*70)
    
    return results


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch test trading analysis on CSV data")
    parser.add_argument("--csv", type=str, help="Path to CSV file")
    parser.add_argument("--symbol", type=str, help="Filter by symbol (e.g., AAPL)")
    parser.add_argument("--max-tests", type=int, help="Maximum number of tests to run")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output for each test")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to file")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_batch_test(
            csv_path=args.csv,
            symbol=args.symbol,
            max_tests=args.max_tests,
            verbose=args.verbose,
            save_results=not args.no_save
        ))
    except KeyboardInterrupt:
        print("\n\nBatch test interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


