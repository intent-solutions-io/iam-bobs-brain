"""
Quality Gates Example

Run this script to see the quality gates pattern in action.

Usage:
    python example.py
"""

from workflow import create_content_qa_loop


def main():
    """Run the example quality gates workflow."""
    print("Creating Quality Gates Workflow...")
    print("=" * 60)

    # Create the workflow
    loop = create_content_qa_loop(max_iterations=3)

    print(f"Loop: {loop.name}")
    print(f"Max Iterations: {loop.max_iterations}")
    print()

    # Show loop structure
    review_pair = loop.sub_agents[0]
    print(f"Review Pair ({review_pair.name}):")
    for agent in review_pair.sub_agents:
        role = "Generator" if "generator" in agent.name else "Critic"
        output_key = getattr(agent, 'output_key', 'N/A')
        has_callback = "Yes" if agent.after_agent_callback else "No"
        print(f"  - {role}: {agent.name}")
        print(f"    output_key: {output_key}")
        print(f"    escalation callback: {has_callback}")

    print()
    print("Loop Behavior:")
    print("  1. Generator produces output → state['content']")
    print("  2. Critic reviews → state['qa_verdict']")
    print("  3. If PASS: escalate (exit loop)")
    print("  4. If FAIL: retry with feedback (up to 3 times)")

    print()
    print("To execute this workflow, use:")
    print("  from google.adk import Runner")
    print("  runner = Runner(agent=loop)")
    print("  result = await runner.run(input={'user_input': 'Write a blog post about ADK'})")


if __name__ == "__main__":
    main()
