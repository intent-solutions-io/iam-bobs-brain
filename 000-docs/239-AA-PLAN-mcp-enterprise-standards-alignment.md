# 239-AA-PLAN-mcp-enterprise-standards-alignment.md

**Document Type:** Implementation Plan
**Status:** Approved
**Created:** 2025-12-20
**Author:** CTO (via Claude Code audit)

---

## Executive Summary

Following a comprehensive audit of Google's official MCP repository (https://github.com/google/mcp) by four specialist agents, this plan outlines the path forward for ensuring Bob's Brain meets enterprise standards while maintaining compatibility with the broader MCP ecosystem.

**Key Finding:** Bob's Brain is already MORE enterprise-ready than Google's MCP examples (9/10 vs 3/10). Our Hard Mode rules (R1-R8) provide stricter guarantees. This plan focuses on selective enhancements, not wholesale adoption.

---

## Audit Summary

### Agent Reports

| Agent | Scope | Key Finding |
|-------|-------|-------------|
| ADK Pattern Auditor | R1-R8 alignment | 30% aligned - Google prioritizes flexibility, we prioritize strictness (correct) |
| Security Auditor | Auth, transport, IAM | Security gaps: OAuth 2.1, WIF, Origin validation needed |
| Architect Reviewer | Enterprise readiness | Bob's Brain 9/10, Google MCP 3/10 - we're ahead |
| Code Reviewer | Patterns, testing | FastMCP patterns valuable, our lazy-loading superior |

### Strategic Position

```
                    FLEXIBILITY
                         ↑
                         │
    Google MCP ──────────┼──────────── Bob's Brain
    (demo-grade)         │             (enterprise-grade)
                         │
                         │
                    STRICTNESS
                         ↓
```

**Conclusion:** Bob's Brain occupies the correct position for enterprise deployments. Google MCP is designed for broad adoption and demos, not production governance.

---

## Implementation Phases

### Phase A: Security Hardening (P1 - Critical)

**Objective:** Close security gaps identified by Security Auditor

#### A.1: Enable Workload Identity Federation

**Current State:** WIF resources commented out in `infra/terraform/iam.tf`
**Target State:** WIF enabled for all environments

```hcl
# UNCOMMENT in infra/terraform/iam.tf
resource "google_iam_workload_identity_pool" "github_actions" { ... }
resource "google_iam_workload_identity_pool_provider" "github_actions" { ... }
resource "google_service_account_iam_member" "github_actions_wif" { ... }
```

**Files:**
- `infra/terraform/iam.tf` - Uncomment WIF resources
- `infra/terraform/envs/dev/terraform.tfvars` - Add pool/provider IDs
- `.github/workflows/*.yml` - Update to use WIF

#### A.2: Add Origin Validation Middleware

**Current State:** No DNS rebinding protection
**Target State:** Origin validation for all MCP endpoints

```python
# mcp/src/auth/origin_validator.py
ALLOWED_ORIGINS = [
    "https://agent.googleapis.com",
    "https://bob.intent.solutions",
    os.getenv("ALLOWED_ORIGIN", ""),
]

@app.middleware("http")
async def validate_origin(request: Request, call_next):
    origin = request.headers.get("Origin")
    if origin and origin not in ALLOWED_ORIGINS:
        logger.warning(f"DNS rebinding blocked: {origin}")
        return JSONResponse(status_code=403, content={"error": "Invalid origin"})
    return await call_next(request)
```

**Files:**
- `mcp/src/auth/origin_validator.py` - New file
- `mcp/src/server.py` - Add middleware
- `mcp/tests/unit/test_origin_validation.py` - Tests

#### A.3: Add Protected Resource Metadata Endpoint

**MCP Spec Requirement:** RFC 9728 compliance

```python
# mcp/src/server.py
@app.get("/.well-known/oauth-protected-resource")
async def resource_metadata():
    return {
        "resource": os.getenv("MCP_SERVER_URL", "https://bobs-mcp.run.app"),
        "authorization_servers": ["https://accounts.google.com"],
        "bearer_methods_supported": ["header"],
        "resource_documentation": "https://github.com/intent-solutions-io/bobs-brain"
    }
```

**Files:**
- `mcp/src/server.py` - Add endpoint

---

### Phase B: MCP Spec Compliance (P2 - High)

**Objective:** Align with MCP specification 2025-06-18

#### B.1: OAuth 2.1 Token Validation

**Current State:** Basic header-based identity validation
**Target State:** Full OAuth 2.1 with audience validation

```python
# mcp/src/auth/oauth_validator.py
from google.auth import jwt
from google.auth.transport import requests

async def validate_oauth_token(request: Request) -> dict:
    """Validate OAuth 2.1 Bearer token per MCP spec."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")

    token = auth_header.split(" ", 1)[1]

    # Decode and validate
    try:
        claims = jwt.decode(token, request=requests.Request())

        # MUST verify audience (MCP spec requirement)
        expected_aud = os.getenv("MCP_SERVER_AUDIENCE")
        if claims.get("aud") != expected_aud:
            raise HTTPException(401, "Token not issued for this server")

        return claims
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        raise HTTPException(401, "Invalid token")
```

**Files:**
- `mcp/src/auth/oauth_validator.py` - New file
- `mcp/src/auth/validator.py` - Integrate OAuth
- `mcp/tests/unit/test_oauth.py` - Tests

#### B.2: Secure Session ID Generation

**Current State:** User/channel concatenation
**Target State:** Cryptographically bound session IDs

```python
# mcp/src/session.py
import secrets
import hashlib

def create_secure_session_id(user_id: str, channel_id: str) -> str:
    """Create cryptographically bound session ID per MCP spec."""
    random_component = secrets.token_urlsafe(32)
    binding = hashlib.sha256(f"{user_id}:{channel_id}".encode()).hexdigest()[:16]
    return f"{binding}:{random_component}"
```

**Files:**
- `mcp/src/session.py` - New file
- `service/slack_webhook/main.py` - Use secure sessions

---

### Phase C: Testing Infrastructure (P2 - High)

**Objective:** Adopt Google's multi-version testing patterns

#### C.1: Add Nox for Multi-Version Testing

```python
# noxfile.py
import nox

@nox.session(python=["3.10", "3.11", "3.12", "3.13"])
def tests(session):
    """Run tests across Python versions."""
    session.install("-r", "requirements.txt")
    session.install("pytest", "pytest-cov", "pytest-asyncio")
    session.run("pytest", "--cov=agents", "--cov=mcp", "-v")

@nox.session
def lint(session):
    """Check code formatting."""
    session.install("ruff", "black")
    session.run("ruff", "check", ".")
    session.run("black", "--check", "--line-length", "100", ".")

@nox.session
def typecheck(session):
    """Run type checking."""
    session.install("mypy", "-r", "requirements.txt")
    session.run("mypy", "agents/", "mcp/")
```

**Files:**
- `noxfile.py` - New file
- `.github/workflows/ci.yml` - Add Nox jobs

#### C.2: Add Pydantic Structured Outputs

```python
# agents/shared_contracts/compliance.py
from pydantic import BaseModel, Field
from typing import List

class ComplianceResult(BaseModel):
    """ADK compliance check result."""
    agent_name: str = Field(description="Agent under review")
    compliance_status: str = Field(description="COMPLIANT | VIOLATIONS | ERROR")
    violations: List[str] = Field(default_factory=list)
    risk_level: str = Field(description="HIGH | MEDIUM | LOW")
    rules_checked: List[str] = Field(default_factory=list)

class ToolInvocationResult(BaseModel):
    """Standardized tool result."""
    success: bool
    data: dict = Field(default_factory=dict)
    error: str | None = None
    metadata: dict = Field(default_factory=dict)
```

**Files:**
- `agents/shared_contracts/compliance.py` - New file
- `mcp/src/tools/*.py` - Use Pydantic models

---

### Phase D: Code Pattern Improvements (P3 - Medium)

**Objective:** Adopt valuable patterns from Google's implementations

#### D.1: Async Pagination Pattern

```python
# agents/shared_tools/utils.py
async def paginate_async(pager) -> List[dict]:
    """Async pagination for API responses."""
    return [item async for item in pager]
```

#### D.2: Flexible Input Types

```python
# mcp/src/tools/get_file.py
async def execute(path: str | Path, encoding: str = "utf-8") -> dict:
    """Get file contents.

    Args:
        path: File path. Accepts:
            - String: "/path/to/file"
            - Path object: Path("/path/to/file")
        encoding: File encoding (default: utf-8)
    """
    normalized_path = Path(path) if isinstance(path, str) else path
    ...
```

#### D.3: Progress Reporting for Long-Running Tools

```python
# mcp/src/tools/check_patterns.py
async def execute(path: str, rules: List[str], ctx: Context = None) -> dict:
    """Check Hard Mode compliance with progress reporting."""
    if ctx:
        await ctx.report_progress(progress=0, total=100)

    results = []
    for i, rule in enumerate(rules):
        result = await check_rule(rule, path)
        results.append(result)

        if ctx:
            progress = int((i + 1) / len(rules) * 100)
            await ctx.report_progress(progress=progress, total=100)
            await ctx.info(f"Checked {rule}: {result['status']}")

    return {"results": results}
```

---

### Phase E: Documentation & Governance (P3 - Medium)

**Objective:** Document patterns for future portfolio reuse

#### E.1: Create MCP Integration Guide

**File:** `000-docs/240-DR-STND-mcp-integration-patterns.md`

Contents:
- When to use MCP vs ADK tools
- Security requirements (OAuth 2.1, Origin validation)
- Testing patterns (Nox, multi-version)
- Deployment patterns (Cloud Run, feature flags)

#### E.2: Update Hard Mode Rules

**File:** `000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md`

Add:
- R9: MCP Security - OAuth 2.1 required for external MCP endpoints
- R10: Origin Validation - DNS rebinding protection required

---

## Implementation Timeline

| Phase | Priority | Scope | Effort |
|-------|----------|-------|--------|
| A.1 | P1 | Enable WIF | 2 hours |
| A.2 | P1 | Origin validation | 2 hours |
| A.3 | P1 | Resource metadata | 1 hour |
| B.1 | P2 | OAuth 2.1 | 4 hours |
| B.2 | P2 | Secure sessions | 2 hours |
| C.1 | P2 | Nox testing | 2 hours |
| C.2 | P2 | Pydantic outputs | 3 hours |
| D.1-3 | P3 | Code patterns | 4 hours |
| E.1-2 | P3 | Documentation | 3 hours |

**Total Estimated Effort:** 23 hours across phases

---

## Success Criteria

### Phase A Complete When:
- [ ] WIF enabled and tested in dev environment
- [ ] Origin validation middleware deployed
- [ ] `/.well-known/oauth-protected-resource` returns valid metadata
- [ ] All MCP unit tests pass

### Phase B Complete When:
- [ ] OAuth 2.1 token validation working
- [ ] Secure session IDs in use
- [ ] MCP spec 2025-06-18 compliance verified

### Phase C Complete When:
- [ ] Nox runs tests on Python 3.10-3.13
- [ ] Pydantic models for all tool outputs
- [ ] CI pipeline includes Nox jobs

### Phase D Complete When:
- [ ] Async pagination in shared_tools
- [ ] Flexible input types documented
- [ ] Progress reporting for long tools

### Phase E Complete When:
- [ ] MCP Integration Guide published
- [ ] Hard Mode R9/R10 documented
- [ ] Portfolio teams can follow patterns

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| OAuth 2.1 complexity | Medium | Use google-auth library, not custom |
| WIF configuration errors | High | Test in dev first, rollback plan |
| Breaking changes to MCP auth | Medium | Feature flag for OAuth (fallback to current) |
| Multi-version Python issues | Low | Nox isolates environments |

---

## Appendix: Patterns NOT Adopted

| Pattern | Source | Reason for Rejection |
|---------|--------|---------------------|
| Import-time side effects | Google Analytics MCP | Violates 6767-LAZY |
| Manual gcloud deploys | Google MCP docs | Violates R4 |
| Cloud Run as app runtime | Google MCP | Violates R3 |
| 80-char line length | Google style | Too restrictive |
| unittest over pytest | Google Analytics | pytest is more modern |

---

## References

- Google MCP Repository: https://github.com/google/mcp
- MCP Specification 2025-06-18: https://modelcontextprotocol.io/specification/2025-06-18/
- Bob's Brain Hard Mode: `000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md`
- API Registry Architecture: `000-docs/237-AT-ARCH-apiregistry-cloud-tool-governance.md`

---

## Approval

**CTO Decision:** APPROVED

This plan preserves Bob's Brain's enterprise advantages while selectively adopting security and testing patterns from the broader MCP ecosystem. Hard Mode rules R1-R8 remain non-negotiable.

**Next Step:** Begin Phase A (Security Hardening)
