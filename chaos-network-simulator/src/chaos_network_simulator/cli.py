import argparse
import sys
import urllib.request
import time
from typing import NoReturn

from .scenario import Scenario
from .runner import ChaosRunner

def http_get(url: str) -> None:
    """Simple HTTP GET target."""
    with urllib.request.urlopen(url, timeout=5) as response:
        response.read()

def main() -> NoReturn:
    parser = argparse.ArgumentParser(description="Chaos Network Simulator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a scenario file")
    validate_parser.add_argument("scenario_file", help="Path to the scenario JSON file")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a scenario against a target")
    run_parser.add_argument("scenario_file", help="Path to the scenario JSON file")
    run_parser.add_argument("--target", required=True, help="Target URL to test (HTTP GET)")
    run_parser.add_argument("--iterations", type=int, default=10, help="Number of iterations")
    run_parser.add_argument("--output", help="Output file for results (JSON)")

    args = parser.parse_args()

    if args.command == "validate":
        try:
            Scenario.from_json(args.scenario_file)
            print(f"Scenario '{args.scenario_file}' is valid.")
            sys.exit(0)
        except Exception as e:
            print(f"Error validating scenario: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "run":
        try:
            scenario = Scenario.from_json(args.scenario_file)
        except Exception as e:
            print(f"Error loading scenario: {e}", file=sys.stderr)
            sys.exit(1)

        print(f"Running scenario from '{args.scenario_file}' against {args.target} for {args.iterations} iterations...")
        print(f"Configuration: {scenario}")

        runner = ChaosRunner(scenario)
        
        # We wrap the target to pass to runner
        # Note: urllib might raise URLError, which counts as a failure in runner
        result = runner.run(http_get, args.target, iterations=args.iterations)

        print("\nResults:")
        print(f"  Successes: {result.successes}")
        print(f"  Failures:  {result.failures}")
        print(f"  Dropped:   {result.dropped}")
        print(f"  Total:     {result.total_requests}")
        print("-" * 20)
        print(f"  Avg Latency: {result.avg_latency_ms:.2f} ms")
        print(f"  P50 Latency: {result.p50_ms:.2f} ms")
        print(f"  P90 Latency: {result.p90_ms:.2f} ms")
        print(f"  P99 Latency: {result.p99_ms:.2f} ms")

        if args.output:
            # TODO: Implement JSON output for results
            print(f"Warning: Output to file not yet implemented.")
        
        sys.exit(0 if result.failures == 0 and result.dropped == 0 else 1)

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
