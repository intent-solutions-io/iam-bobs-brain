"""
Sequential Workflow Example

Run this script to see the sequential workflow in action.

Usage:
    python example.py
"""

from workflow import create_analysis_pipeline


def main():
    """Run the example sequential workflow."""
    print("Creating Sequential Workflow...")
    print("=" * 60)

    # Create the workflow
    workflow = create_analysis_pipeline()

    print(f"Workflow: {workflow.name}")
    print(f"Pipeline: {' → '.join(a.name for a in workflow.sub_agents)}")
    print()

    # Show state flow
    print("State Flow:")
    for i, agent in enumerate(workflow.sub_agents):
        output_key = getattr(agent, 'output_key', 'N/A')
        print(f"  {i+1}. {agent.name} → state['{output_key}']")

    print()
    print("To execute this workflow, use:")
    print("  from google.adk import Runner")
    print("  runner = Runner(agent=workflow)")
    print("  result = await runner.run(input={'user_input': 'Your problem here'})")


if __name__ == "__main__":
    main()
