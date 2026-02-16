# 166-AA-AUDT: A2A Protocol Alignment Analysis

**Date:** 2025-11-29
**Status:** ✅ Analysis Complete
**Author:** Claude Code
**Protocol Reference:** https://github.com/a2aproject/a2a-python

---

## Executive Summary

Analyzed Bob's Brain AgentCard implementations against the official Agent2Agent (A2A) Protocol specification from a2a-python. Found significant gaps in our current implementation that need addressing for full protocol compliance.

**Key Finding:** Our AgentCards are missing ~60% of required fields from the A2A v0.3.0 specification.

---

## Current State Analysis

### 1. Our Current AgentCard Structure

**Location:** `agents/*/well-known/agent-card.json`
**Format:** Custom simplified schema
**Version:** Not aligned with A2A protocol

**Current Fields:**
```json
{
  "name": "string",
  "version": "string",
  "url": "string",
  "description": "string",
  "capabilities": ["array"],
  "default_input_modes": ["array"],
  "default_output_modes": ["array"],
  "skills": [{
    "skill_id": "string",
    "name": "string",
    "description": "string",
    "input_schema": {},
    "output_schema": {}
  }],
  "spiffe_id": "string"  // Custom field
}
```

### 2. A2A Protocol v0.3.0 Requirements

**Source:** `a2a-python/src/a2a/types.py`
**Protocol Version:** 0.3.0
**Full Specification:** https://a2a-protocol.org

**Required Fields:**
```python
class AgentCard(A2ABaseModel):
    # Core Identity
    name: str
    version: str
    protocol_version: str = "0.3.0"
    description: str

    # Endpoints & Transport
    url: str
    preferred_transport: str = "JSONRPC"
    additional_interfaces: list[AgentInterface]

    # Capabilities & Skills
    capabilities: AgentCapabilities  # Object, not array
    skills: list[AgentSkill]
    default_input_modes: list[str]
    default_output_modes: list[str]

    # Security
    security: list[dict[str, list[str]]]
    security_schemes: dict[str, SecurityScheme]
    signatures: list[AgentCardSignature]

    # Provider & Documentation
    provider: AgentProvider
    documentation_url: str
    icon_url: str

    # Extended Card Support
    supports_authenticated_extended_card: bool
```

---

## Gap Analysis

### Critical Missing Fields (MUST ADD)

| Field | A2A Requirement | Our Status | Impact |
|-------|----------------|------------|---------|
| `protocol_version` | Required ("0.3.0") | ❌ Missing | Cannot validate protocol compliance |
| `preferred_transport` | Required (default: "JSONRPC") | ❌ Missing | Cannot negotiate transport |
| `capabilities` | Object structure | ❌ Using array | Incorrect type structure |
| `skills.id` | Required string | ❌ Using `skill_id` | Non-compliant field name |
| `skills.tags` | Required array | ❌ Missing | Cannot categorize skills |
| `security` | Required for auth | ❌ Missing | No security declaration |
| `provider` | Recommended | ❌ Missing | No provider identification |

### Custom Fields (MUST MIGRATE)

| Our Field | A2A Equivalent | Migration Path |
|-----------|----------------|----------------|
| `spiffe_id` | None (custom extension) | Move to `extensions` or skill metadata |
| `skill_id` | `id` | Rename field |
| `input_schema` | Not in spec | Consider extension or remove |
| `output_schema` | Not in spec | Consider extension or remove |

### Transport & Interface Gaps

**Current:** No transport declaration
**Required:** Must specify transport protocol support

```json
"preferred_transport": "JSONRPC",
"additional_interfaces": [
  {
    "url": "https://api.example.com/a2a/v1",
    "transport": "JSONRPC"
  },
  {
    "url": "https://grpc.example.com/a2a",
    "transport": "GRPC"
  }
]
```

---

## Migration Plan

### Phase 1: Add Required Fields (Backward Compatible)

**Changes:** Add missing required fields while keeping custom fields
**Risk:** Low - additive changes only
**Timeline:** Immediate

```json
{
  // Existing fields...
  "protocol_version": "0.3.0",
  "preferred_transport": "JSONRPC",
  "provider": {
    "organization": "Intent Solutions",
    "url": "https://intent.solutions"
  },
  "security": [],
  "security_schemes": {},
  "documentation_url": "https://github.com/jeremylongshore/bobs-brain",
  "icon_url": null,
  "supports_authenticated_extended_card": false
}
```

### Phase 2: Restructure Skills

**Changes:** Align skill structure with A2A spec
**Risk:** Medium - breaking change for skill consumers
**Timeline:** Next minor version

```json
"skills": [
  {
    "id": "bob.answer_adk_question",  // Renamed from skill_id
    "name": "Answer ADK Question",
    "description": "...",
    "tags": ["adk", "documentation", "support"],  // NEW
    "examples": [  // NEW
      "How do I create an ADK agent?",
      "What is the Agent Engine deployment process?"
    ],
    "input_modes": null,  // Inherit from agent defaults
    "output_modes": null,  // Inherit from agent defaults
    "security": null  // No special security requirements
    // Move input_schema/output_schema to extensions
  }
]
```

### Phase 3: Implement Capabilities Object

**Changes:** Convert capabilities from array to proper object structure
**Risk:** Medium - requires understanding AgentCapabilities schema
**Timeline:** With Phase 2

### Phase 4: Add Security & Signatures

**Changes:** Implement proper security declarations and JWS signatures
**Risk:** High - requires key management and signing infrastructure
**Timeline:** Future enhancement

---

## Implementation Checklist

### Immediate Actions (Phase 1)

- [ ] Add `protocol_version: "0.3.0"` to all AgentCards
- [ ] Add `preferred_transport: "JSONRPC"`
- [ ] Add `provider` object with Intent Solutions info
- [ ] Add empty `security` and `security_schemes` fields
- [ ] Add `documentation_url` pointing to GitHub repo
- [ ] Set `supports_authenticated_extended_card: false`

### Next Release (Phase 2-3)

- [ ] Rename `skill_id` to `id` in all skills
- [ ] Add `tags` array to each skill
- [ ] Add `examples` array with 2-3 examples per skill
- [ ] Convert `capabilities` from array to object
- [ ] Move `spiffe_id` to appropriate extension field
- [ ] Create migration script for schema/output schemas

### Future Enhancements (Phase 4)

- [ ] Implement AgentCardSignature generation
- [ ] Add OAuth2/API key security schemes
- [ ] Support authenticated extended cards
- [ ] Add GRPC transport interface

---

## Testing Requirements

### 1. Validation Tests

```python
# tests/unit/test_a2a_compliance.py
def test_agentcard_a2a_compliance():
    """Validate AgentCards against A2A v0.3.0 schema"""
    from a2a.types import AgentCard

    for agent_dir in Path("agents").iterdir():
        card_path = agent_dir / ".well-known" / "agent-card.json"
        if card_path.exists():
            with open(card_path) as f:
                card_data = json.load(f)

            # Should validate against A2A schema
            card = AgentCard(**card_data)
            assert card.protocol_version == "0.3.0"
```

### 2. A2A Inspector Compatibility

Use official A2A Inspector tool:
```bash
# Install a2a-inspector
git clone https://github.com/a2aproject/a2a-inspector.git

# Validate our AgentCards
a2a-inspector validate agents/bob/.well-known/agent-card.json
```

### 3. Client Compatibility Testing

Test with a2a-python SDK client:
```python
from a2a.client import A2AClient

client = A2AClient(
    url="https://bob.intent.solutions",
    transport="JSONRPC"
)

# Should successfully retrieve and parse AgentCard
card = client.get_agent_card()
assert card.protocol_version == "0.3.0"
```

---

## Dependencies

### Required Libraries

```txt
# requirements.txt additions
a2a-sdk>=0.3.0  # For validation and client testing
pydantic>=2.0    # For model validation
```

### Documentation Updates Needed

1. Update `000-docs/000-DR-STND-agentcards-and-a2a-contracts.md`
2. Create migration guide for existing deployments
3. Update agent deployment scripts
4. Add A2A compliance to CI checks

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing integrations | Medium | High | Phased migration with backward compatibility |
| Schema validation failures | High | Medium | Add validation tests before deployment |
| Security scheme complexity | Low | High | Start with no auth, add incrementally |
| Transport negotiation issues | Low | Medium | Default to JSONRPC initially |

---

## Recommendations

### Immediate (Priority 1)
1. ✅ **Add protocol_version field** - Critical for A2A compliance
2. ✅ **Fix skill.id field naming** - Simple rename, high impact
3. ✅ **Add provider information** - Improves discoverability

### Short-term (Priority 2)
1. ⏳ **Implement full skill structure** - Add tags and examples
2. ⏳ **Convert capabilities to object** - Align with spec
3. ⏳ **Add transport declarations** - Enable protocol negotiation

### Long-term (Priority 3)
1. 🔮 **Implement security schemes** - For production use
2. 🔮 **Add AgentCard signatures** - For authenticity
3. 🔮 **Support extended cards** - For authenticated users

---

## Conclusion

Bob's Brain AgentCards require significant updates to achieve A2A Protocol v0.3.0 compliance. The migration can be done in phases to minimize disruption:

1. **Phase 1** (Immediate): Add missing required fields - **Low risk**
2. **Phase 2** (Next release): Restructure skills and capabilities - **Medium risk**
3. **Phase 3** (Future): Add security and signatures - **Requires infrastructure**

**Recommended Action:** Start with Phase 1 immediately to claim A2A compliance, then iterate through remaining phases based on integration requirements.

---

## Appendix: File Comparison

### Current Bob AgentCard (165 lines)
```json
{
  "name": "bobs-brain",
  "version": "0.11.0",
  "spiffe_id": "spiffe://...",
  // ... simplified structure
}
```

### A2A Compliant AgentCard (250+ lines estimated)
```json
{
  "protocol_version": "0.3.0",
  "name": "bobs-brain",
  "version": "0.11.0",
  "url": "https://bob.intent.solutions",
  "preferred_transport": "JSONRPC",
  "provider": {
    "organization": "Intent Solutions",
    "url": "https://intent.solutions"
  },
  // ... full A2A structure
}
```

---

**Generated:** 2025-11-29
**Repository:** jeremylongshore/bobs-brain
**Analysis Tool:** a2a-python v0.3.0 specification

🤖 Generated with [Claude Code](https://claude.com/claude-code)