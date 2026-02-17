#!/usr/bin/env python3
"""
ARV Department Runner

Executes Agent Readiness Verification (ARV) checks for the IAM/ADK department.

Usage:
    python3 scripts/run_arv_department.py [options]

Options:
    --env ENV               Target environment (dev/staging/prod, default: dev)
    --category CATEGORY     Run only checks in this category
    --include-optional      Include optional/conditional checks even if not required
    --verbose               Show detailed output from checks

Exit Codes:
    0 - All required checks passed
    1 - One or more required checks failed
    2 - Error during execution
"""

import argparse
import os
import sys
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.arv.check_impl import run_all_checks
from agents.arv.spec import (
    ArvResult,
    Environment,
    get_category_description,
    get_check_summary,
    get_checks_by_category,
    get_checks_for_env,
)


def print_header(env: Environment):
    """Print the ARV header."""
    print("=" * 70)
    print("ARV – IAM/ADK Department Readiness Verification")
    print("=" * 70)
    print(f"Environment: {env.upper()}")
    print()


def print_results_by_category(results: list[ArvResult]):
    """
    Print results grouped by category.

    Args:
        results: List of ArvResult objects
    """
    # Group results by category
    by_category = defaultdict(list)
    for result in results:
        by_category[result.check.category].append(result)

    # Print each category
    for category in sorted(by_category.keys()):
        category_results = by_category[category]

        print(f"[{category.upper()}] {get_category_description(category)}")

        for result in category_results:
            # Determine status icon
            if result.skipped:
                icon = "⚠️"
                status = "SKIPPED"
            elif result.passed:
                icon = "✅"
                status = "PASSED"
            else:
                icon = "❌"
                status = "FAILED"

            # Print check result
            print(f"  {icon} {result.check.id} – {status}")
            if result.details:
                # Print first line of details
                first_line = result.details.split("\n")[0]
                print(f"     {first_line}")

        print()


def print_summary(results: list[ArvResult]):
    """
    Print summary of ARV results.

    Args:
        results: List of ArvResult objects
    """
    # Calculate statistics
    total = len(results)
    passed = sum(1 for r in results if r.passed and not r.skipped)
    failed = sum(1 for r in results if not r.passed and not r.skipped)
    skipped = sum(1 for r in results if r.skipped)

    # Required checks only
    required_results = [r for r in results if r.check.required or not r.skipped]
    required_total = len(required_results)
    required_passed = sum(1 for r in required_results if r.passed and not r.skipped)
    required_failed = sum(1 for r in required_results if not r.passed and not r.skipped)

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total checks:    {total}")
    print(f"  Passed:        {passed}")
    print(f"  Failed:        {failed}")
    print(f"  Skipped:       {skipped}")
    print()
    print(f"Required checks: {required_total}")
    print(f"  Passed:        {required_passed}")
    print(f"  Failed:        {required_failed}")
    print()

    # Overall result
    if required_failed == 0:
        print("✅ RESULT: PASSED")
        print()
        print(f"All {required_passed} required checks passed.")
        if skipped > 0:
            print(f"{skipped} optional checks were skipped (feature flags disabled).")
    else:
        print("❌ RESULT: FAILED")
        print()
        print(f"{required_failed} required checks failed.")
        print("Fix the failures above before proceeding.")

    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run ARV checks for IAM/ADK department"
    )
    parser.add_argument(
        "--env",
        type=str,
        default=os.getenv("DEPLOYMENT_ENV", "dev"),
        choices=["dev", "staging", "prod"],
        help="Target environment (default: dev or DEPLOYMENT_ENV)",
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=["config", "tests", "rag", "engine", "storage", "notifications"],
        help="Run only checks in this category",
    )
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Include optional checks even if conditions not met",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output from checks",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all checks and exit",
    )

    args = parser.parse_args()

    # List mode
    if args.list:
        summary = get_check_summary()
        print("ARV Checks for IAM/ADK Department")
        print("=" * 70)
        print(f"Total checks: {summary['total_checks']}")
        print(f"Required:     {summary['required_checks']}")
        print(f"Optional:     {summary['optional_checks']}")
        print()
        print("Checks by category:")
        for category, count in summary["checks_by_category"].items():
            if count > 0:
                print(f"  {category}: {count}")
        print()
        print("Run 'python3 scripts/run_arv_department.py' to execute all checks.")
        return 0

    env: Environment = args.env  # type: ignore

    # Get checks to run
    if args.category:
        checks = get_checks_by_category(env, args.category)  # type: ignore
    else:
        checks = get_checks_for_env(env)

    if not checks:
        print(f"No checks found for environment '{env}' and category '{args.category}'")
        return 2

    # Print header
    print_header(env)

    # Run checks
    print(f"Running {len(checks)} checks...\n")
    results = run_all_checks(checks, env, verbose=args.verbose)

    # Print results
    print_results_by_category(results)

    # Print summary
    print_summary(results)

    # Determine exit code
    required_results = [r for r in results if r.check.required or not r.skipped]
    required_failed = sum(1 for r in required_results if not r.passed and not r.skipped)

    if required_failed > 0:
        return 1
    else:
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nERROR: {e!s}", file=sys.stderr)
        sys.exit(2)
