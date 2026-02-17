"""
Legacy tool with outdated patterns.
"""

import requests


# VIOLATION: Not using ADK Tool class
def search_database(query: str) -> str:
    """Search the database."""
    # VIOLATION: Direct HTTP call without proper error handling
    response = requests.get(f"http://api.example.com/search?q={query}")

    # VIOLATION: No validation or sanitization
    return response.text

# VIOLATION: Synchronous tool instead of async
def process_data(data: dict) -> dict:
    """Process data synchronously."""
    # VIOLATION: No input validation
    result = {}
    for key, value in data.items():
        # VIOLATION: Potential security issue - eval
        if isinstance(value, str) and value.startswith("eval:"):
            result[key] = eval(value[5:])  # Security violation!
        else:
            result[key] = value
    return result

# VIOLATION: Global state
CACHE = {}

def cached_operation(key: str, value: str = None):
    """Operation with global state."""
    global CACHE  # VIOLATION: Global mutable state

    if value:
        CACHE[key] = value

    return CACHE.get(key, "Not found")
