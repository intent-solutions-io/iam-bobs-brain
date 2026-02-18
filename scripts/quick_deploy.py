#!/usr/bin/env python3
"""Quick deploy script using Vertex AI SDK"""

import sys

from google.cloud.aiplatform_v1 import ReasoningEngineServiceClient
from google.cloud.aiplatform_v1.types import ReasoningEngine

PROJECT = "bobs-brain"
LOCATION = "us-central1"

# Agent configs
AGENTS = [
    ("bob", "Bob (Global Orchestrator)"),
    ("iam-senior-adk-devops-lead", "IAM Senior ADK DevOps Lead (Foreman)"),
    ("iam-adk", "IAM ADK (Specialist)"),
    ("iam-issue", "IAM Issue (Specialist)"),
    ("iam-fix-plan", "IAM Fix Plan (Specialist)"),
    ("iam-fix-impl", "IAM Fix Implementation (Specialist)"),
    ("iam-qa", "IAM QA (Specialist)"),
    ("iam-doc", "IAM Documentation (Specialist)"),
    ("iam-cleanup", "IAM Cleanup (Specialist)"),
    ("iam-index", "IAM Index (Specialist)"),
]


def list_engines():
    """List all reasoning engines"""
    print("📋 Listing reasoning engines...")

    # Try regional endpoint
    client_options = {"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
    client = ReasoningEngineServiceClient(client_options=client_options)

    parent = f"projects/{PROJECT}/locations/{LOCATION}"
    print(f"   Parent: {parent}")

    try:
        engines = list(client.list_reasoning_engines(parent=parent))
        print(f"✅ Found {len(engines)} engines\n")

        for engine in engines:
            engine_id = engine.name.split("/")[-1]
            print(f"  - {engine.display_name}")
            print(f"    ID: {engine_id}")
            print()

        return engines
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def deploy_agent(agent_name, display_name):
    """Deploy a single agent"""
    print(f"🚀 Deploying: {agent_name}")

    client_options = {"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
    client = ReasoningEngineServiceClient(client_options=client_options)

    parent = f"projects/{PROJECT}/locations/{LOCATION}"

    try:
        engine = ReasoningEngine(display_name=f"{display_name} (dev)")

        operation = client.create_reasoning_engine(
            parent=parent,
            reasoning_engine=engine,
        )

        print("   Creating... (this may take a minute)")
        result = operation.result(timeout=180)

        engine_id = result.name.split("/")[-1]
        print(f"✅ Deployed! ID: {engine_id}\n")

        return engine_id
    except Exception as e:
        print(f"❌ Failed: {e}\n")
        return None


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_engines()
    elif len(sys.argv) > 1 and sys.argv[1] == "deploy-all":
        print("🚀 Deploying all 10 agents...\n")
        results = {}

        for agent_name, display_name in AGENTS:
            engine_id = deploy_agent(agent_name, display_name)
            if engine_id:
                results[agent_name] = engine_id

        print("\n" + "=" * 50)
        print("📊 Deployment Summary")
        print("=" * 50)
        print(f"✅ Deployed: {len(results)}/{len(AGENTS)}\n")

        for agent_name, engine_id in results.items():
            print(f"{agent_name}: {engine_id}")

        print("\n💡 Update 000-docs/agent-engine-registry.csv with these IDs")
    else:
        print("Usage:")
        print("  python3 scripts/quick_deploy.py list")
        print("  python3 scripts/quick_deploy.py deploy-all")


if __name__ == "__main__":
    main()
