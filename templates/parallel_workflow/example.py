"""
Parallel Workflow Example

Run this script to see the parallel workflow in action.

Usage:
    python example.py
"""

from workflow import create_multi_source_analysis


def main():
    """Run the example parallel workflow."""
    print("Creating Parallel Workflow...")
    print("=" * 60)

    # Create the workflow
    workflow = create_multi_source_analysis()

    print(f"Workflow: {workflow.name}")
    print()

    # Show parallel agents
    parallel = workflow.sub_agents[0]
    print(f"Parallel Phase ({parallel.name}):")
    for agent in parallel.sub_agents:
        output_key = getattr(agent, 'output_key', 'N/A')
        print(f"  - {agent.name} → state['{output_key}']")

    print()

    # Show aggregator
    if len(workflow.sub_agents) > 1:
        aggregator = workflow.sub_agents[1]
        output_key = getattr(aggregator, 'output_key', 'N/A')
        print(f"Aggregation Phase:")
        print(f"  - {aggregator.name} → state['{output_key}']")

    print()
    print("Key Pattern:")
    print("  1. All parallel agents run CONCURRENTLY")
    print("  2. Each writes to UNIQUE output_key (prevents race conditions)")
    print("  3. Aggregator combines all results")

    print()
    print("To execute this workflow, use:")
    print("  from google.adk import Runner")
    print("  runner = Runner(agent=workflow)")
    print("  result = await runner.run(input={'user_input': 'Your input here'})")


if __name__ == "__main__":
    main()
