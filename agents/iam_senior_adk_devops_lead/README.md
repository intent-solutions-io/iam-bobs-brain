# iam-senior-adk-devops-lead - ADK Department Foreman

**Version:** 0.1.0
**Status:** In Development (Phase 1)
**Type:** Department Foreman / Orchestrator

## Overview

The `iam-senior-adk-devops-lead` agent serves as the department foreman for the ADK/Agent Engineering team. It acts as the middle layer between Bob (global orchestrator) and the iam-* specialist agents, managing task delegation and workflow coordination.

## Position in Hierarchy

```
Bob (Global Orchestrator)
    ↓
iam-senior-adk-devops-lead (Department Foreman) ← You are here
    ↓
iam-* specialists (Worker Agents)
```

## Responsibilities

### Primary Functions
1. **Request Analysis** - Understand and decompose high-level requests from Bob
2. **Task Planning** - Create execution plans using appropriate specialists
3. **Delegation** - Route tasks to correct specialist agents
4. **Coordination** - Orchestrate multi-agent workflows
5. **Quality Control** - Validate outputs from specialists
6. **Reporting** - Aggregate results back to Bob

### Specialists Managed
- **iam-adk** - ADK/Vertex design and static analysis
- **iam-issue** - GitHub issue specification and creation
- **iam-fix-plan** - Fix planning and design
- **iam-fix-impl** - Implementation and coding
- **iam-qa** - Testing and CI/CD verification
- **iam-doc** - Documentation and AAR creation
- **iam-cleanup** - Repository hygiene
- **iam-index** - Knowledge management

## Technical Implementation

### Base Architecture
- **Framework:** Google ADK LlmAgent
- **Model:** Gemini 2.0 Flash (fast, efficient for orchestration)
- **Memory:** Dual memory (Session + Memory Bank)
- **Runtime:** Vertex AI Agent Engine
- **Protocol:** A2A for agent-to-agent communication

### Tools Available
1. **delegate_to_specialist** - Invoke iam-* specialists
2. **create_task_plan** - Generate execution plans
3. **aggregate_results** - Combine specialist outputs
4. **analyze_repository** - Understand codebase state

## Usage Patterns

### Pattern 1: Single Specialist
```
Bob: "Analyze this code for ADK compliance"
    ↓
Foreman: Routes to iam-adk
    ↓
iam-adk: Performs analysis
    ↓
Foreman: Returns results to Bob
```

### Pattern 2: Sequential Workflow
```
Bob: "Fix this ADK pattern violation"
    ↓
Foreman: Creates plan
    ↓
    1. iam-adk: Analyze violation
    2. iam-fix-plan: Create fix plan
    3. iam-fix-impl: Implement fix
    4. iam-qa: Test changes
    ↓
Foreman: Aggregates and returns
```

### Pattern 3: Parallel Execution
```
Bob: "Audit the entire codebase"
    ↓
Foreman: Splits work
    ↓
    ├── iam-adk: Pattern analysis
    ├── iam-issue: Find existing issues
    └── iam-doc: Check documentation
    ↓
Foreman: Merges results
```

## Development Status

### Phase 1 (Current) ✅
- [x] Agent scaffold created
- [x] LlmAgent implementation
- [x] System prompt defined
- [x] Basic tools implemented
- [x] A2A card configured

### Phase 2 (Planned) ⏳
- [ ] Implement iam-* specialist agents
- [ ] Refine delegation patterns
- [ ] Add comprehensive tests
- [ ] Enhance tool capabilities

### Phase 3 (Future) 🔮
- [ ] Complete A2A wiring
- [ ] Terraform infrastructure
- [ ] CI/CD integration
- [ ] Production deployment

## Testing

### Smoke Test
```bash
# Test agent creation
python -c "from agents.iam_senior_adk_devops_lead.agent import get_agent; a = get_agent(); print('✅ Foreman agent created')"

# Test A2A card
python -c "from agents.iam_senior_adk_devops_lead.a2a_card import get_agent_card; c = get_agent_card(); print(f'✅ A2A: {c.name}')"
```

### Unit Tests
```bash
pytest tests/unit/test_iam_senior_adk_devops_lead.py -v
```

## Configuration

### Required Environment Variables
```bash
PROJECT_ID=your-gcp-project
LOCATION=us-central1
AGENT_ENGINE_ID=foreman-engine-id
APP_NAME=iam-senior-adk-devops-lead
AGENT_SPIFFE_ID=spiffe://intent.solutions/agent/iam-senior-adk-devops-lead/dev/us-central1/0.1.0
```

### Optional Configuration
```bash
FOREMAN_A2A_URL=https://iam-senior-adk-devops-lead.run.app
APP_VERSION=0.1.0
LOG_LEVEL=INFO
```

## Files Structure

```
iam-senior-adk-devops-lead/
├── __init__.py           # Package initialization
├── agent.py              # LlmAgent implementation
├── a2a_card.py           # A2A protocol card
├── README.md             # This file
└── tools/
    ├── __init__.py       # Tools package
    ├── delegation.py     # Specialist delegation
    ├── planning.py       # Task planning & aggregation
    └── repository.py     # Repository analysis
```

## Integration Points

### Input from Bob
```json
{
  "request_id": "req_123",
  "type": "audit|fix|implement|document",
  "description": "High-level request",
  "context": {...},
  "constraints": [...]
}
```

### Output to Bob
```json
{
  "request_id": "req_123",
  "status": "completed|failed|partial",
  "plan": {...},
  "results": {...},
  "follow_up": [...]
}
```

## Related Documentation

- [079-AA-PLAN-iam-senior-adk-devops-lead-design.md](../../000-docs/079-AA-PLAN-iam-senior-adk-devops-lead-design.md) - Design document
- [080-AA-REPT-iam-senior-adk-devops-lead-scaffold.md](../../000-docs/080-AA-REPT-iam-senior-adk-devops-lead-scaffold.md) - Implementation AAR (pending)
- [CLAUDE.md](../../CLAUDE.md) - Repository guide
- [078-DR-STND-opus-adk-agent-initialization.md](../../000-docs/078-DR-STND-opus-adk-agent-initialization.md) - Opus standard

## Support

- **Phase Lead:** ADK Department Build Captain
- **Repository:** bobs-brain
- **Status:** Active development