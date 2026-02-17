#!/usr/bin/env python3
"""
Check RAG Readiness - ARV gate for Vertex AI Search integration

This script validates that Bob and foreman are structurally ready for RAG
using the centralized config module without making any API calls.

Part of Agent Readiness Verification (ARV) for Phase RC1.

Usage:
    python scripts/check_rag_readiness.py
    python scripts/check_rag_readiness.py --verbose

Exit codes:
    0 - RAG ready
    1 - Not ready (missing requirements)
    2 - Error during checks
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Tuple

# Add repo root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class RAGReadinessChecker:
    """Check RAG readiness using centralized config module."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.passed = []
        self.failed = []
        self.warnings = []

    def log(self, message: str):
        """Log message if verbose mode."""
        if self.verbose:
            print(f"  {message}")

    def check_configuration_module(self) -> bool:
        """Check RAG configuration module."""
        print("\n🔍 Checking RAG Configuration Module...")

        # Check config module exists
        config_path = Path("agents/config/rag.py")
        if not config_path.exists():
            self.failed.append("agents/config/rag.py not found")
            return False
        self.log(f"✓ Found {config_path}")

        # Try to import config module
        try:
            from agents.config.rag import (
                VertexSearchConfig,  # noqa: F401
                get_bob_vertex_search_config,  # noqa: F401
                get_current_env,
                get_foreman_vertex_search_config,  # noqa: F401
                get_vertex_search_config,  # noqa: F401
                validate_rag_config,
            )
            self.log("✓ Imported RAG config functions")
        except ImportError as e:
            self.failed.append(f"Cannot import RAG config: {e}")
            return False

        # Test environment detection
        try:
            env = get_current_env()
            self.log(f"✓ Current environment: {env}")

            if env not in ["dev", "staging", "prod"]:
                self.failed.append(f"Invalid environment: {env}")
                return False

        except Exception as e:
            self.failed.append(f"Error detecting environment: {e}")
            return False

        # Validate configuration for current environment
        try:
            validation = validate_rag_config(env)

            if validation["valid"]:
                self.log("✓ RAG configuration is valid")
                config = validation["config"]
                self.log(f"  Project: {config.project_id}")
                self.log(f"  Location: {config.location}")
                self.log(f"  Datastore: {config.datastore_id}")

                # Check for placeholders
                if config.is_placeholder():
                    self.warnings.append(
                        "Configuration contains placeholder values. "
                        "Update with real datastore IDs."
                    )
            else:
                # Config invalid - not a blocker if vars just aren't set yet
                self.warnings.append(
                    "RAG configuration not yet populated. "
                    "This is expected if Vertex Search datastores aren't created yet."
                )
                for error in validation["errors"]:
                    self.log(f"  Info: {error}")

            # Even with warnings, consider this check passed if module is importable
            self.passed.append("RAG configuration module structure valid")
            return True

        except Exception as e:
            self.failed.append(f"Error validating RAG config: {e}")
            return False

    def check_tool_factory(self) -> bool:
        """Check Vertex Search tool factory."""
        print("\n🔍 Checking Vertex Search Tool Factory...")

        # Check tool factory exists
        tool_path = Path("agents/tools/vertex_search.py")
        if not tool_path.exists():
            self.failed.append("agents/tools/vertex_search.py not found")
            return False
        self.log(f"✓ Found {tool_path}")

        # Try to import tool factory
        try:
            from agents.tools.vertex_search import (
                VertexSearchToolStub,  # noqa: F401
                get_bob_vertex_search_tool,
                get_foreman_vertex_search_tool,
                get_vertex_search_tool_for_env,  # noqa: F401
            )
            self.log("✓ Imported tool factory functions")
        except ImportError as e:
            self.failed.append(f"Cannot import tool factory: {e}")
            return False

        # Try to create tools (will fail if config not set, but that's ok)
        try:
            bob_tool = get_bob_vertex_search_tool()
            self.log(f"✓ Bob's tool created: {bob_tool}")

            foreman_tool = get_foreman_vertex_search_tool()
            self.log(f"✓ Foreman's tool created: {foreman_tool}")

            # Test that tools have expected methods
            if not hasattr(bob_tool, 'search'):
                self.failed.append("Bob's tool missing 'search' method")
            if not hasattr(foreman_tool, 'search'):
                self.failed.append("Foreman's tool missing 'search' method")

            self.passed.append("Tool factory working correctly")
            return True

        except ValueError as e:
            # Expected if config vars not set
            self.warnings.append(
                f"Tools cannot be created yet: {e}. "
                "Set VERTEX_SEARCH_PROJECT_ID and datastore IDs to test fully."
            )
            # Still pass - factory code is valid
            self.passed.append("Tool factory code structure valid")
            return True
        except Exception as e:
            self.failed.append(f"Unexpected error creating tools: {e}")
            return False

    def check_environment_variables(self) -> bool:
        """Check environment variable configuration."""
        print("\n🔍 Checking Environment Variables...")

        required_vars = {
            "VERTEX_SEARCH_PROJECT_ID": "GCP project ID",
            "VERTEX_SEARCH_DATASTORE_ID_DEV": "Dev datastore ID",
            "VERTEX_SEARCH_DATASTORE_ID_STAGING": "Staging datastore ID",
            "VERTEX_SEARCH_DATASTORE_ID_PROD": "Production datastore ID",
        }

        optional_vars = {
            "VERTEX_SEARCH_LOCATION": "GCP region (defaults to 'global')",
            "DEPLOYMENT_ENV": "Environment override (defaults to 'dev')",
        }

        all_set = True
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                # Mask actual values for security
                if "ID" in var and len(value) > 10:
                    masked = f"{value[:4]}...{value[-4:]}"
                else:
                    masked = value
                self.log(f"✓ {var}={masked} ({description})")
            else:
                self.warnings.append(f"{var} not set ({description})")
                all_set = False

        for var, description in optional_vars.items():
            value = os.getenv(var)
            if value:
                self.log(f"✓ {var}={value} ({description})")

        if all_set:
            self.passed.append("All required environment variables set")
        else:
            self.warnings.append(
                "Some environment variables not set. "
                "This is expected for local dev or CI without real datastores."
            )

        # Don't fail - just warn
        return True

    def check_documentation(self) -> bool:
        """Check documentation requirements."""
        print("\n🔍 Checking Documentation...")

        docs_path = Path("000-docs")
        if not docs_path.exists():
            self.failed.append("000-docs directory not found")
            return False

        # Check for RAG-related docs
        rag_docs = list(docs_path.glob("*rag*.md")) + \
                  list(docs_path.glob("*knowledge*.md"))

        if rag_docs:
            self.log(f"✓ Found {len(rag_docs)} RAG-related docs:")
            for doc in rag_docs:
                self.log(f"  - {doc.name}")
            self.passed.append("RAG documentation present")
        else:
            self.warnings.append("No RAG documentation found (expected in 000-docs/)")

        return True

    def check_config_template(self) -> bool:
        """Check .env.example has RAG configuration."""
        print("\n🔍 Checking Configuration Template...")

        env_example = Path(".env.example")
        if not env_example.exists():
            self.failed.append(".env.example not found")
            return False

        try:
            content = env_example.read_text()

            # Check for RAG config section
            if "VERTEX_SEARCH" in content:
                self.log("✓ RAG configuration documented in .env.example")

                # Check for environment-specific datastores
                if "DATASTORE_ID_DEV" in content and \
                   "DATASTORE_ID_STAGING" in content and \
                   "DATASTORE_ID_PROD" in content:
                    self.log("✓ Environment-specific datastore IDs documented")
                    self.passed.append("Configuration template complete")
                else:
                    self.warnings.append(
                        "Environment-specific datastore IDs not in .env.example"
                    )
            else:
                self.warnings.append("RAG configuration not documented in .env.example")

        except Exception as e:
            self.failed.append(f"Error reading .env.example: {e}")
            return False

        return True

    def generate_report(self) -> Tuple[bool, str]:
        """Generate readiness report."""
        # Consider ready if no hard failures (warnings are ok)
        is_ready = len(self.failed) == 0

        report = "\n" + "=" * 60
        report += "\nRAG READINESS CHECK (Phase RC1)"
        report += "\n" + "=" * 60

        # Status indicators
        config_ok = all("config" not in f.lower() or "module" not in f.lower()
                       for f in self.failed)
        tools_ok = all("tool" not in f.lower() and "factory" not in f.lower()
                      for f in self.failed)
        docs_ok = all("doc" not in f.lower() for f in self.failed)
        template_ok = all("template" not in f.lower() and ".env" not in f.lower()
                         for f in self.failed)

        report += f"\n{'✅' if config_ok else '❌'} Configuration Module: {'VALID' if config_ok else 'INVALID'}"
        report += f"\n{'✅' if tools_ok else '❌'} Tool Factory: {'WORKING' if tools_ok else 'BROKEN'}"
        report += f"\n{'✅' if docs_ok else '❌'} Documentation: {'PRESENT' if docs_ok else 'MISSING'}"
        report += f"\n{'✅' if template_ok else '❌'} Config Template: {'COMPLETE' if template_ok else 'INCOMPLETE'}"

        report += f"\n\n{'✅ RAG READY' if is_ready else '❌ NOT READY'}"

        if self.failed:
            report += "\n\n❌ Failed Checks:"
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
            report += "\n  - RAG structure is ready"
            report += "\n  - Set environment variables to connect to real datastores"
            report += "\n  - Replace VertexSearchToolStub with real ADK tool"
        else:
            report += "\n  - Fix failed checks above"
            report += "\n  - Ensure agents/config/rag.py is importable"
            report += "\n  - Ensure agents/tools/vertex_search.py exists"

        report += "\n" + "=" * 60 + "\n"

        return is_ready, report

    def run(self) -> int:
        """Run all readiness checks."""
        try:
            # Run all checks
            self.check_configuration_module()
            self.check_tool_factory()
            self.check_environment_variables()
            self.check_documentation()
            self.check_config_template()

            # Generate report
            is_ready, report = self.generate_report()
            print(report)

            # Return appropriate exit code
            return 0 if is_ready else 1

        except Exception as e:
            print(f"\n❌ Error during checks: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 2


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check RAG readiness for Bob and foreman (Phase RC1)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )

    args = parser.parse_args()

    checker = RAGReadinessChecker(verbose=args.verbose)
    return checker.run()


if __name__ == "__main__":
    sys.exit(main())
