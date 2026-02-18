#!/usr/bin/env python3
"""
Deploy Agent to Vertex AI Agent Engine (Inline Source Pattern)

This script deploys agents to Vertex AI Agent Engine using the inline source
deployment pattern (6767-INLINE), which deploys code directly from the
repository without requiring Cloud Storage buckets.

Part of Phase 21 - Real Agent Engine deployment implementation.

Usage:
    # Dry-run (config validation only)
    python scripts/deploy_inline_source.py --agent bob --env dev --dry-run

    # Real deployment
    python scripts/deploy_inline_source.py --agent bob --env dev --project bobs-brain --region us-central1

Exit Codes:
    0 - Success
    1 - API/deployment error
    2 - Configuration/argument error
    3 - Missing dependencies

Related Docs:
    - 000-docs/152-AA-REPT-phase-21-agent-engine-dev-first-live-deploy-and-smoke-tests.md
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_config(config: Dict) -> None:
    """Print deployment configuration in a readable format."""
    print("\n" + "=" * 80)
    print("DEPLOYMENT CONFIGURATION")
    print("=" * 80)
    for key, value in config.items():
        print(f"{key:25} {value}")
    print("=" * 80 + "\n")


def validate_config(args: argparse.Namespace) -> Dict:
    """
    Validate deployment configuration and return config dict.

    Args:
        args: Command-line arguments

    Returns:
        Configuration dictionary

    Raises:
        SystemExit: If configuration is invalid (exit code 2)
    """
    # Validate agent
    valid_agents = ["bob", "foreman", "iam-adk", "iam-issue"]
    if args.agent not in valid_agents:
        print(f"❌ Error: Invalid agent '{args.agent}'")
        print(f"Valid agents: {', '.join(valid_agents)}")
        sys.exit(2)

    # Validate environment
    valid_envs = ["dev", "staging", "prod"]
    if args.env not in valid_envs:
        print(f"❌ Error: Invalid environment '{args.env}'")
        print(f"Valid environments: {', '.join(valid_envs)}")
        sys.exit(2)

    # For non-dry-run, require project and region
    if not args.dry_run:
        if not args.project:
            # Try environment variable
            args.project = os.getenv("PROJECT_ID")
            if not args.project:
                print("❌ Error: --project required for real deployment")
                print("   Or set PROJECT_ID environment variable")
                sys.exit(2)

        if not args.region:
            # Try environment variable
            args.region = os.getenv("LOCATION", "us-central1")

    # Build configuration
    agent_module_map = {
        "bob": "agents.bob.agent",
        "foreman": "agents.iam_senior_adk_devops_lead.agent",
        "iam-adk": "agents.iam_adk.agent",
        "iam-issue": "agents.iam_issue.agent",
    }

    display_name_map = {
        "bob": "bobs-brain",
        "foreman": "bobs-brain-foreman",
        "iam-adk": "bobs-brain-iam-adk",
        "iam-issue": "bobs-brain-iam-issue",
    }

    config = {
        "agent": args.agent,
        "environment": args.env,
        "project": args.project or "NOT_SET",
        "region": args.region or "NOT_SET",
        "agent_module": agent_module_map[args.agent],
        "entrypoint": f"{agent_module_map[args.agent]}::app",
        "display_name": f"{display_name_map[args.agent]}-{args.env}",
        "description": f"{display_name_map[args.agent]} deployed to {args.env}",
        "dry_run": args.dry_run,
    }

    return config


def deploy_with_inline_source(config: Dict) -> str:
    """
    Deploy agent to Vertex AI Agent Engine using inline source.

    Args:
        config: Deployment configuration dictionary

    Returns:
        Resource name of deployed agent

    Raises:
        SystemExit: If deployment fails (exit code 1 or 3)

    Environment Variables (Observability/Telemetry):
        GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY: Enable Agent Engine telemetry (default: true)
        OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT: Capture LLM message content in traces (default: false)
            WARNING: May include sensitive user data, use with care in dev-only environments
    """
    # Check dependencies
    try:
        import vertexai
        from vertexai import agent_engines
    except ImportError as e:
        print(f"❌ Error: Missing required libraries: {e}")
        print("   Install with: pip install google-cloud-aiplatform[adk,agent_engines]")
        sys.exit(3)

    # Read telemetry configuration from environment
    # These control observability and tracing for Agent Engine deployments
    enable_telemetry = (
        os.getenv("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "true").lower()
        == "true"
    )
    capture_message_content = (
        os.getenv("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "false").lower()
        == "true"
    )

    print(f"🚀 Deploying {config['agent']} to Vertex AI Agent Engine...")
    print(f"   Environment: {config['environment']}")
    print(f"   Project: {config['project']}")
    print(f"   Region: {config['region']}")
    print(f"   Display Name: {config['display_name']}")
    print(f"   Telemetry Enabled: {enable_telemetry}")
    if capture_message_content:
        print(
            f"   ⚠️  Message Content Capture: {capture_message_content} (dev-only, may include sensitive data)"
        )

    try:
        # Initialize Vertex AI
        vertexai.init(
            project=config["project"],
            location=config["region"],
        )

        # Import the agent module
        print(f"\n📦 Loading agent from {config['agent_module']}...")
        module_path, app_name = config["entrypoint"].split("::")
        import importlib

        module = importlib.import_module(module_path)

        # Get the agent/app object
        if hasattr(module, app_name):
            agent_app = getattr(module, app_name)
        elif hasattr(module, "get_agent"):
            # Fallback: wrap agent in AdkApp
            agent = module.get_agent()
            agent_app = agent_engines.AdkApp(
                agent=agent,
                enable_tracing=enable_telemetry,  # Use telemetry config from env
            )
        else:
            raise ValueError(
                f"Cannot find '{app_name}' or 'get_agent()' in {module_path}"
            )

        # Set OTEL env var for message content capture (if enabled)
        # This must be set before agent execution for OpenTelemetry to pick it up
        if capture_message_content:
            os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"

        print("✅ Agent loaded successfully")

        # Deploy to Agent Engine
        print("\n🔄 Creating reasoning engine on Vertex AI...")
        print("   This may take 2-3 minutes...")

        remote_app = agent_engines.create(
            agent_engine=agent_app,
            requirements=[
                "google-cloud-aiplatform[adk,agent_engines]>=1.111",
                "google-adk>=1.15.1",
            ],
            display_name=config["display_name"],
            description=config["description"],
        )

        resource_name = remote_app.resource_name
        print("\n✅ Deployment successful!")
        print(f"   Resource Name: {resource_name}")

        # Extract reasoning engine ID
        engine_id = resource_name.split("/")[-1]
        print(f"   Engine ID: {engine_id}")
        print("\n🔍 View in Console:")
        print(
            f"   https://console.cloud.google.com/vertex-ai/agent-engine?project={config['project']}"
        )

        return resource_name

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Deploy agent to Vertex AI Agent Engine with inline source",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry-run (config validation only)
    python scripts/deploy_inline_source.py --agent bob --env dev --dry-run

    # Deploy bob to dev
    python scripts/deploy_inline_source.py \\
        --agent bob \\
        --env dev \\
        --project bobs-brain \\
        --region us-central1

    # Deploy foreman to dev (using env vars)
    export PROJECT_ID=bobs-brain
    export LOCATION=us-central1
    python scripts/deploy_inline_source.py --agent foreman --env dev
        """,
    )

    parser.add_argument(
        "--agent",
        required=True,
        choices=["bob", "foreman", "iam-adk", "iam-issue"],
        help="Agent to deploy",
    )

    parser.add_argument(
        "--env",
        required=True,
        choices=["dev", "staging", "prod"],
        help="Environment to deploy to",
    )

    parser.add_argument("--project", help="GCP project ID (or use PROJECT_ID env var)")

    parser.add_argument(
        "--region", help="GCP region (or use LOCATION env var, defaults to us-central1)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration only, do not deploy",
    )

    args = parser.parse_args()

    # Validate configuration
    config = validate_config(args)

    # Print configuration
    print_config(config)

    # Dry-run mode: just validate and exit
    if config["dry_run"]:
        print("✅ Configuration valid (dry-run mode)")
        print("   To deploy for real, remove --dry-run flag")
        sys.exit(0)

    # Real deployment
    resource_name = deploy_with_inline_source(config)
    print(
        f"\n🎉 Agent {config['agent']} successfully deployed to {config['environment']}"
    )
    print(f"   Resource: {resource_name}")
    sys.exit(0)


if __name__ == "__main__":
    main()
