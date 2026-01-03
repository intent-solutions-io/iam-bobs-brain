# Bob's Brain Multi-Agent Pattern Templates

Reusable pattern templates for building multi-agent systems with Google ADK.

These templates implement Google's recommended [Multi-Agent Patterns](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/) using ADK primitives.

## Available Templates

| Template | Pattern | ADK Primitive | Use Case |
|----------|---------|---------------|----------|
| [Sequential Workflow](./sequential_workflow/) | Sequential Pipeline | `SequentialAgent` | Dependent step processing |
| [Parallel Workflow](./parallel_workflow/) | Parallel Fan-Out | `ParallelAgent` | Concurrent independent tasks |
| [Quality Gates](./quality_gates/) | Generator-Critic + Loop | `LoopAgent` | Iterative refinement |
| [Foreman-Worker](./foreman_worker/) | Hierarchical Decomposition | `LlmAgent` + A2A | Task delegation |
| [Human Approval](./human_approval/) | Human-in-the-Loop | Callbacks | Risk-gated execution |

## Quick Start

1. **Install ADK:**
   ```bash
   pip install google-adk
   ```

2. **Copy a template:**
   ```bash
   cp -r templates/sequential_workflow/ my_workflow/
   ```

3. **Customize the workflow:**
   ```python
   # Edit workflow.py with your agents
   from google.adk.agents import SequentialAgent

   workflow = SequentialAgent(
       name="my_workflow",
       sub_agents=[agent1, agent2, agent3],
   )
   ```

4. **Run the example:**
   ```bash
   python example.py
   ```

## Pattern Selection Guide

```
Need to process steps in order?
    → Sequential Workflow

Need to run independent tasks concurrently?
    → Parallel Workflow

Need to iterate until quality passes?
    → Quality Gates (LoopAgent)

Need to delegate tasks to specialists?
    → Foreman-Worker

Need human approval for risky actions?
    → Human Approval
```

## Template Structure

Each template includes:

```
template_name/
├── README.md           # Pattern documentation
├── workflow.py         # Reusable workflow factory
├── example.py          # Runnable example
└── requirements.txt    # Dependencies (if any)
```

## Integration with Agent Starter Pack

These templates are designed to work with [Agent Starter Pack](https://github.com/GoogleCloudPlatform/agent-starter-pack). Copy templates into your ASP-based project:

```bash
# From your ASP project root
cp -r /path/to/bobs-brain/templates/sequential_workflow/ app/workflows/
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on improving these templates.

## References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Multi-Agent Patterns Guide](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)
- [Agent Starter Pack](https://github.com/GoogleCloudPlatform/agent-starter-pack)
- [Bob's Brain Repository](https://github.com/intent-solutions-io/bobs-brain)

## License

Apache 2.0 - See LICENSE file.
