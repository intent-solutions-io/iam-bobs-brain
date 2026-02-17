#!/usr/bin/env python3
"""
Smoke test for all agents lazy-loading App pattern (6774).

This script validates that all agents in the department follow the lazy-loading
App pattern and can be imported without full environment setup.

Usage:
    python3 scripts/smoke_check_agents.py
    make smoke-agents
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_agent_lazy_loading(agent_module_path: str) -> dict:
    """
    Test that an agent module follows lazy-loading pattern.

    Args:
        agent_module_path: Module path (e.g., "agents.bob.agent")

    Returns:
        dict: Test results with keys: passed, errors, warnings
    """
    results = {
        "passed": [],
        "errors": [],
        "warnings": []
    }

    print(f"\n🔍 Testing {agent_module_path}...")

    # Test 1: Module can be imported without env vars
    print("  ✓ Test 1: Import without env vars", end="")
    try:
        # Clear critical env vars to test lazy loading
        saved_env = {}
        for key in ["PROJECT_ID", "LOCATION", "AGENT_ENGINE_ID", "AGENT_SPIFFE_ID"]:
            saved_env[key] = os.environ.pop(key, None)

        # Remove from sys.modules if already loaded
        if agent_module_path in sys.modules:
            del sys.modules[agent_module_path]

        # Try import
        import importlib
        module = importlib.import_module(agent_module_path)

        # Restore env
        for key, value in saved_env.items():
            if value:
                os.environ[key] = value

        results["passed"].append("import_without_env")
        print(" ✅")
    except Exception as e:
        results["errors"].append(f"import_without_env: {e}")
        print(f" ❌ {e}")
        return results  # Stop testing if import fails

    # Test 2: Module has create_agent function
    print("  ✓ Test 2: create_agent() exists", end="")
    if hasattr(module, "create_agent"):
        results["passed"].append("has_create_agent")
        print(" ✅")
    else:
        results["errors"].append("Missing create_agent() function")
        print(" ❌")

    # Test 3: Module has create_app function
    print("  ✓ Test 3: create_app() exists", end="")
    if hasattr(module, "create_app"):
        results["passed"].append("has_create_app")
        print(" ✅")
    else:
        results["errors"].append("Missing create_app() function")
        print(" ❌")

    # Test 4: Module has app symbol (not root_agent)
    print("  ✓ Test 4: Module-level 'app' exists", end="")
    if hasattr(module, "app"):
        results["passed"].append("has_app_symbol")
        print(" ✅")
    else:
        results["errors"].append("Missing module-level 'app' symbol")
        print(" ❌")

    # Test 5: Module does NOT have root_agent (old pattern)
    print("  ✓ Test 5: No 'root_agent' symbol (old pattern)", end="")
    if not hasattr(module, "root_agent"):
        results["passed"].append("no_root_agent")
        print(" ✅")
    else:
        results["warnings"].append("Module still has 'root_agent' symbol (old pattern)")
        print(" ⚠️  Warning: root_agent still exists")

    # Test 6: create_runner marked as deprecated
    print("  ✓ Test 6: create_runner() marked DEPRECATED", end="")
    if hasattr(module, "create_runner"):
        docstring = module.create_runner.__doc__ or ""
        if "DEPRECATED" in docstring:
            results["passed"].append("runner_deprecated")
            print(" ✅")
        else:
            results["warnings"].append("create_runner() not marked as DEPRECATED")
            print(" ⚠️  Warning: Not marked DEPRECATED")
    else:
        results["passed"].append("no_create_runner")
        print(" ✅ (no create_runner)")

    return results


def main():
    """Run smoke tests for all agents."""
    print("🧪 Department ADK IAM - Lazy Loading Smoke Test")
    print("=" * 60)

    # List of all agents in the department
    agents = [
        ("bob", "agents.bob.agent"),
        ("iam-senior-adk-devops-lead", "agents.iam_senior_adk_devops_lead.agent"),
        ("iam-adk", "agents.iam_adk.agent"),
        ("iam-issue", "agents.iam_issue.agent"),
        ("iam-fix-plan", "agents.iam_fix_plan.agent"),
        ("iam-fix-impl", "agents.iam_fix_impl.agent"),
        ("iam-qa", "agents.iam_qa.agent"),
        ("iam-doc", "agents.iam_doc.agent"),
        ("iam-cleanup", "agents.iam_cleanup.agent"),
        ("iam-index", "agents.iam_index.agent"),
    ]

    all_results = {}
    total_passed = 0
    total_errors = 0
    total_warnings = 0

    # Test each agent
    for agent_name, module_path in agents:
        results = test_agent_lazy_loading(module_path)
        all_results[agent_name] = results
        total_passed += len(results["passed"])
        total_errors += len(results["errors"])
        total_warnings += len(results["warnings"])

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    for agent_name, results in all_results.items():
        passed = len(results["passed"])
        errors = len(results["errors"])
        warnings = len(results["warnings"])

        status = "✅ PASS" if errors == 0 else "❌ FAIL"
        print(f"{status} {agent_name:<30} ({passed} passed, {errors} errors, {warnings} warnings)")

        # Show errors
        for error in results["errors"]:
            print(f"     ❌ {error}")

    print("\n" + "=" * 60)
    print(f"Total: {total_passed} passed, {total_errors} errors, {total_warnings} warnings")

    if total_errors == 0:
        print("\n✅ All agents follow lazy-loading App pattern (6774)")
        return 0
    else:
        print(f"\n❌ {total_errors} errors found - agents not fully migrated")
        return 1


if __name__ == "__main__":
    sys.exit(main())
