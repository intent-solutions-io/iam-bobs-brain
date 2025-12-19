"""
Compliance Workflow - Sequential Pipeline Pattern

Implements Google's Sequential Pipeline pattern using SequentialAgent.
Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/

Pipeline: iam-adk -> iam-issue -> iam-fix-plan
State flow:
  - iam-adk outputs to "adk_findings" in session.state
  - iam-issue reads {adk_findings}, outputs to "issue_specs"
  - iam-fix-plan reads {issue_specs}, outputs to "fix_plans"

This workflow automates the compliance analysis pipeline:
1. Analyze repository for ADK pattern violations (iam-adk)
2. Convert findings into structured issue specifications (iam-issue)
3. Create implementation plans for each issue (iam-fix-plan)

Usage:
    from agents.workflows import create_compliance_workflow

    workflow = create_compliance_workflow()
    # Run via Runner or within a parent agent
"""

from google.adk.agents import LlmAgent, SequentialAgent
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment variables
AGENT_SPIFFE_ID = os.getenv(
    "AGENT_SPIFFE_ID",
    "spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.14.0",
)


def create_analysis_agent() -> LlmAgent:
    """
    Create the ADK analysis agent with output_key for state passing.

    This agent analyzes repositories for ADK pattern violations and writes
    findings to session.state["adk_findings"].

    Returns:
        LlmAgent: Configured analysis agent with output_key="adk_findings"
    """
    logger.info("Creating analysis agent for compliance workflow")

    # Lazy import to avoid circular dependency
    from agents.shared_tools import IAM_ADK_TOOLS

    instruction = """You are the ADK analysis specialist in a compliance workflow.

**Your Task:** Analyze the provided repository or code for ADK pattern violations.

**Input:** You receive a task with:
- repo_path: Path to repository to analyze
- focus_areas: Specific directories or patterns to check
- rules: Which Hard Mode rules (R1-R8) to validate

**Output:** Write your findings to state as structured JSON:
```json
{
  "compliance_status": "COMPLIANT|NON_COMPLIANT|WARNING",
  "violations": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "rule": "R1|R2|...|R8",
      "file": "path/to/file.py",
      "line": 42,
      "message": "Description of violation",
      "remediation": "How to fix it"
    }
  ],
  "summary": "Brief summary of findings",
  "analyzed_files": ["list", "of", "files"]
}
```

**Important:** Your output will be used by the next agent in the pipeline (iam-issue).
Be thorough but structured - the issue agent needs clear, actionable findings."""

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",
        name="workflow_analysis",
        instruction=instruction,
        tools=IAM_ADK_TOOLS,
        output_key="adk_findings",  # State key for SequentialAgent
    )

    logger.info(
        "Analysis agent created with output_key='adk_findings'",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    return agent


def create_issue_agent() -> LlmAgent:
    """
    Create the issue specification agent with state reading and output_key.

    This agent reads findings from session.state["adk_findings"] and writes
    issue specifications to session.state["issue_specs"].

    Returns:
        LlmAgent: Configured issue agent with output_key="issue_specs"
    """
    logger.info("Creating issue agent for compliance workflow")

    # Lazy import to avoid circular dependency
    from agents.shared_tools import IAM_ISSUE_TOOLS

    instruction = """You are the issue specification specialist in a compliance workflow.

**Your Task:** Convert ADK analysis findings into structured GitHub issue specifications.

**Input:** Read findings from state variable {adk_findings}:
- compliance_status: Overall status
- violations: List of violations with severity, rule, file, line, message, remediation

**Output:** Write issue specifications to state as structured JSON:
```json
{
  "issue_specs": [
    {
      "title": "Brief, descriptive title",
      "component": "agents|service|infra|ci|docs",
      "severity": "low|medium|high|critical",
      "type": "bug|tech_debt|improvement|task|violation",
      "description": "Full issue description with context",
      "acceptance_criteria": ["List", "of", "criteria"],
      "labels": ["generated", "labels"],
      "source_violations": ["list of violation IDs this addresses"]
    }
  ],
  "summary": "Brief summary of issues created",
  "total_issues": 3
}
```

**Important:** Your output will be used by the next agent (iam-fix-plan).
Group related violations into single issues when appropriate."""

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",
        name="workflow_issue",
        instruction=instruction,
        tools=IAM_ISSUE_TOOLS,
        output_key="issue_specs",  # State key for SequentialAgent
    )

    logger.info(
        "Issue agent created with output_key='issue_specs'",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    return agent


def create_planning_agent() -> LlmAgent:
    """
    Create the fix planning agent with state reading and output_key.

    This agent reads issue specs from session.state["issue_specs"] and writes
    fix plans to session.state["fix_plans"].

    Returns:
        LlmAgent: Configured planning agent with output_key="fix_plans"
    """
    logger.info("Creating planning agent for compliance workflow")

    # Lazy import to avoid circular dependency
    from agents.shared_tools import IAM_FIX_PLAN_TOOLS

    instruction = """You are the fix planning specialist in a compliance workflow.

**Your Task:** Create implementation plans for issue specifications.

**Input:** Read issue specifications from state variable {issue_specs}:
- issue_specs: List of issues with title, component, severity, description, etc.

**Output:** Write fix plans to state as structured JSON:
```json
{
  "fix_plans": [
    {
      "issue_title": "Reference to source issue",
      "summary": "Brief description of fix approach",
      "risk_level": "low|medium|high",
      "implementation_steps": [
        {
          "step": 1,
          "description": "What to do",
          "files_affected": ["list", "of", "files"],
          "estimated_effort": "30 minutes"
        }
      ],
      "testing_strategy": {
        "unit_tests": ["tests to add/modify"],
        "integration_tests": ["integration tests"],
        "manual_verification": ["manual steps"]
      },
      "rollout_notes": "Deployment considerations",
      "total_effort": "2 hours"
    }
  ],
  "summary": "Brief summary of all fix plans",
  "total_effort": "8 hours",
  "risk_assessment": "Overall risk assessment"
}
```

**Important:** This is the final stage of the compliance workflow.
Your output will be reviewed by the foreman and potentially executed by iam-fix-impl."""

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",
        name="workflow_planning",
        instruction=instruction,
        tools=IAM_FIX_PLAN_TOOLS,
        output_key="fix_plans",  # State key for SequentialAgent
    )

    logger.info(
        "Planning agent created with output_key='fix_plans'",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    return agent


def create_compliance_workflow() -> SequentialAgent:
    """
    Create the complete compliance analysis workflow using SequentialAgent.

    This implements Google's Sequential Pipeline pattern:
    - Agents execute in order: analysis -> issue -> planning
    - Each agent writes to unique output_key in session.state
    - Next agent reads from previous agent's output_key

    Pipeline:
        iam-adk (analysis) -> iam-issue -> iam-fix-plan
        output_key: adk_findings -> issue_specs -> fix_plans

    Returns:
        SequentialAgent: Configured workflow ready for execution

    Usage:
        workflow = create_compliance_workflow()

        # Execute via Runner
        runner = Runner(agent=workflow, app_name="compliance")
        result = runner.run(session_id="...", user_id="...", new_message=task)

        # Or use within foreman as AgentTool (Phase 2)
        # workflow_tool = AgentTool(agent=workflow)
    """
    logger.info(
        "Creating compliance workflow (SequentialAgent)",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    # Create individual agents with output_key
    analysis_agent = create_analysis_agent()
    issue_agent = create_issue_agent()
    planning_agent = create_planning_agent()

    # Create SequentialAgent pipeline
    workflow = SequentialAgent(
        name="compliance_workflow",
        sub_agents=[
            analysis_agent,   # Step 1: Analyze -> adk_findings
            issue_agent,      # Step 2: Create issues -> issue_specs
            planning_agent,   # Step 3: Plan fixes -> fix_plans
        ],
    )

    logger.info(
        "Compliance workflow created successfully",
        extra={
            "spiffe_id": AGENT_SPIFFE_ID,
            "pipeline": "analysis -> issue -> planning",
            "output_keys": ["adk_findings", "issue_specs", "fix_plans"],
        }
    )

    return workflow


# ============================================================================
# MODULE-LEVEL WORKFLOW (For testing/direct use)
# ============================================================================

# Note: For production use in foreman, call create_compliance_workflow()
# and integrate with the foreman's orchestration logic.

if __name__ == "__main__":
    """
    Test the compliance workflow creation.

    This entry point validates the workflow structure without executing.
    """
    logger.info("Testing compliance workflow creation...")

    workflow = create_compliance_workflow()

    print(f"Workflow name: {workflow.name}")
    print(f"Sub-agents: {[a.name for a in workflow.sub_agents]}")
    print("Output keys:")
    for agent in workflow.sub_agents:
        print(f"  - {agent.name}: output_key={getattr(agent, 'output_key', 'N/A')}")

    logger.info("Compliance workflow test complete")
