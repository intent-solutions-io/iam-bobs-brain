# 238-AT-ARCH-mcp-server-cloudrun-implementation.md

**Document Type:** Architecture Design
**Status:** Proposed
**Created:** 2025-12-20
**Author:** Claude Code (Build Captain)

---

## The Question

How do we implement MCP servers on Cloud Run while maintaining Hard Mode rules (R1-R8) and ARV (Agent Readiness Verification)?

---

## The Challenge

MCP servers are **separate infrastructure** from agents. They:
- Run on Cloud Run (not Agent Engine)
- Have their own repos
- Deploy independently

But they still need to follow Bob's Brain quality standards:
- Can't just deploy anything
- Need testing, validation, governance
- Must integrate with the existing ARV gates

---

## Hard Mode Rules Applied to MCP Servers

| Rule | Applies? | How |
|------|----------|-----|
| **R1: ADK-Only** | **Partially** | MCP server uses MCP protocol (not ADK). But it serves ADK agents. The *client* (agent) uses ADK. |
| **R2: Agent Engine** | **No** | MCP servers run on Cloud Run, not Agent Engine. This is correct - they're infrastructure, not agents. |
| **R3: Gateway Separation** | **Yes** | MCP servers ARE gateways. They sit between agents and external systems. Cloud Run is the right place. |
| **R4: CI-Only Deployments** | **Yes** | MCP servers deploy via Terraform + GitHub Actions. No manual deploys. |
| **R5: Dual Memory** | **No** | MCP servers are stateless. Session/memory is in agents. |
| **R6: Single Docs** | **Partially** | Each MCP repo has its own docs. Cross-reference back to bobs-brain patterns. |
| **R7: SPIFFE ID** | **Yes** | MCP servers validate caller identity via headers. Propagate SPIFFE in logs. |
| **R8: Drift Detection** | **Yes** | MCP servers have their own drift checks (no forbidden imports, etc.) |

**Key insight:** R1/R2 don't apply directly because MCP servers are **infrastructure**, not agents. But R3/R4/R7/R8 absolutely apply.

---

## MCP Server Structure (Template)

```
mcp-<name>/                          # e.g., mcp-repo-ops
├── .github/
│   └── workflows/
│       ├── ci.yml                   # Tests, lint, drift check
│       └── deploy.yml               # Terraform apply on merge
│
├── src/
│   ├── server.py                    # MCP server entrypoint
│   ├── tools/                       # Tool implementations
│   │   ├── __init__.py
│   │   ├── search_codebase.py
│   │   └── get_file.py
│   └── auth/
│       └── validator.py             # R7: Validate caller identity
│
├── tests/
│   ├── unit/
│   │   ├── test_tools.py
│   │   └── test_auth.py
│   └── integration/
│       └── test_server.py
│
├── terraform/
│   ├── main.tf                      # Cloud Run + Registry
│   ├── variables.tf
│   └── outputs.tf
│
├── scripts/
│   ├── check_drift.sh               # R8: No forbidden imports
│   └── arv_check.sh                 # Pre-deploy validation
│
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## The MCP Server Implementation

### server.py - Entrypoint

```python
"""
MCP Server: mcp-repo-ops

Provides repository operation tools for Bob's Brain agents.
Accessed via Cloud API Registry.

R3: This is a gateway - runs on Cloud Run, not Agent Engine.
R4: Deployed via Terraform, triggered by GitHub Actions.
R7: Validates caller identity before processing requests.
"""

import logging
from mcp.server import MCPServer
from mcp.types import Tool, TextContent

from src.tools import search_codebase, get_file, analyze_deps
from src.auth import validate_request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_server() -> MCPServer:
    """Create and configure the MCP server."""
    server = MCPServer("mcp-repo-ops")

    # Register tools
    @server.tool("search_codebase")
    async def handle_search(query: str, path: str = ".") -> list[TextContent]:
        """Search repository for code patterns."""
        results = await search_codebase.execute(query, path)
        return [TextContent(type="text", text=result) for result in results]

    @server.tool("get_file")
    async def handle_get_file(path: str) -> TextContent:
        """Get contents of a file."""
        content = await get_file.execute(path)
        return TextContent(type="text", text=content)

    @server.tool("analyze_dependencies")
    async def handle_deps(path: str = ".") -> TextContent:
        """Analyze project dependencies."""
        analysis = await analyze_deps.execute(path)
        return TextContent(type="text", text=analysis)

    return server


# For Cloud Run
server = create_server()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(server.app, host="0.0.0.0", port=8080)
```

### auth/validator.py - R7 Compliance

```python
"""
Request validation for MCP server.

R7: SPIFFE ID propagation - validate caller identity.
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

# Allowed caller identities (service accounts)
ALLOWED_CALLERS = [
    "bob-agent@PROJECT_ID.iam.gserviceaccount.com",
    "iam-adk-agent@PROJECT_ID.iam.gserviceaccount.com",
    # Add more as needed
]


async def validate_request(request: Request) -> str:
    """
    Validate the incoming request and extract caller identity.

    R7: Every request must have valid identity.
    Log the SPIFFE ID for audit trail.

    Returns:
        Caller identity string

    Raises:
        HTTPException if not authorized
    """
    # Get identity from header (set by API Registry or Cloud Run)
    caller_identity = request.headers.get("X-Goog-Authenticated-User-Email")

    if not caller_identity:
        # Check for service account identity
        caller_identity = request.headers.get("X-Serverless-Authorization")

    if not caller_identity:
        logger.warning("Request with no identity - rejecting")
        raise HTTPException(status_code=401, detail="No caller identity")

    # Validate against allowlist
    if not _is_allowed(caller_identity):
        logger.warning(f"Unauthorized caller: {caller_identity}")
        raise HTTPException(status_code=403, detail="Not authorized")

    # R7: Log the identity
    logger.info(f"Authorized request from: {caller_identity}")

    return caller_identity


def _is_allowed(identity: str) -> bool:
    """Check if caller is in allowlist."""
    for allowed in ALLOWED_CALLERS:
        if allowed in identity:
            return True
    return False
```

---

## CI/CD Pipeline (R4 Compliant)

### .github/workflows/ci.yml

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install ruff mypy
      - run: ruff check src/
      - run: mypy src/

  drift-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: R8 - Check for forbidden imports
        run: bash scripts/check_drift.sh

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio
      - run: pytest tests/unit/ -v

  arv-check:
    runs-on: ubuntu-latest
    needs: [lint, drift-check, test]
    steps:
      - uses: actions/checkout@v4
      - name: ARV Gate - Pre-deploy validation
        run: bash scripts/arv_check.sh
```

### .github/workflows/deploy.yml

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write  # For WIF

    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SA }}

      - uses: google-github-actions/setup-gcloud@v2

      # Build and push to Artifact Registry
      - name: Build container
        run: |
          gcloud builds submit \
            --tag gcr.io/${{ secrets.PROJECT_ID }}/mcp-repo-ops:${{ github.sha }}

      # Deploy via Terraform (R4 compliant)
      - uses: hashicorp/setup-terraform@v3
      - name: Terraform Init
        working-directory: terraform/
        run: terraform init

      - name: Terraform Apply
        working-directory: terraform/
        run: |
          terraform apply -auto-approve \
            -var="project_id=${{ secrets.PROJECT_ID }}" \
            -var="image_tag=${{ github.sha }}"
```

---

## Drift Detection (R8)

### scripts/check_drift.sh

```bash
#!/usr/bin/env bash
# R8: Drift detection for MCP server

set -e

echo "=== R8: Drift Detection for MCP Server ==="

# Forbidden imports (anti-patterns)
FORBIDDEN=(
    "langchain"
    "crewai"
    "autogen"
    "openai"  # Use Vertex AI
)

VIOLATIONS=0

for pattern in "${FORBIDDEN[@]}"; do
    echo "Checking for: $pattern"
    if grep -r "$pattern" src/ --include="*.py" 2>/dev/null; then
        echo "VIOLATION: Found $pattern in src/"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

# Check for hardcoded secrets
if grep -rE "(password|secret|api_key)\s*=" src/ --include="*.py" 2>/dev/null; then
    echo "VIOLATION: Possible hardcoded secrets"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

if [ $VIOLATIONS -gt 0 ]; then
    echo "FAILED: $VIOLATIONS drift violations found"
    exit 1
fi

echo "PASSED: No drift violations"
```

---

## ARV Gate for MCP Servers

### scripts/arv_check.sh

```bash
#!/usr/bin/env bash
# ARV (Agent Readiness Verification) for MCP Server

set -e

echo "=== ARV Gate: MCP Server Readiness ==="

CHECKS_PASSED=0
CHECKS_TOTAL=0

# Check 1: Dockerfile exists and is valid
echo "Check 1: Dockerfile validation"
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if [ -f "Dockerfile" ]; then
    # Basic Dockerfile lint
    if grep -q "FROM python" Dockerfile && grep -q "EXPOSE 8080" Dockerfile; then
        echo "  ✅ Dockerfile valid"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo "  ❌ Dockerfile missing required directives"
    fi
else
    echo "  ❌ Dockerfile not found"
fi

# Check 2: R7 - Auth validator exists
echo "Check 2: R7 - Auth validator"
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if [ -f "src/auth/validator.py" ]; then
    if grep -q "validate_request" src/auth/validator.py; then
        echo "  ✅ Auth validator present"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo "  ❌ Auth validator missing validate_request"
    fi
else
    echo "  ❌ src/auth/validator.py not found"
fi

# Check 3: Terraform exists
echo "Check 3: Terraform configuration"
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if [ -f "terraform/main.tf" ]; then
    if grep -q "google_cloud_run" terraform/main.tf; then
        echo "  ✅ Terraform Cloud Run config present"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo "  ❌ Terraform missing Cloud Run resource"
    fi
else
    echo "  ❌ terraform/main.tf not found"
fi

# Check 4: Tests exist
echo "Check 4: Test coverage"
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if [ -d "tests/unit" ] && [ "$(ls -A tests/unit/)" ]; then
    echo "  ✅ Unit tests present"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo "  ❌ No unit tests found"
fi

# Check 5: README with tool documentation
echo "Check 5: Tool documentation"
CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
if [ -f "README.md" ]; then
    if grep -q "## Tools" README.md || grep -q "## API" README.md; then
        echo "  ✅ Tool documentation present"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo "  ❌ README missing tool documentation"
    fi
else
    echo "  ❌ README.md not found"
fi

# Summary
echo ""
echo "=== ARV Summary ==="
echo "Checks passed: $CHECKS_PASSED / $CHECKS_TOTAL"

if [ $CHECKS_PASSED -eq $CHECKS_TOTAL ]; then
    echo "✅ ARV PASSED - Ready to deploy"
    exit 0
else
    echo "❌ ARV FAILED - Fix issues before deploy"
    exit 1
fi
```

---

## Terraform Configuration (R4)

### terraform/main.tf

```hcl
# MCP Server: mcp-repo-ops
# R4: All infrastructure via Terraform, deployed by CI

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "bobs-brain-terraform-state"
    prefix = "mcp-repo-ops"
  }
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "image_tag" {
  type = string
}

# Service account for the MCP server
resource "google_service_account" "mcp_server" {
  project      = var.project_id
  account_id   = "mcp-repo-ops"
  display_name = "MCP Repo Ops Server"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "mcp_server" {
  name     = "mcp-repo-ops"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.mcp_server.email

    containers {
      image = "gcr.io/${var.project_id}/mcp-repo-ops:${var.image_tag}"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      # R7: Pass project info for identity validation
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
    }

    scaling {
      min_instance_count = 0  # Scale to zero when not in use
      max_instance_count = 10
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# IAM: Allow API Registry to invoke this service
resource "google_cloud_run_v2_service_iam_member" "registry_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.mcp_server.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:api-registry@${var.project_id}.iam.gserviceaccount.com"
}

# Register in API Registry (when available)
# resource "google_vertex_ai_mcp_server" "repo_ops" {
#   project  = var.project_id
#   location = "global"
#
#   display_name = "mcp-repo-ops"
#   description  = "Repository operations for Bob's Brain agents"
#
#   server_config {
#     cloud_run_service = google_cloud_run_v2_service.mcp_server.uri
#   }
# }

output "service_url" {
  value = google_cloud_run_v2_service.mcp_server.uri
}
```

---

## Summary: MCP Server Hard Mode Checklist

Before deploying any MCP server, verify:

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| R4: CI deploys only | Check `.github/workflows/deploy.yml` | Uses Terraform, WIF auth |
| R7: Auth validator | `grep validate_request src/auth/` | Function exists |
| R8: No drift | `bash scripts/check_drift.sh` | Exit 0 |
| ARV: Ready to deploy | `bash scripts/arv_check.sh` | All checks pass |
| Tests: Coverage | `pytest tests/unit/ -v` | All tests pass |
| Terraform: Valid | `terraform validate` | Valid config |

---

## Creating a New MCP Server

1. **Clone template** (we'll create one in `intent-solutions-io/mcp-server-template`)
2. **Rename and customize** tools in `src/tools/`
3. **Update ALLOWED_CALLERS** in `src/auth/validator.py`
4. **Update Terraform** service name
5. **Push to new repo** under `intent-solutions-io/`
6. **Configure secrets** (WIF_PROVIDER, WIF_SA, PROJECT_ID)
7. **Merge to main** → Auto deploys via CI

---

## References

- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- Bob's Brain Hard Mode: `000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md`
- API Registry Architecture: `000-docs/237-AT-ARCH-apiregistry-cloud-tool-governance.md`
