# Bob's MCP Server

MCP server for Bob's Brain agents. Provides tools for repository operations.

## Tools

| Tool | Description |
|------|-------------|
| `search_codebase` | Search for code patterns |
| `get_file` | Read file contents |
| `analyze_dependencies` | Parse dependency files |
| `check_patterns` | Validate against Hard Mode rules |

## Architecture

```
bobs-brain/
├── agents/    → Agent Engine
├── service/   → Slack gateway (Cloud Run)
└── mcp/       → This MCP server (Cloud Run)
```

## Development

```bash
cd mcp/
pip install -r requirements.txt
ALLOW_LOCAL_DEV=true python -m src.server
```

## API

- `GET /health` - Health check
- `GET /tools` - List available tools
- `POST /tools/{name}` - Invoke a tool
