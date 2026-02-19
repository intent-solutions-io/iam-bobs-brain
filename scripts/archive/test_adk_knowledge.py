#!/usr/bin/env python3
"""
Test Bob's ADK Knowledge

This script tests Bob's ability to answer ADK-related questions using:
1. Enhanced ADK expert instructions
2. Local ADK documentation search tools
3. API reference lookup capabilities

Usage:
    python scripts/test_adk_knowledge.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner

from agents.bob.tools.adk_tools import (
    get_adk_api_reference,
    list_adk_documentation,
    search_adk_docs,
)


async def test_adk_knowledge():
    """Test Bob's ADK knowledge with sample queries."""

    print("=" * 80)
    print("🧪 Testing Bob's ADK Knowledge")
    print("=" * 80)

    # Create simplified agent for testing (no SPIFFE ID, Vertex services needed)
    agent = LlmAgent(
        name="Bob",
        model="gemini-2.0-flash-exp",
        tools=[
            search_adk_docs,
            get_adk_api_reference,
            list_adk_documentation,
        ],
        instruction="""You are Bob, an expert Google Agent Development Kit (ADK) specialist.

You help developers:
- Design and build AI agents using Google ADK
- Understand ADK architecture and best practices
- Implement tools and multi-agent systems
- Deploy to Vertex AI Agent Engine

You have access to comprehensive local ADK documentation via tools:
- search_adk_docs: Search all documentation
- get_adk_api_reference: Get API details for classes
- list_adk_documentation: See available docs

When answering ADK questions:
1. Use the documentation tools to find accurate information
2. Provide specific code examples with correct imports
3. Explain both what and why
4. Reference official patterns

Be concise and helpful.""",
    )

    # Create in-memory runner for testing
    runner = InMemoryRunner(agent=agent, app_name="test-bobs-brain")

    # Test queries
    test_queries = [
        # Query 1: Basic agent creation
        {
            "query": "How do I create a simple LlmAgent with tools in Google ADK? Show me code.",
            "expected": ["LlmAgent", "tools", "model", "instruction"],
        },
        # Query 2: Multi-agent system
        {
            "query": "What's the difference between SequentialAgent and ParallelAgent?",
            "expected": ["SequentialAgent", "ParallelAgent", "sub_agents"],
        },
        # Query 3: Deployment
        {
            "query": "How do I deploy an agent to Vertex AI Agent Engine?",
            "expected": ["adk deploy", "agent_engine", "Vertex"],
        },
        # Query 4: Memory management
        {
            "query": "Explain the dual memory pattern with Session and Memory Bank.",
            "expected": [
                "VertexAiSessionService",
                "VertexAiMemoryBankService",
                "Runner",
            ],
        },
    ]

    results = []

    for idx, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        expected_terms = test_case["expected"]

        print(f"\n{'=' * 80}")
        print(f"📝 Test {idx}/{len(test_queries)}: {query}")
        print(f"{'=' * 80}\n")

        try:
            # Use run_debug() for testing
            events = await runner.run_debug(
                query, verbose=False  # Set to True for detailed logs
            )

            # Extract final response
            final_response = None
            tool_calls = []

            for event in events:
                # Track tool calls
                if event.content and hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "function_call"):
                            tool_calls.append(part.function_call.name)

                # Get final response
                if event.is_final_response():
                    final_response = (
                        event.content.text
                        if hasattr(event.content, "text")
                        else str(event.content)
                    )

            if final_response:
                print(f"🤖 **Bob's Response:**\n{final_response}\n")

                # Check if expected terms are in response
                response_lower = final_response.lower()
                matched_terms = [
                    term for term in expected_terms if term.lower() in response_lower
                ]

                # Evaluate quality
                if tool_calls:
                    print(f"✅ Tools used: {', '.join(tool_calls)}")

                if (
                    len(matched_terms) >= len(expected_terms) * 0.7
                ):  # At least 70% coverage
                    print(
                        f"✅ Response quality: GOOD (matched {len(matched_terms)}/{len(expected_terms)} expected terms)"
                    )
                    results.append(
                        {
                            "query": query,
                            "status": "PASS",
                            "matched": len(matched_terms),
                        }
                    )
                else:
                    print(
                        f"⚠️  Response quality: PARTIAL (matched {len(matched_terms)}/{len(expected_terms)} expected terms)"
                    )
                    results.append(
                        {
                            "query": query,
                            "status": "PARTIAL",
                            "matched": len(matched_terms),
                        }
                    )
            else:
                print("❌ No final response received")
                results.append({"query": query, "status": "FAIL", "matched": 0})

        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({"query": query, "status": "ERROR", "matched": 0})

    # Cleanup
    await runner.close()

    # Summary
    print(f"\n{'=' * 80}")
    print("📊 Test Summary")
    print(f"{'=' * 80}\n")

    passed = sum(1 for r in results if r["status"] == "PASS")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    failed = sum(1 for r in results if r["status"] in ["FAIL", "ERROR"])

    print(f"✅ Passed: {passed}/{len(results)}")
    print(f"⚠️  Partial: {partial}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")

    if passed >= len(results) * 0.75:  # At least 75% pass rate
        print("\n🎉 **Overall: SUCCESS** - Bob demonstrates strong ADK knowledge!")
        return 0
    elif passed + partial >= len(results) * 0.75:
        print(
            "\n⚠️  **Overall: PARTIAL** - Bob has ADK knowledge but could be more accurate"
        )
        return 0
    else:
        print("\n❌ **Overall: NEEDS IMPROVEMENT** - Bob needs better ADK grounding")
        return 1


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Bob's Brain - ADK Knowledge Test Suite")
    print("=" * 80 + "\n")

    exit_code = asyncio.run(test_adk_knowledge())

    print(f"\n{'=' * 80}")
    print("✅ Testing complete!")
    print(f"{'=' * 80}\n")

    sys.exit(exit_code)
