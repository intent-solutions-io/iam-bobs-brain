#!/usr/bin/env python3
"""
Configuration Validator for Bob's Brain

Validates all environment variables against the config inventory.
Used for:
- Local development (make check-config)
- CI/CD pipelines (pre-deploy checks)
- ARV (Agent Readiness Verification)

Exit Codes:
- 0: Configuration is valid for the current environment
- 1: Configuration has errors (missing required vars, invalid values)
"""

import os
import sys
from typing import Dict, Tuple

# Add parent directory to path so we can import agents.config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.config.inventory import (
    Environment,
    EnvVarSpec,
    get_all_vars,
)


def get_current_env() -> Environment:
    """Get current environment from DEPLOYMENT_ENV."""
    env_str = os.getenv("DEPLOYMENT_ENV", "dev").lower()

    if env_str in ("dev", "development"):
        return "dev"
    elif env_str in ("staging", "stage"):
        return "staging"
    elif env_str in ("prod", "production"):
        return "prod"
    else:
        # Default to dev for safety
        return "dev"


def is_boolean_like(value: str) -> bool:
    """Check if value is a valid boolean-like string."""
    return value.lower() in ("true", "false", "1", "0", "yes", "no", "on", "off")


def is_var_set(var: EnvVarSpec) -> Tuple[bool, str]:
    """
    Check if variable is set in environment.

    Returns:
        (is_set, value) tuple
    """
    value = os.getenv(var.name)
    if value is None or value == "":
        return False, ""
    return True, value


def is_feature_flag_enabled(flag_name: str) -> bool:
    """Check if a feature flag is enabled."""
    value = os.getenv(flag_name, "false").lower()
    return value in ("true", "1", "yes", "on")


def check_conditional_requirement(var: EnvVarSpec) -> Tuple[bool, str]:
    """
    Check if a conditional requirement is met.

    Returns:
        (is_required, reason) tuple
    """
    if not var.required_when:
        return False, ""

    # Simple parsing of required_when conditions
    # Format: "FLAG_NAME=true" or "FLAG_NAME=true or FLAG2=true"
    condition = var.required_when

    # Check for common patterns
    if "LIVE_RAG_BOB_ENABLED=true" in condition and is_feature_flag_enabled(
        "LIVE_RAG_BOB_ENABLED"
    ):
        return True, "LIVE_RAG_BOB_ENABLED is enabled"

    if "LIVE_RAG_FOREMAN_ENABLED=true" in condition and is_feature_flag_enabled(
        "LIVE_RAG_FOREMAN_ENABLED"
    ):
        return True, "LIVE_RAG_FOREMAN_ENABLED is enabled"

    if "LIVE_RAG_*_ENABLED=true" in condition and (
        is_feature_flag_enabled("LIVE_RAG_BOB_ENABLED")
        or is_feature_flag_enabled("LIVE_RAG_FOREMAN_ENABLED")
    ):
        return True, "RAG is enabled for at least one agent"

    if "SLACK_NOTIFICATIONS_ENABLED=true" in condition and is_feature_flag_enabled(
        "SLACK_NOTIFICATIONS_ENABLED"
    ):
        return True, "SLACK_NOTIFICATIONS_ENABLED is enabled"

    if "GITHUB_ISSUE_CREATION_ENABLED=true" in condition and is_feature_flag_enabled(
        "GITHUB_ISSUE_CREATION_ENABLED"
    ):
        return True, "GITHUB_ISSUE_CREATION_ENABLED is enabled"

    if "ORG_STORAGE_WRITE_ENABLED=true" in condition and is_feature_flag_enabled(
        "ORG_STORAGE_WRITE_ENABLED"
    ):
        return True, "ORG_STORAGE_WRITE_ENABLED is enabled"

    if "ENGINE_MODE_* flags enabled" in condition:
        engine_flags = [
            "ENGINE_MODE_FOREMAN_TO_IAM_ADK",
            "ENGINE_MODE_FOREMAN_TO_IAM_ISSUE",
            "ENGINE_MODE_FOREMAN_TO_IAM_FIX",
        ]
        if any(is_feature_flag_enabled(flag) for flag in engine_flags):
            return True, "At least one ENGINE_MODE flag is enabled"

    # Agent Engine per-agent conditions (AE1)
    if "ENGINE_MODE enabled for Bob" in condition:
        # Bob Agent Engine is implicitly enabled if any ENGINE_MODE is on
        engine_flags = [
            "ENGINE_MODE_FOREMAN_TO_IAM_ADK",
            "ENGINE_MODE_FOREMAN_TO_IAM_ISSUE",
            "ENGINE_MODE_FOREMAN_TO_IAM_FIX",
        ]
        if any(is_feature_flag_enabled(flag) for flag in engine_flags):
            return True, "ENGINE_MODE flags indicate Agent Engine is used"

    if "ENGINE_MODE enabled for foreman" in condition:
        # Foreman Engine is enabled if routing to IAM agents via Engine
        engine_flags = [
            "ENGINE_MODE_FOREMAN_TO_IAM_ADK",
            "ENGINE_MODE_FOREMAN_TO_IAM_ISSUE",
            "ENGINE_MODE_FOREMAN_TO_IAM_FIX",
        ]
        if any(is_feature_flag_enabled(flag) for flag in engine_flags):
            return True, "ENGINE_MODE flags indicate foreman uses Agent Engine"

    if "ENGINE_MODE_FOREMAN_TO_IAM_ADK=true" in condition:
        if is_feature_flag_enabled("ENGINE_MODE_FOREMAN_TO_IAM_ADK"):
            return True, "ENGINE_MODE_FOREMAN_TO_IAM_ADK is enabled"

    if "ENGINE_MODE_FOREMAN_TO_IAM_ISSUE=true" in condition:
        if is_feature_flag_enabled("ENGINE_MODE_FOREMAN_TO_IAM_ISSUE"):
            return True, "ENGINE_MODE_FOREMAN_TO_IAM_ISSUE is enabled"

    if "ENGINE_MODE_FOREMAN_TO_IAM_FIX=true" in condition:
        if is_feature_flag_enabled("ENGINE_MODE_FOREMAN_TO_IAM_FIX"):
            return True, "ENGINE_MODE_FOREMAN_TO_IAM_FIX is enabled"

    if "iam-qa deployed to Agent Engine" in condition:
        # For now, iam-qa Engine deployment is optional/future
        # Don't require the ID unless explicitly planning to use it
        return False, ""

    # Not required by condition
    return False, ""


def validate_config(env: Environment) -> Dict:
    """
    Validate configuration for the given environment.

    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "env": str,
            "required_ok": List[EnvVarSpec],
            "required_missing": List[EnvVarSpec],
            "optional_set": List[EnvVarSpec],
            "optional_unset": List[EnvVarSpec],
            "invalid_values": List[Tuple[EnvVarSpec, str, str]],  # (var, value, reason)
            "deprecated_set": List[EnvVarSpec],
        }
    """
    all_vars = get_all_vars()

    required_ok = []
    required_missing = []
    optional_set = []
    optional_unset = []
    invalid_values = []
    deprecated_set = []

    for var in all_vars:
        is_set, value = is_var_set(var)

        # Check if deprecated
        if var.deprecated and is_set:
            deprecated_set.append(var)

        # Determine if required for this env
        if var.is_required_for_env(env):
            if is_set:
                required_ok.append(var)
            else:
                required_missing.append(var)
        elif var.is_optional_for_env(env):
            # Check conditional requirements
            is_conditionally_required, reason = check_conditional_requirement(var)

            if is_conditionally_required:
                if is_set:
                    required_ok.append(var)
                else:
                    required_missing.append(var)
            else:
                if is_set:
                    optional_set.append(var)
                else:
                    optional_unset.append(var)

        # Validate boolean-like vars
        if is_set and var.category == "features":
            # Feature flags should be boolean-like
            if not is_boolean_like(value) and not value.isdigit():
                invalid_values.append(
                    (var, value, "Feature flag should be true/false or 0-100")
                )

    return {
        "valid": len(required_missing) == 0 and len(invalid_values) == 0,
        "env": env,
        "required_ok": required_ok,
        "required_missing": required_missing,
        "optional_set": optional_set,
        "optional_unset": optional_unset,
        "invalid_values": invalid_values,
        "deprecated_set": deprecated_set,
    }


def print_validation_results(results: Dict) -> None:
    """Print validation results in a human-readable format."""
    env = results["env"]

    print("=" * 70)
    print(f"Configuration Validation for Environment: {env.upper()}")
    print("=" * 70)
    print()

    # Required variables (OK)
    if results["required_ok"]:
        print(f"✅ REQUIRED VARIABLES ({len(results['required_ok'])} OK):")
        for var in results["required_ok"]:
            is_set, value = is_var_set(var)
            # Mask sensitive values
            if "TOKEN" in var.name or "SECRET" in var.name or "KEY" in var.name:
                display_value = value[:10] + "..." if len(value) > 10 else value
            else:
                display_value = value
            print(f"   ✓ {var.name} = {display_value}")
        print()

    # Required variables (MISSING)
    if results["required_missing"]:
        print(f"❌ REQUIRED VARIABLES MISSING ({len(results['required_missing'])}):")
        for var in results["required_missing"]:
            print(f"   ✗ {var.name}")
            print(f"      {var.description}")
            if var.required_when:
                print(f"      Required when: {var.required_when}")
            if var.default:
                print(f"      Default: {var.default}")
        print()

    # Invalid values
    if results["invalid_values"]:
        print(f"⚠️  INVALID VALUES ({len(results['invalid_values'])}):")
        for var, value, reason in results["invalid_values"]:
            print(f"   ! {var.name} = {value}")
            print(f"      Issue: {reason}")
        print()

    # Deprecated variables
    if results["deprecated_set"]:
        print(f"⚠️  DEPRECATED VARIABLES ({len(results['deprecated_set'])}):")
        for var in results["deprecated_set"]:
            print(f"   ! {var.name}")
            if var.canonical_replacement:
                print(f"      Use instead: {var.canonical_replacement}")
        print()

    # Optional variables (SET)
    if results["optional_set"]:
        print(f"ℹ️  OPTIONAL VARIABLES SET ({len(results['optional_set'])}):")
        for var in results["optional_set"][:5]:  # Show first 5
            print(f"   • {var.name}")
        if len(results["optional_set"]) > 5:
            print(f"   ... and {len(results['optional_set']) - 5} more")
        print()

    # Optional variables (UNSET)
    if results["optional_unset"]:
        print(
            f"💤 OPTIONAL VARIABLES UNSET ({len(results['optional_unset'])}) - OK if not needed"
        )
        print()

    # Summary
    print("=" * 70)
    print("SUMMARY:")
    print("=" * 70)
    total_required = len(results["required_ok"]) + len(results["required_missing"])
    print(f"Required variables: {len(results['required_ok'])}/{total_required} OK")
    print(f"Optional set: {len(results['optional_set'])}")
    print(f"Optional unset: {len(results['optional_unset'])}")

    if results["deprecated_set"]:
        print(f"⚠️  Deprecated: {len(results['deprecated_set'])}")
    if results["invalid_values"]:
        print(f"❌ Invalid: {len(results['invalid_values'])}")

    print()

    if results["valid"]:
        print("✅ Configuration is VALID for", env.upper())
        print()
        print("All required variables are set and valid.")
        print("You can proceed with deployment or testing.")
    else:
        print("❌ Configuration is INVALID for", env.upper())
        print()
        print("Fix the issues above before proceeding.")
        print()
        print("Tips:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in required values")
        print("  3. Run this script again")

    print("=" * 70)


def main():
    """Main entry point."""
    env = get_current_env()

    results = validate_config(env)

    print_validation_results(results)

    # Exit with appropriate code
    if results["valid"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
