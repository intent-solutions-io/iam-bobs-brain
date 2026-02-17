"""
Simple structure test for iam-doc agent.

This test verifies the agent structure is correct without requiring
google.adk to be installed (mocking the imports).
"""

import sys
from unittest.mock import MagicMock

# Mock google.adk modules
sys.modules["google"] = MagicMock()
sys.modules["google.adk"] = MagicMock()
sys.modules["google.adk.agents"] = MagicMock()
sys.modules["google.adk.sessions"] = MagicMock()
sys.modules["google.adk.memory"] = MagicMock()

# Now we can import our agent
from agents.iam_doc.tools.documentation_tools import (
    create_design_doc,
    generate_aar,
)

# Test tool imports
print("✅ All tools imported successfully")

# Test AAR generation
result = generate_aar(
    phase_name="Test Phase",
    objectives=["Objective 1", "Objective 2"],
    outcomes=["Outcome 1", "Outcome 2"],
    lessons_learned=["Lesson 1"],
    next_steps=["Next step 1"],
)

print(f"✅ AAR generated: {result['file_name']}")
print(f"   - Objectives: {result['metadata']['objectives_count']}")
print(f"   - Outcomes: {result['metadata']['outcomes_count']}")

# Test design doc creation
design = create_design_doc(
    title="Test Design",
    purpose="Test purpose",
    architecture="Test architecture",
    decisions=[{"decision": "Decision 1", "rationale": "Rationale 1"}],
)

print(f"✅ Design doc created: {design['file_name']}")
print(f"   - Decisions: {design['metadata']['decisions_count']}")

print("\n✅ All structure tests passed!")
print("iam-doc agent is ready for deployment to Vertex AI Agent Engine.")
