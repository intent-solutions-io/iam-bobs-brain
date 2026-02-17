"""
Example agent with ADK violations for testing.
This file deliberately contains anti-patterns for the pipeline to detect.
"""


# VIOLATION: Not using ADK LlmAgent pattern
class ExampleAgent:
    """Legacy agent not using ADK patterns."""

    def __init__(self, name: str, model: str = "gpt-4"):
        # VIOLATION: Using OpenAI instead of Gemini
        self.name = name
        self.model = model
        self.tools = []  # VIOLATION: Custom tool handling

    def add_tool(self, tool_func):
        """Add a tool to the agent."""
        # VIOLATION: Not using ADK tool registration
        self.tools.append(tool_func)

    def run(self, prompt: str) -> str:
        """Execute the agent."""
        # VIOLATION: Direct LLM calls without ADK
        # Simulating OpenAI call
        response = f"Mock response for: {prompt}"
        return response


# VIOLATION: Missing proper ADK memory setup
def create_agent():
    """Create an agent instance."""
    agent = ExampleAgent("test_agent")

    # VIOLATION: Custom tool definition
    def custom_tool(query: str):
        return f"Tool result: {query}"

    agent.add_tool(custom_tool)
    return agent


# VIOLATION: Missing A2A protocol support
# VIOLATION: No AgentCard definition
# VIOLATION: No proper error handling
# VIOLATION: No observability/logging setup

if __name__ == "__main__":
    # VIOLATION: Direct execution instead of ADK runner
    agent = create_agent()
    result = agent.run("Test prompt")
    print(result)
