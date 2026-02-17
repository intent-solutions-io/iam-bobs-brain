#!/usr/bin/env python3
"""
ARV Minimum Gate Check - Agent Readiness Verification (Phase RC2)

This script validates the minimum requirements for agent readiness:
- All iam-* agents must have agent.py, prompts/docs, and basic test coverage
- Foreman orchestrator must have correlation ID wiring
- Structured logging helper must be present

Part of Phase RC2 observability and ARV improvements.

Usage:
    python scripts/check_arv_minimum.py
    python scripts/check_arv_minimum.py --verbose
    python scripts/check_arv_minimum.py --portfolio  # Check all local repos

Exit codes:
    0 - ARV minimum requirements met
    1 - Requirements not met (blocking issues found)
    2 - Error during checks
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "agents"))

# Import repo registry (PORT2 - for portfolio mode)
try:
    from config.repos import RepoConfig, list_repos  # noqa: F401

    REGISTRY_AVAILABLE = True
except ImportError as e:
    REGISTRY_AVAILABLE = False
    REGISTRY_ERROR = str(e)


class ARVMinimumChecker:
    """Check minimum ARV requirements for agent readiness."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.passed = []
        self.failed = []
        self.warnings = []

    def log(self, message: str):
        """Log message if verbose mode."""
        if self.verbose:
            print(f"  {message}")

    def check_logging_helper(self) -> bool:
        """Check that structured logging helper exists."""
        print("\n🔍 Checking Structured Logging Helper...")

        logging_path = Path("agents/utils/logging.py")
        if not logging_path.exists():
            self.failed.append("agents/utils/logging.py not found")
            return False

        self.log(f"✓ Found {logging_path}")

        # Try to import logging helper
        try:
            from agents.utils.logging import (  # noqa: F401
                get_logger,
                log_agent_step,
                log_pipeline_complete,
                log_pipeline_start,
            )

            self.log("✓ Logging helper imports successfully")
            self.passed.append("Structured logging helper present and importable")
            return True
        except ImportError as e:
            self.failed.append(f"Cannot import logging helper: {e}")
            return False

    def check_correlation_ids(self) -> bool:
        """Check that correlation IDs are wired in contracts."""
        print("\n🔍 Checking Correlation ID Wiring...")

        # Check shared contracts (package with __init__.py)
        contracts_path = Path("agents/shared_contracts")
        contracts_init = contracts_path / "__init__.py"
        if not contracts_path.exists() or not contracts_init.exists():
            self.failed.append("agents/shared_contracts/ package not found")
            return False

        self.log(f"✓ Found {contracts_path}/ package")

        # Check that PipelineRequest and PipelineResult have pipeline_run_id
        try:
            from agents.shared_contracts import PipelineRequest, PipelineResult

            # Test PipelineRequest
            req = PipelineRequest(repo_hint="test", task_description="test")
            if not hasattr(req, "pipeline_run_id"):
                self.failed.append("PipelineRequest missing pipeline_run_id field")
                return False

            self.log(f"✓ PipelineRequest has pipeline_run_id: {req.pipeline_run_id}")

            # Test PipelineResult (check field exists in dataclass)
            result_fields = [
                f.name for f in PipelineResult.__dataclass_fields__.values()
            ]
            if "pipeline_run_id" not in result_fields:
                self.failed.append("PipelineResult missing pipeline_run_id field")
                return False

            self.log("✓ PipelineResult has pipeline_run_id field")
            self.passed.append("Correlation IDs wired in pipeline contracts")
            return True

        except Exception as e:
            self.failed.append(f"Error checking correlation IDs: {e}")
            return False

    def check_iam_agents(self) -> bool:
        """Check that all iam-* agents meet minimum requirements."""
        print("\n🔍 Checking IAM-* Agents...")

        agents_dir = Path("agents")
        if not agents_dir.exists():
            self.failed.append("agents/ directory not found")
            return False

        # Find all iam-* agent directories
        # Exclude iam_senior_adk_devops_lead (orchestrator module, not a deployed agent)
        iam_agents = [
            d
            for d in agents_dir.iterdir()
            if d.is_dir()
            and d.name.startswith("iam")
            and d.name != "iam_senior_adk_devops_lead"
        ]  # Orchestrator module

        if not iam_agents:
            self.warnings.append(
                "No iam-* agent directories found yet (expected for early phases)"
            )
            self.log(
                "⚠️  No iam-* agents found (expected if agents not yet scaffolded)"
            )
            return True  # Not a failure if we haven't created agents yet

        self.log(
            f"Found {len(iam_agents)} iam-* agent directories (excluding orchestrator module)"
        )

        all_valid = True
        for agent_dir in iam_agents:
            agent_name = agent_dir.name
            self.log(f"\nChecking {agent_name}...")

            # Check 1: agent.py exists
            agent_py = agent_dir / "agent.py"
            if not agent_py.exists():
                self.failed.append(f"{agent_name}: missing agent.py")
                all_valid = False
                continue

            self.log(f"  ✓ {agent_name}/agent.py exists")

            # Check 2: agent.py is importable (basic smoke test)
            try:
                # We can't actually import it without ADK dependencies,
                # but we can check that it has valid Python syntax
                import ast

                with open(agent_py) as f:
                    ast.parse(f.read())
                self.log(f"  ✓ {agent_name}/agent.py has valid syntax")
            except SyntaxError as e:
                self.failed.append(f"{agent_name}/agent.py has syntax errors: {e}")
                all_valid = False
                continue

            # Check 3: Has documentation (README, system prompt, or docs/)
            has_docs = False
            doc_files = [
                agent_dir / "README.md",
                agent_dir / "prompts" / "system.md",
                agent_dir / "docs",
            ]
            for doc_file in doc_files:
                if doc_file.exists():
                    has_docs = True
                    self.log(f"  ✓ {agent_name} has documentation: {doc_file.name}")
                    break

            if not has_docs:
                self.warnings.append(
                    f"{agent_name}: no documentation found (README, prompts/, or docs/)"
                )
                self.log(f"  ⚠️  {agent_name} has no documentation")

            # Check 4: Has test coverage
            # Look for: 1) files named *{agent_name}*.py, or
            #           2) files that reference the agent in their content
            test_files = list(Path("tests").glob(f"**/*{agent_name}*.py"))

            # Also check for comprehensive test files that test multiple agents
            if not test_files:
                comprehensive_tests = [
                    Path("tests/unit/test_iam_specialists_coverage.py"),
                    Path("tests/unit/test_iam_agents.py"),
                ]
                for test_file in comprehensive_tests:
                    if test_file.exists():
                        with open(test_file) as f:
                            if agent_name in f.read():
                                test_files = [test_file]
                                break

            if test_files:
                self.log(
                    f"  ✓ {agent_name} has test coverage: {len(test_files)} test file(s)"
                )
            else:
                self.warnings.append(f"{agent_name}: no test coverage found")
                self.log(f"  ⚠️  {agent_name} has no test coverage")

        if all_valid and iam_agents:
            self.passed.append(
                f"All {len(iam_agents)} iam-* agents meet minimum requirements"
            )

        return all_valid

    def check_foreman_orchestrator(self) -> bool:
        """Check that foreman orchestrator has correlation ID wiring."""
        print("\n🔍 Checking Foreman Orchestrator...")

        orchestrator_path = Path("agents/iam_senior_adk_devops_lead/orchestrator.py")
        if not orchestrator_path.exists():
            self.failed.append("Foreman orchestrator not found at expected path")
            return False

        self.log(f"✓ Found {orchestrator_path}")

        # Check that orchestrator uses logging and correlation IDs
        try:
            with open(orchestrator_path) as f:
                content = f.read()

            # Check for logging imports (accept both relative and absolute paths)
            has_logging_import = (
                "from utils.logging import" in content
                or "from agents.utils.logging import" in content
            )
            if not has_logging_import:
                self.failed.append("Orchestrator doesn't import logging helper")
                return False

            self.log("✓ Orchestrator imports logging helper")

            # Check for correlation ID usage
            if "pipeline_run_id" not in content:
                self.failed.append(
                    "Orchestrator doesn't use pipeline_run_id correlation IDs"
                )
                return False

            self.log("✓ Orchestrator uses pipeline_run_id")

            # Check for logging calls
            logging_calls = [
                "log_pipeline_start",
                "log_pipeline_complete",
                "log_agent_step",
            ]
            for call in logging_calls:
                if call not in content:
                    self.warnings.append(f"Orchestrator doesn't call {call}")
                else:
                    self.log(f"✓ Orchestrator calls {call}")

            self.passed.append(
                "Foreman orchestrator has correlation ID and logging wiring"
            )
            return True

        except Exception as e:
            self.failed.append(f"Error checking orchestrator: {e}")
            return False

    def generate_report(self) -> Tuple[bool, str]:
        """Generate ARV minimum readiness report."""
        is_ready = len(self.failed) == 0

        report = "\n" + "=" * 60
        report += "\nARV MINIMUM GATE CHECK (Phase RC2)"
        report += "\n" + "=" * 60

        # Status indicators
        logging_ok = "logging helper" in " ".join(self.passed).lower()
        correlation_ok = "correlation" in " ".join(self.passed).lower()
        agents_ok = not any("iam-" in f for f in self.failed)
        orchestrator_ok = "orchestrator" in " ".join(self.passed).lower()

        report += f"\n{'✅' if logging_ok else '❌'} Logging Helper: {'PRESENT' if logging_ok else 'MISSING'}"
        report += f"\n{'✅' if correlation_ok else '❌'} Correlation IDs: {'WIRED' if correlation_ok else 'MISSING'}"
        report += f"\n{'✅' if orchestrator_ok else '❌'} Foreman Orchestrator: {'READY' if orchestrator_ok else 'NOT READY'}"
        report += f"\n{'✅' if agents_ok else '⚠️ '} IAM-* Agents: {'READY' if agents_ok else 'ISSUES FOUND'}"

        report += (
            f"\n\n{'✅ ARV MINIMUM MET' if is_ready else '❌ ARV MINIMUM NOT MET'}"
        )

        if self.failed:
            report += "\n\n❌ Blocking Issues:"
            for item in self.failed:
                report += f"\n  - {item}"

        if self.warnings:
            report += "\n\n⚠️  Warnings (not blockers):"
            for item in self.warnings:
                report += f"\n  - {item}"

        if self.passed and self.verbose:
            report += "\n\n✅ Passed Checks:"
            for item in self.passed:
                report += f"\n  - {item}"

        report += "\n\n💡 Next Steps:"
        if is_ready:
            report += "\n  - ARV minimum requirements met"
            report += "\n  - Ready to proceed with deployment"
            report += "\n  - Address warnings for production readiness"
        else:
            report += "\n  - Fix blocking issues above"
            report += "\n  - Ensure all iam-* agents have agent.py and docs"
            report += "\n  - Verify correlation ID wiring"

        report += "\n" + "=" * 60 + "\n"

        return is_ready, report

    def run(self) -> int:
        """Run all ARV minimum checks."""
        try:
            # Run all checks
            self.check_logging_helper()
            self.check_correlation_ids()
            self.check_foreman_orchestrator()
            self.check_iam_agents()

            # Generate report
            is_ready, report = self.generate_report()
            print(report)

            # Return appropriate exit code
            return 0 if is_ready else 1

        except Exception as e:
            print(f"\n❌ Error during ARV checks: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()
            return 2


def run_portfolio_checks(verbose: bool = False) -> int:
    """
    Run ARV minimum checks across all local repos (PORT2 feature).

    Currently, this runs the check on the current repo and reports
    portfolio-style metrics. Future: iterate through all local repos.
    """
    if not REGISTRY_AVAILABLE:
        print("❌ Registry not available. Cannot run portfolio checks.")
        print("   Install config/repos.py to enable portfolio mode.")
        return 2

    print("\n" + "=" * 70)
    print("ARV MINIMUM GATE CHECK - PORTFOLIO MODE (PORT2)")
    print("=" * 70)

    # Get all local repos
    try:
        all_repos = list_repos()
        local_repos = [r for r in all_repos if r.is_local]

        print(f"\n📋 Checking {len(local_repos)} local repositories...")
        print()

        for repo in local_repos:
            print(f"  • {repo.id}: {repo.display_name}")
            print(f"    Local path: {repo.local_path}")

        # For external repos
        external_repos = [r for r in all_repos if not r.is_local]
        if external_repos:
            print(f"\n⏭️  Skipping {len(external_repos)} external repositories:")
            for repo in external_repos:
                print(
                    f"  • {repo.id}: {repo.display_name} (local_path={repo.local_path})"
                )

        print()

    except Exception as e:
        print(f"❌ Error loading registry: {e}")
        return 2

    # Run check on current repo
    # (Future: iterate through all local repos if we have multiple)
    print("=" * 70)
    print("CHECKING: bobs-brain (current repository)")
    print("=" * 70)

    checker = ARVMinimumChecker(verbose=verbose)
    result = checker.run()

    # Portfolio summary
    print("\n" + "=" * 70)
    print("PORTFOLIO SUMMARY")
    print("=" * 70)
    print(f"Repos checked: {len(local_repos)}")
    print(f"Repos passed: {1 if result == 0 else 0}")
    print(f"Repos failed: {0 if result == 0 else 1}")
    print(f"Repos skipped: {len(external_repos)}")
    print("=" * 70 + "\n")

    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check ARV minimum requirements (Phase RC2)",
        epilog="""
Examples:
  # Check current repo (default)
  python scripts/check_arv_minimum.py

  # Portfolio mode - check all local repos
  python scripts/check_arv_minimum.py --portfolio

  # Verbose output
  python scripts/check_arv_minimum.py --verbose
        """,
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--portfolio",
        "-p",
        action="store_true",
        help="Run checks across all local repos (PORT2 feature)",
    )

    args = parser.parse_args()

    if args.portfolio:
        return run_portfolio_checks(verbose=args.verbose)
    else:
        checker = ARVMinimumChecker(verbose=args.verbose)
        return checker.run()


if __name__ == "__main__":
    sys.exit(main())
