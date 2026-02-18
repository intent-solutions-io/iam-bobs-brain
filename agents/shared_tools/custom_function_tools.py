"""
Custom Function Tools Module

This module demonstrates how to create custom tools using ADK's FunctionTool pattern.
Based on documentation: https://google.github.io/adk-docs/tools-custom/function-tools/

ADK Custom Tool Creation Pattern:
1. Define a function with type hints
2. Add comprehensive docstring with Args and Returns
3. Wrap with @dataclass or use directly as FunctionTool

Example:
    from dataclasses import dataclass
    from google.adk.tools import FunctionTool

    @dataclass
    class MyCustomTool(FunctionTool):
        def __call__(self, param: str) -> str:
            '''Custom tool description.

            Args:
                param: Parameter description

            Returns:
                Return value description
            '''
            return f"Result: {param}"
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# EXAMPLE: Creating Custom Function Tools
# ============================================================================


def example_custom_tool(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Example custom tool following ADK pattern.

    This demonstrates the correct way to create a custom tool:
    - Type hints on all parameters
    - Comprehensive docstring
    - Args section describing each parameter
    - Returns section describing output

    Args:
        query: The search query to execute
        max_results: Maximum number of results to return (default: 10)

    Returns:
        List of result dictionaries containing matches
    """
    # Tool implementation
    results = []
    # ... actual implementation ...
    return results


def create_custom_file_tool(base_path: str = "/workspace") -> Any:
    """
    Factory function to create a custom file access tool.

    This pattern is useful when you need to configure tools with specific settings.

    Args:
        base_path: Base directory for file operations

    Returns:
        Configured file tool function
    """

    def file_tool(operation: str, path: str, content: Optional[str] = None) -> str:
        """
        Custom file operations tool.

        Args:
            operation: One of 'read', 'write', 'list'
            path: Relative path from base directory
            content: Content to write (for write operations)

        Returns:
            File content, list of files, or operation status
        """
        import os

        full_path = os.path.join(base_path, path)

        if operation == "read":
            try:
                with open(full_path) as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
        elif operation == "write":
            if content is None:
                return "Error: content required for write operation"
            try:
                with open(full_path, "w") as f:
                    f.write(content)
                return f"Successfully wrote to {path}"
            except Exception as e:
                return f"Error writing file: {e}"
        elif operation == "list":
            try:
                files = os.listdir(full_path)
                return "\n".join(files)
            except Exception as e:
                return f"Error listing directory: {e}"
        else:
            return f"Unknown operation: {operation}"

    return file_tool


# ============================================================================
# PATTERN: Tool Validation
# ============================================================================


def validate_tool_signature(func: Any) -> bool:
    """
    Validate that a function follows ADK tool requirements.

    ADK tools must have:
    - Type hints on all parameters
    - Comprehensive docstring
    - Args section in docstring
    - Returns section in docstring

    Args:
        func: Function to validate

    Returns:
        True if valid ADK tool signature
    """
    import inspect

    # Check for type hints
    sig = inspect.signature(func)
    for param_name, param in sig.parameters.items():
        if param.annotation == inspect.Parameter.empty:
            logger.warning(f"Parameter {param_name} missing type hint")
            return False

    # Check for docstring
    if not func.__doc__:
        logger.warning("Function missing docstring")
        return False

    # Check for Args and Returns sections
    doc = func.__doc__.lower()
    if "args:" not in doc:
        logger.warning("Docstring missing Args section")
        return False
    if "returns:" not in doc:
        logger.warning("Docstring missing Returns section")
        return False

    return True


# ============================================================================
# PATTERN: Tool Wrapper for Legacy Functions
# ============================================================================


def wrap_legacy_function(func: Any, description: str) -> Any:
    """
    Wrap a legacy function to make it ADK-compatible.

    This is useful when integrating existing code that doesn't follow ADK patterns.

    Args:
        func: Legacy function to wrap
        description: Description of what the function does

    Returns:
        ADK-compatible tool function
    """
    import functools
    import inspect

    @functools.wraps(func)
    def wrapped_tool(**kwargs):
        """ADK-compatible wrapper.

        Args:
            **kwargs: Parameters passed to the wrapped function

        Returns:
            Result from the wrapped function
        """
        try:
            # Filter kwargs to match function signature
            sig = inspect.signature(func)
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
            return func(**filtered_kwargs)
        except Exception as e:
            logger.error(f"Error in wrapped tool: {e}")
            return f"Error: {e!s}"

    # Update docstring
    wrapped_tool.__doc__ = f"""{description}

    Wrapped legacy function: {func.__name__}

    Args:
        **kwargs: Parameters for the wrapped function

    Returns:
        Result from the wrapped function
    """

    return wrapped_tool


# ============================================================================
# PATTERN: Async Tool Support
# ============================================================================


async def example_async_tool(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Example async tool for network operations.

    ADK supports async tools for I/O-bound operations.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Response data dictionary
    """
    import asyncio

    import aiohttp

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=timeout) as response:
                return {
                    "status": response.status,
                    "content": await response.text(),
                    "headers": dict(response.headers),
                }
        except asyncio.TimeoutError:
            return {"error": f"Request timed out after {timeout} seconds"}
        except Exception as e:
            return {"error": str(e)}
