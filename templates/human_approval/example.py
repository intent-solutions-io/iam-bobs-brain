"""
Human Approval Example

Run this script to see the human approval pattern in action.

Usage:
    python example.py
"""

from workflow import (
    RiskLevel,
    classify_risk,
    create_deployment_approval_flow,
)


def main():
    """Run the example human approval pattern."""
    print("Creating Human Approval Pattern...")
    print("=" * 60)

    # Show risk classification
    print("Risk Classification Examples:")
    print("-" * 40)

    examples = [
        ("Update README", ["docs/README.md"]),
        ("Refactor utils", ["agents/utils.py"]),
        ("Deploy to staging", ["service/main.py"]),
        ("Delete old tables", ["migrations/drop.sql"]),
    ]

    for action, files in examples:
        risk = classify_risk(action, files)
        needs_approval = RiskLevel.requires_approval(risk)
        approval_str = "REQUIRES APPROVAL" if needs_approval else "auto-approved"
        print(f"  '{action}' → {risk.value.upper()} ({approval_str})")

    print()
    print("Risk Level Behavior:")
    print("  LOW      → Auto-approve")
    print("  MEDIUM   → Auto-approve + log")
    print("  HIGH     → Block until human approves")
    print("  CRITICAL → Block + escalation")

    print()

    # Create workflow
    print("Deployment Approval Workflow:")
    print("-" * 40)

    # Note: This requires google-adk to be installed
    try:
        workflow = create_deployment_approval_flow()
        print(f"Workflow: {workflow.name}")
        print(f"Pipeline: {' → '.join(a.name for a in workflow.sub_agents)}")
    except ImportError:
        print("  (Install google-adk to see workflow details)")

    print()
    print("Pattern Behavior:")
    print("  1. Risk assessor classifies action")
    print("  2. Approval gate checks risk level")
    print("  3. LOW/MEDIUM: Proceeds automatically")
    print("  4. HIGH/CRITICAL: Blocks until approved")
    print("  5. Timeout after 5 minutes (configurable)")

    print()
    print("To execute this pattern, use:")
    print("  from google.adk import Runner")
    print("  runner = Runner(agent=workflow)")
    print("  result = await runner.run(input={'action_request': 'Deploy v1.2.3'})")


if __name__ == "__main__":
    main()
