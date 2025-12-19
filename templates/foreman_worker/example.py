"""
Foreman-Worker Example

Run this script to see the foreman-worker pattern in action.

Usage:
    python example.py
"""

from workflow import create_analysis_department


def main():
    """Run the example foreman-worker pattern."""
    print("Creating Foreman-Worker Pattern...")
    print("=" * 60)

    # Create the department
    department = create_analysis_department()
    foreman = department["foreman"]
    workers = department["workers"]

    print(f"Foreman: {foreman.name}")
    print(f"Tools: {len(foreman.tools)} delegation tool(s)")
    print()

    print("Workers:")
    for worker in workers:
        output_key = getattr(worker, 'output_key', 'N/A')
        print(f"  - {worker.name}")
        print(f"    output_key: {output_key}")

    print()
    print("Pattern Behavior:")
    print("  1. Foreman receives high-level request")
    print("  2. Foreman analyzes and decomposes task")
    print("  3. Foreman delegates to appropriate worker(s)")
    print("  4. Workers execute domain-specific tasks")
    print("  5. Foreman aggregates results")

    print()
    print("Foreman Constraints:")
    print("  - NEVER executes worker tasks directly")
    print("  - ALWAYS delegates to workers")
    print("  - Returns structured aggregated results")

    print()
    print("To execute this pattern, use:")
    print("  from google.adk import Runner")
    print("  runner = Runner(agent=foreman)")
    print("  result = await runner.run(input={'request': 'Analyze my codebase'})")


if __name__ == "__main__":
    main()
