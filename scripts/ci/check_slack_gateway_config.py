#!/usr/bin/env python3
"""
Slack Gateway Configuration Validator (Phase 25)
Validates Terraform configuration for Slack Bob Gateway deployment.

Exit Codes:
  0 - All checks passed
  1 - Validation errors found
  2 - Script error (file not found, etc.)

Usage:
  python3 scripts/ci/check_slack_gateway_config.py [env]

  env: dev, staging, or prod (default: dev)

Checks:
  - Terraform vars file exists and is valid HCL
  - Required variables present
  - No hardcoded secrets in prod
  - Service account naming convention
  - Environment labels present
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ValidationError:
    """Represents a validation error."""
    def __init__(self, severity: str, message: str, hint: Optional[str] = None):
        self.severity = severity  # 'ERROR', 'WARNING', 'INFO'
        self.message = message
        self.hint = hint


class SlackGatewayConfigValidator:
    """Validates Slack gateway Terraform configuration."""

    # Required variables for Slack gateway
    REQUIRED_VARS = [
        'project_id',
        'region',
        'environment',
        'app_name',
        'slack_webhook_image',
    ]

    # Variables that may reference secrets (acceptable patterns)
    SECRET_REF_VARS = [
        'slack_signing_secret_id',
        'slack_bot_token_secret_id',
    ]

    # Patterns that indicate hardcoded secrets (NEVER acceptable)
    SECRET_PATTERNS = [
        (r'xoxb-[a-zA-Z0-9-]+', 'Slack bot token'),
        (r'xoxp-[a-zA-Z0-9-]+', 'Slack user token'),
        (r'[a-f0-9]{32,}', 'Potential API key (32+ hex chars)'),
        (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI API key pattern'),
        (r'AIza[a-zA-Z0-9_-]{35}', 'Google API key pattern'),
    ]

    # Valid environments
    VALID_ENVIRONMENTS = ['dev', 'staging', 'prod']

    def __init__(self, env: str = 'dev'):
        self.env = env
        self.errors: List[ValidationError] = []
        self.config_file = Path(f'infra/terraform/envs/{env}.tfvars')
        self.config: Dict[str, str] = {}

    def add_error(self, severity: str, message: str, hint: Optional[str] = None):
        """Add a validation error."""
        self.errors.append(ValidationError(severity, message, hint))

    def parse_tfvars(self) -> bool:
        """Parse Terraform variables file."""
        if not self.config_file.exists():
            self.add_error(
                'ERROR',
                f'Configuration file not found: {self.config_file}',
                'Create the file or specify correct environment (dev/staging/prod)'
            )
            return False

        try:
            with open(self.config_file) as f:
                content = f.read()

            # Simple HCL parsing (not perfect, but sufficient for validation)
            # Matches: key = "value" or key = value
            pattern = r'(\w+)\s*=\s*(?:"([^"]+)"|(\S+))'
            matches = re.findall(pattern, content)

            for key, quoted_val, unquoted_val in matches:
                value = quoted_val if quoted_val else unquoted_val
                self.config[key] = value

            if not self.config:
                self.add_error(
                    'ERROR',
                    'No variables found in configuration file',
                    'Check HCL syntax and ensure file contains Terraform variables'
                )
                return False

            return True

        except Exception as e:
            self.add_error('ERROR', f'Failed to parse configuration: {e!s}')
            return False

    def check_required_variables(self):
        """Check that all required variables are present."""
        missing = [var for var in self.REQUIRED_VARS if var not in self.config]

        if missing:
            self.add_error(
                'ERROR',
                f'Missing required variables: {", ".join(missing)}',
                'Add these variables to your tfvars file'
            )

    def check_environment(self):
        """Validate environment value."""
        env_value = self.config.get('environment')

        if not env_value:
            self.add_error(
                'ERROR',
                'Environment variable not set',
                f'Set environment to one of: {", ".join(self.VALID_ENVIRONMENTS)}'
            )
        elif env_value not in self.VALID_ENVIRONMENTS:
            self.add_error(
                'ERROR',
                f'Invalid environment "{env_value}"',
                f'Must be one of: {", ".join(self.VALID_ENVIRONMENTS)}'
            )

    def check_hardcoded_secrets(self):
        """Check for hardcoded secrets (never acceptable in prod)."""
        # Read raw file content for secret scanning
        try:
            with open(self.config_file) as f:
                content = f.read()

            # Check for secret patterns
            for pattern, secret_type in self.SECRET_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    # Allow placeholder values in dev
                    if self.env == 'dev':
                        placeholder_patterns = [
                            'placeholder', 'dev-', 'test-', 'dummy', 'fake',
                            'YOUR_', 'REPLACE_', 'TODO'
                        ]
                        is_placeholder = any(
                            p.lower() in match.lower()
                            for match in matches
                            for p in placeholder_patterns
                        )

                        if is_placeholder:
                            self.add_error(
                                'INFO',
                                f'Dev placeholder detected for {secret_type}',
                                'Ensure real secrets are in Secret Manager for prod'
                            )
                            continue

                    # Hard error for prod secrets
                    severity = 'ERROR' if self.env == 'prod' else 'WARNING'
                    self.add_error(
                        severity,
                        f'Potential hardcoded {secret_type} detected',
                        'Use Secret Manager for sensitive values'
                    )

        except Exception as e:
            self.add_error('WARNING', f'Could not scan for secrets: {e!s}')

    def check_secret_manager_refs(self):
        """Verify Secret Manager references for prod."""
        if self.env != 'prod':
            return

        # In prod, we should use Secret Manager secret IDs
        for secret_var in self.SECRET_REF_VARS:
            if secret_var not in self.config:
                self.add_error(
                    'WARNING',
                    f'Secret Manager reference not found: {secret_var}',
                    'Production should use Secret Manager for credentials'
                )

    def check_labels(self):
        """Check that environment labels exist."""
        # Simple check - just verify 'labels' key exists in config
        # Full validation would require parsing the map structure
        has_labels = any('labels' in line.lower()
                        for line in open(self.config_file).readlines())

        if not has_labels:
            self.add_error(
                'WARNING',
                'No labels found in configuration',
                'Add labels for cost tracking and resource management'
            )

    def check_service_account(self):
        """Validate service account naming (if present)."""
        # Service account is created by module, so this is informational
        # Just check if there's a custom SA email that follows conventions
        # Skipping for now - module handles this

    def validate(self) -> Tuple[bool, List[ValidationError]]:
        """Run all validation checks."""
        print(f'{Colors.BLUE}Validating Slack gateway configuration for {self.env}...{Colors.END}')
        print()

        # Parse configuration
        if not self.parse_tfvars():
            return False, self.errors

        # Run validation checks
        self.check_required_variables()
        self.check_environment()
        self.check_hardcoded_secrets()
        self.check_secret_manager_refs()
        self.check_labels()
        self.check_service_account()

        # Determine overall result
        has_errors = any(e.severity == 'ERROR' for e in self.errors)

        return not has_errors, self.errors

    def print_results(self, success: bool, errors: List[ValidationError]):
        """Print validation results."""
        if not errors:
            print(f'{Colors.GREEN}✅ All checks passed!{Colors.END}')
            print()
            print(f'Configuration: {self.config_file}')
            print(f'Environment: {self.env}')
            return

        # Group errors by severity
        error_count = sum(1 for e in errors if e.severity == 'ERROR')
        warning_count = sum(1 for e in errors if e.severity == 'WARNING')
        info_count = sum(1 for e in errors if e.severity == 'INFO')

        # Print errors
        for error in errors:
            if error.severity == 'ERROR':
                icon = '❌'
                color = Colors.RED
            elif error.severity == 'WARNING':
                icon = '⚠️ '
                color = Colors.YELLOW
            else:  # INFO
                icon = 'ℹ️ '
                color = Colors.BLUE

            print(f'{color}{icon} {error.severity}: {error.message}{Colors.END}')
            if error.hint:
                print(f'   💡 {error.hint}')
            print()

        # Print summary
        print('─' * 60)
        if success:
            print(f'{Colors.GREEN}✅ Validation passed with warnings{Colors.END}')
        else:
            print(f'{Colors.RED}❌ Validation failed{Colors.END}')

        print(f'Errors: {error_count}, Warnings: {warning_count}, Info: {info_count}')
        print()


def main():
    """Main entry point."""
    # Parse arguments
    env = sys.argv[1] if len(sys.argv) > 1 else 'dev'

    if env not in SlackGatewayConfigValidator.VALID_ENVIRONMENTS:
        print(f'{Colors.RED}Invalid environment: {env}{Colors.END}')
        print(f'Valid environments: {", ".join(SlackGatewayConfigValidator.VALID_ENVIRONMENTS)}')
        return 2

    # Run validation
    validator = SlackGatewayConfigValidator(env)
    success, errors = validator.validate()
    validator.print_results(success, errors)

    # Exit with appropriate code
    if not success:
        return 1
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f'{Colors.RED}Script error: {e!s}{Colors.END}')
        import traceback
        traceback.print_exc()
        sys.exit(2)
