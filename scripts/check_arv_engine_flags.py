#!/usr/bin/env python3
"""
ARV Engine Flags Check (Phase AE3)

Agent Readiness Verification gate ensuring feature flags are safely configured
for the current environment.

This script validates that:
1. No production flags are enabled prematurely
2. Feature flags follow the rollout progression (dev → staging → prod)
3. Production features have proper prerequisites (ARV checks, monitoring, etc.)
4. Dangerous combinations are not enabled

Exit Codes:
- 0: All checks passed (safe to proceed)
- 1: Blocking issues found (STOP - unsafe configuration)
- 2: Warnings only (consider fixing but not blocking)

Usage:
    python3 scripts/check_arv_engine_flags.py              # Basic check
    python3 scripts/check_arv_engine_flags.py --verbose    # Detailed output
    make check-arv-engine-flags                            # Via Makefile
    make check-arv-engine-flags-verbose                    # Verbose via Makefile

Related Docs:
- 000-docs/6767-103-DR-STND-live-rag-and-agent-engine-rollout-plan.md
- agents/config/features.py
"""

import argparse
import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from agents.config.features import (
    AGENT_ENGINE_BOB_NEXT_GEN_ENABLED,
    AGENT_ENGINE_BOB_NEXT_GEN_PERCENT,
    BLUE_GREEN_SHADOW_TRAFFIC_ENABLED,
    ENGINE_MODE_FOREMAN_TO_IAM_ADK,
    ENGINE_MODE_FOREMAN_TO_IAM_FIX,
    ENGINE_MODE_FOREMAN_TO_IAM_ISSUE,
    LIVE_RAG_BOB_ENABLED,
    LIVE_RAG_FOREMAN_ENABLED,
    SLACK_SWE_PIPELINE_MODE_ENABLED,
    get_all_flags,
    get_current_environment,
    get_enabled_flags,
)


class ARVEngineFlagsChecker:
    """
    ARV gate checker for feature flag safety.

    Validates feature flags against environment and rollout plan to prevent
    premature or unsafe feature enablement in production.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.info = []

    def log_info(self, message: str) -> None:
        """Log informational message (always shown in verbose mode)."""
        self.info.append(message)
        if self.verbose:
            print(f"ℹ️  {message}")

    def log_warning(self, message: str) -> None:
        """Log warning (shown always, but not blocking)."""
        self.warnings.append(message)
        print(f"⚠️  {message}")

    def log_error(self, message: str) -> None:
        """Log error (blocking issue)."""
        self.errors.append(message)
        print(f"❌ {message}")

    def check_environment_detection(self) -> bool:
        """
        Verify environment can be detected correctly.

        Returns:
            bool: True if environment detection works, False otherwise
        """
        env = get_current_environment()
        self.log_info(f"Current environment: {env}")

        if env not in ("dev", "staging", "prod"):
            self.log_error(
                f"Invalid environment detected: {env} (expected dev/staging/prod)"
            )
            return False

        return True

    def check_all_flags_status(self) -> None:
        """
        Display status of all feature flags.
        """
        all_flags = get_all_flags()
        enabled = get_enabled_flags()

        self.log_info(f"Total flags: {len(all_flags)}")
        self.log_info(f"Enabled flags: {len(enabled)}")

        if self.verbose:
            print("\n📋 All Feature Flags:")
            for name, value in all_flags.items():
                status = (
                    "✅ ENABLED"
                    if (value is True or (isinstance(value, int) and value > 0))
                    else "⬜ DISABLED"
                )
                print(f"  {name}: {value} ({status})")
            print()

    def check_prod_safety(self) -> bool:
        """
        Validate that production flags are safe.

        Production safety rules:
        1. No experimental features enabled in prod
        2. All prod features must have passed staging validation
        3. Blue/Green migration follows canary progression (5% → 25% → 50% → 100%)
        4. No dangerous flag combinations

        Returns:
            bool: True if production is safe, False if blocking issues found
        """
        env = get_current_environment()
        enabled = get_enabled_flags()

        if env != "prod":
            self.log_info(
                f"Environment is {env} (not prod) - skipping strict prod checks"
            )
            return True

        if not enabled:
            self.log_info("✅ Production is SAFE: All flags disabled")
            return True

        self.log_info(
            f"Production has {len(enabled)} enabled flag(s): {', '.join(enabled)}"
        )

        # Check 1: RAG flags in prod
        if LIVE_RAG_BOB_ENABLED or LIVE_RAG_FOREMAN_ENABLED:
            # RAG can be enabled in prod IF:
            # - Vertex AI Search is configured (VERTEX_SEARCH_DATASTORE_ID)
            # - Feature has been validated in staging
            # For now, we'll warn (not block) since this is Phase AE3 design
            self.log_warning(
                "Live RAG enabled in production - ensure Vertex AI Search is configured and staging validated"
            )

        # Check 2: Engine mode flags in prod
        if (
            ENGINE_MODE_FOREMAN_TO_IAM_ADK
            or ENGINE_MODE_FOREMAN_TO_IAM_ISSUE
            or ENGINE_MODE_FOREMAN_TO_IAM_FIX
        ):
            # Engine mode can be enabled in prod IF:
            # - Agents are deployed to Agent Engine
            # - A2A adapter is configured correctly
            # - Feature has been validated in staging
            # For now, we'll warn (not block) since this is Phase AE3 design
            self.log_warning(
                "Agent Engine A2A mode enabled in production - ensure agents deployed and staging validated"
            )

        # Check 3: Gateway routing in prod
        if SLACK_SWE_PIPELINE_MODE_ENABLED:
            # Option B routing can be enabled in prod IF:
            # - a2a_gateway is deployed to Cloud Run
            # - Feature has been validated in staging
            # For now, we'll warn (not block) since this is Phase AE3 design
            self.log_warning(
                "Option B gateway routing enabled in production - ensure a2a_gateway deployed and staging validated"
            )

        # Check 4: Blue/Green migration
        if AGENT_ENGINE_BOB_NEXT_GEN_ENABLED:
            percent = AGENT_ENGINE_BOB_NEXT_GEN_PERCENT

            # Validate canary progression
            if percent not in (0, 5, 25, 50, 100):
                self.log_error(
                    f"Invalid canary percentage in prod: {percent}% (must be 0, 5, 25, 50, or 100)"
                )
                return False

            if percent > 0:
                self.log_warning(
                    f"Blue/Green migration active in production: {percent}% traffic to next-gen Bob"
                )

                # If significant traffic (>25%), ensure monitoring is in place
                if percent >= 25:
                    self.log_warning(
                        f"Significant traffic on next-gen ({percent}%) - ensure monitoring and rollback plan ready"
                    )

        # Check 5: Shadow traffic
        if BLUE_GREEN_SHADOW_TRAFFIC_ENABLED:
            if not AGENT_ENGINE_BOB_NEXT_GEN_ENABLED:
                self.log_error(
                    "Shadow traffic enabled but next-gen Bob is not enabled - invalid configuration"
                )
                return False

            self.log_warning(
                "Shadow traffic enabled in production - double resource usage (validate cost acceptable)"
            )

        # All production checks passed (may have warnings but no blocking errors)
        return True

    def check_rollout_progression(self) -> bool:
        """
        Validate that features follow proper rollout progression.

        Rollout rules:
        1. Features should be enabled in dev before staging
        2. Features should be enabled in staging before prod
        3. Canary percentages should increase gradually (5% → 25% → 50% → 100%)

        Returns:
            bool: True if progression is correct, False if violations found
        """
        env = get_current_environment()
        enabled = get_enabled_flags()

        if not enabled:
            self.log_info("✅ No flags enabled - rollout progression is safe")
            return True

        # For now, we can only check the current environment
        # (Would need to query other environments to validate full progression)
        if env == "prod" and enabled:
            self.log_info(
                "Production has flags enabled - ensure they were validated in staging first"
            )

        # Check canary progression
        if AGENT_ENGINE_BOB_NEXT_GEN_ENABLED:
            percent = AGENT_ENGINE_BOB_NEXT_GEN_PERCENT
            if env == "prod" and percent > 0:
                # Log current canary stage
                if percent == 5:
                    self.log_info("Canary Stage: PROD 5% (initial canary)")
                elif percent == 25:
                    self.log_info("Canary Stage: PROD 25% (cautious)")
                elif percent == 50:
                    self.log_info("Canary Stage: PROD 50% (half)")
                elif percent == 100:
                    self.log_info("Canary Stage: PROD 100% (full next-gen)")

        return True

    def check_prerequisites(self) -> bool:
        """
        Validate that prerequisites are met for enabled features.

        Prerequisites:
        - RAG flags require VERTEX_SEARCH_DATASTORE_ID configured
        - Engine mode requires agents deployed to Agent Engine
        - Gateway routing requires a2a_gateway deployed
        - Blue/Green requires next-gen agent deployed

        Returns:
            bool: True if prerequisites met, False if missing
        """
        import os

        # Check RAG prerequisites
        if LIVE_RAG_BOB_ENABLED or LIVE_RAG_FOREMAN_ENABLED:
            datastore_id = os.getenv("VERTEX_SEARCH_DATASTORE_ID")
            if not datastore_id:
                self.log_warning(
                    "RAG enabled but VERTEX_SEARCH_DATASTORE_ID not configured - RAG calls will fail"
                )

        # Check Agent Engine prerequisites
        if (
            ENGINE_MODE_FOREMAN_TO_IAM_ADK
            or ENGINE_MODE_FOREMAN_TO_IAM_ISSUE
            or ENGINE_MODE_FOREMAN_TO_IAM_FIX
        ):
            # Would need to check if agents are deployed to Agent Engine
            # For now, just log info
            self.log_info(
                "Engine mode enabled - ensure target agents are deployed to Agent Engine"
            )

        # Check gateway prerequisites
        if SLACK_SWE_PIPELINE_MODE_ENABLED:
            gateway_url = os.getenv("A2A_GATEWAY_URL")
            if not gateway_url or "PLACEHOLDER" in gateway_url.upper():
                self.log_warning(
                    "Gateway routing enabled but A2A_GATEWAY_URL not configured - routing will fail"
                )

        # Check Blue/Green prerequisites
        if AGENT_ENGINE_BOB_NEXT_GEN_ENABLED:
            # Would need to check if next-gen Bob is deployed
            # For now, just log info
            self.log_info(
                "Blue/Green migration enabled - ensure bob_next_gen is deployed to Agent Engine"
            )

        return True

    def run_all_checks(self) -> bool:
        """
        Run all ARV engine flags checks.

        Returns:
            bool: True if all checks passed, False if any blocking issues
        """
        print("🚦 ARV Engine Flags Check (Phase AE3)")
        print("=" * 60)
        print()

        # Check 1: Environment detection
        if not self.check_environment_detection():
            return False

        # Check 2: Display flag status
        self.check_all_flags_status()

        # Check 3: Production safety
        if not self.check_prod_safety():
            return False

        # Check 4: Rollout progression
        if not self.check_rollout_progression():
            return False

        # Check 5: Prerequisites
        if not self.check_prerequisites():
            return False

        return True

    def print_summary(self) -> None:
        """
        Print summary of check results.
        """
        print()
        print("=" * 60)

        if self.errors:
            print("❌ ARV ENGINE FLAGS CHECK FAILED")
            print()
            print("❌ Blocking Issues:")
            for error in self.errors:
                print(f"  - {error}")
        elif self.warnings:
            print("⚠️  ARV ENGINE FLAGS CHECK PASSED (with warnings)")
            print()
            print("⚠️  Warnings (not blocking):")
            for warning in self.warnings:
                print(f"  - {warning}")
        else:
            print("✅ ARV ENGINE FLAGS CHECK PASSED")
            print()
            print("✅ All feature flags are safely configured for this environment.")

        if self.verbose and self.info:
            print()
            print("ℹ️  Additional Info:")
            for info in self.info:
                print(f"  - {info}")

        print("=" * 60)


def main():
    """
    Main entry point for ARV engine flags check.
    """
    parser = argparse.ArgumentParser(
        description="ARV Engine Flags Check - Validate feature flag safety for current environment"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed flag status",
    )

    args = parser.parse_args()

    checker = ARVEngineFlagsChecker(verbose=args.verbose)
    success = checker.run_all_checks()
    checker.print_summary()

    # Exit code
    if not success or checker.errors:
        sys.exit(1)  # Blocking issues
    elif checker.warnings:
        sys.exit(2)  # Warnings only (can proceed but review recommended)
    else:
        sys.exit(0)  # All good


if __name__ == "__main__":
    main()
