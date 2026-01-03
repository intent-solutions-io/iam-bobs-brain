# Agent Templates

Reusable scaffolds for creating new agents in the Bob's Brain agent factory.

## Available Templates

### specialist-agent-adk/
Template for creating ADK-based specialist agents (backend workers called via A2A).

**Use case**: Backend agents that provide specific capabilities (search, audit, analysis)

### orchestrator-agent/
Template for creating orchestrator agents (user-facing, delegates to specialists).

**Use case**: Frontend agents that coordinate specialist agents

## Usage

```bash
# Copy template for new specialist agent
cp -r templates/specialist-agent-adk/ agents/my-new-agent/

# Customize agent.py, system-prompt.md, tools/
cd agents/my-new-agent/
# ... edit files ...
```
