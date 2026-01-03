"""
Parallel Analysis Workflow - Phase P2: Parallel Execution Pattern.

Implements Google's Parallel Fan-Out pattern using ADK's ParallelAgent.
Multiple analysis agents run concurrently, then results are aggregated.

Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/

State Flow:
┌──────────────────────────────────────────────────────────────┐
│                  parallel_analysis                            │
│  ┌──────────────┬──────────────┬──────────────┐              │
│  │   iam-adk    │  iam-cleanup │  iam-index   │  (Concurrent)│
│  │              │              │              │              │
│  │output_key:   │output_key:   │output_key:   │              │
│  │adk_findings  │cleanup_findgs│index_status  │              │
│  └──────┬───────┴──────┬───────┴──────┬───────┘              │
│         └──────────────┼──────────────┘                      │
│                        ▼                                     │
│                result_aggregator                             │
│                        │                                     │
│                output_key: aggregated_analysis               │
└──────────────────────────────────────────────────────────────┘
"""

from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent
import logging

logger = logging.getLogger(__name__)


def create_parallel_analysis() -> ParallelAgent:
    """
    Create parallel analysis agents using ParallelAgent.

    Concurrent execution of independent analysis tasks:
    - iam-adk: ADK compliance and pattern analysis
    - iam-cleanup: Repository hygiene and dead code detection
    - iam-index: Knowledge base status and gap analysis

    Each agent writes to a unique output_key to prevent race conditions.
    All three run simultaneously for improved latency.

    Returns:
        ParallelAgent: Configured parallel agent with three sub-agents
    """
    # Import agent factories (lazy to avoid circular imports)
    from agents.iam_adk.agent import create_agent as create_iam_adk
    from agents.iam_cleanup.agent import create_agent as create_iam_cleanup
    from agents.iam_index.agent import create_agent as create_iam_index

    logger.info("Creating parallel analysis workflow with 3 concurrent agents")

    parallel = ParallelAgent(
        name="parallel_analysis",
        sub_agents=[
            create_iam_adk(),      # output_key="adk_findings"
            create_iam_cleanup(),  # output_key="cleanup_findings"
            create_iam_index(),    # output_key="index_status"
        ],
    )

    logger.info("✅ ParallelAgent created with sub-agents: iam-adk, iam-cleanup, iam-index")
    return parallel


def create_result_aggregator() -> LlmAgent:
    """
    Create aggregator agent that combines parallel analysis results.

    Reads from session.state:
    - {adk_findings}: ADK compliance analysis results
    - {cleanup_findings}: Repository hygiene findings
    - {index_status}: Knowledge index status

    Outputs unified analysis report to state["aggregated_analysis"].

    Returns:
        LlmAgent: Configured aggregator agent
    """
    logger.info("Creating result aggregator agent")

    aggregator = LlmAgent(
        name="result_aggregator",
        model="gemini-2.0-flash-exp",
        instruction="""You are the Analysis Aggregator for the ADK/Agent Engineering Department.

## YOUR ROLE

Combine analysis results from three parallel agents into a unified report.

## INPUTS (from session.state)

1. **{adk_findings}**: ADK compliance analysis
   - Pattern violations (R1-R8)
   - Anti-patterns detected
   - Compliance score

2. **{cleanup_findings}**: Repository hygiene
   - Dead code locations
   - Unused dependencies
   - Structural issues

3. **{index_status}**: Knowledge base status
   - Index coverage
   - Knowledge gaps
   - Search performance

## OUTPUT FORMAT

Produce a unified analysis report with:

```json
{
  "summary": {
    "total_issues": <count>,
    "critical_count": <count>,
    "medium_count": <count>,
    "low_count": <count>,
    "overall_health": "HEALTHY|WARNING|CRITICAL"
  },
  "critical_issues": [
    {
      "source": "adk|cleanup|index",
      "type": "<issue_type>",
      "description": "<description>",
      "location": "<file:line or area>",
      "recommended_action": "<action>"
    }
  ],
  "medium_issues": [...],
  "low_issues": [...],
  "recommendations": [
    {
      "priority": 1,
      "action": "<recommended action>",
      "rationale": "<why this matters>",
      "effort": "low|medium|high"
    }
  ],
  "metrics": {
    "adk_compliance_score": <0-100>,
    "code_hygiene_score": <0-100>,
    "knowledge_coverage": <0-100>
  }
}
```

## AGGREGATION RULES

1. **Critical issues first**: Any issue that blocks deployment or causes errors
2. **Deduplicate**: If same issue reported by multiple agents, merge into one
3. **Prioritize recommendations**: Order by impact and effort
4. **Calculate overall health**:
   - CRITICAL: Any critical issue OR adk_compliance_score < 50
   - WARNING: Medium issues > 5 OR any score < 70
   - HEALTHY: All scores >= 70 and no critical issues

## IMPORTANT

- Never invent issues not present in the inputs
- Preserve specific file/line locations when available
- Be concise but complete
- Focus on actionable recommendations""",
        output_key="aggregated_analysis",
    )

    logger.info("✅ Result aggregator agent created")
    return aggregator


def create_analysis_workflow() -> SequentialAgent:
    """
    Create complete analysis workflow with parallel fan-out and gather.

    Pipeline:
    1. ParallelAgent runs 3 analysis agents concurrently
    2. SequentialAgent then runs aggregator to combine results

    This implements the "Fan-Out / Fan-In" pattern:
    - Fan-Out: ParallelAgent distributes work to specialists
    - Fan-In: Aggregator gathers and synthesizes results

    Returns:
        SequentialAgent: Complete analysis workflow
    """
    logger.info("Creating analysis workflow (parallel fan-out + aggregator)")

    workflow = SequentialAgent(
        name="analysis_workflow",
        sub_agents=[
            create_parallel_analysis(),  # Fan-out: concurrent analysis
            create_result_aggregator(),  # Fan-in: aggregate results
        ],
    )

    logger.info("✅ Analysis workflow created: parallel_analysis → result_aggregator")
    return workflow


# Export functions for workflow module
__all__ = [
    "create_parallel_analysis",
    "create_result_aggregator",
    "create_analysis_workflow",
]
