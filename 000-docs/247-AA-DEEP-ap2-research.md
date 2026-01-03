# AP2 Research - Deep Dive Analysis

**Document ID:** 247-AA-DEEP-ap2-research
**Date:** 2026-01-02
**Author:** Claude Code
**Status:** COMPLETE
**Beads Story:** bobs-brain-kpe.5

---

## 1. What It Is (Executive Summary)

**Agent Payments Protocol (AP2)** is an open-source framework from Google Cloud for enabling secure, interoperable payments through AI agents. It establishes trust using **Mandates** - tamper-proof, cryptographically-signed digital contracts that serve as verifiable proof of user authorization.

The protocol solves three critical problems for agentic commerce:
- **Authorization**: How to verify a user gave an agent specific authority
- **Authenticity**: How to ensure agent requests reflect true user intent (not hallucinations)
- **Accountability**: Clear liability chain when fraudulent/incorrect transactions occur

Core innovation: **"Verifiable Intent, Not Inferred Action"** - trust anchored to deterministic, non-repudiable cryptographic proof rather than AI inference.

---

## 2. Key Primitives to Implement/Integrate

### 2.1 Three Mandate Types

| Mandate | Purpose | Scenario | Signer |
|---------|---------|----------|--------|
| **Intent Mandate** | Delegate authority with constraints | Human NOT present | Shopping Agent + User |
| **Cart Mandate** | Approve specific cart contents | Human present | Merchant + User |
| **Payment Mandate** | Network visibility, AI presence signals | Payment processing | System |

### 2.2 Intent Mandate Structure

**For delegated tasks (human not present):**

```python
class IntentMandate(BaseModel):
    user_cart_confirmation_required: bool
    natural_language_description: str  # User's intent in plain text
    merchants: Optional[List[str]]     # Allowed merchants
    skus: Optional[List[str]]          # Allowed product SKUs
    requires_refundability: bool
    intent_expiry: str                 # ISO 8601 timestamp
```

**Example Use Case:**
```
Intent Mandate Parameters:
- Task: Book weekend trip
- Locations: Round-trip flight + hotel in Palm Springs
- Dates: First weekend of November
- Budget Constraint: $700 total
- Delegated Authority: Agent can interact with airline, hotel, OTA agents
- Expiry: 2026-01-15T23:59:59Z
```

### 2.3 Cart Mandate Structure

**For real-time purchases (human present):**

```python
class CartMandate(BaseModel):
    contents: CartContents  # Cart ID, payment request, expiry, merchant
    merchant_authorization: str  # Base64url-encoded JWT
    # JWT includes: issuer, audience, timestamps, token ID, cart hash
```

**Key Properties:**
- Merchant-generated, user-signed
- Exact items and prices captured
- Cryptographic signature prevents tampering
- "What you see is what you pay for"

### 2.4 Payment Mandate Structure

```python
class PaymentMandate(BaseModel):
    payment_mandate_contents: PaymentMandateContents
    # Includes: mandate ID, payment details, merchant ID, timestamp
    user_authorization: str  # Base64url-encoded verifiable presentation
    # SD-JWT format with issuer signatures and key-binding
```

### 2.5 Role-Based Architecture

| Role | Responsibility |
|------|----------------|
| **User** | Delegates payment tasks, signs mandates |
| **Shopping Agent** | Builds carts, obtains authorization (Gemini, ChatGPT) |
| **Credentials Provider** | Manages payment credentials securely |
| **Merchant Endpoint** | Negotiates products/prices |
| **Merchant Payment Processor** | Constructs final authorization |
| **Network/Issuer** | Processes payment, risk assessment |

### 2.6 Authorization Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User creates Intent Mandate (delegation with constraints) │
│    - Budget limit: $700                                      │
│    - Allowed merchants: [airline, hotel, OTA]                │
│    - Task: Book weekend trip                                 │
│    - Expiry: 2026-01-15T23:59:59Z                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Shopping Agent processes request                          │
│    - Queries merchant endpoints                              │
│    - Negotiates prices                                       │
│    - Builds cart within budget                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Merchant generates Cart Mandate                           │
│    - Signs cart contents with JWT                            │
│    - Includes exact items, prices, terms                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. User signs Cart Mandate (if confirmation required)        │
│    - Cryptographic approval of specific purchase             │
│    - Non-repudiable proof of intent                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Payment Mandate sent to network                           │
│    - AI presence signals (human present/not present)         │
│    - Enables risk scoring by issuer                          │
│    - Complete audit trail                                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.7 Cryptographic Requirements

| Requirement | Implementation |
|-------------|----------------|
| **Signature Algorithm** | ECDSA (Elliptic Curve Digital Signature Algorithm) |
| **Credential Format** | W3C Verifiable Credentials (VCs) |
| **Token Format** | SD-JWT (Selective Disclosure JWT) |
| **Key Management** | Hardware-backed key storage recommended |
| **Encoding** | Base64url for all signatures |

---

## 3. Minimum Interface Contract

### Intent Mandate (Pydantic Schema)

```python
from pydantic import BaseModel
from typing import Optional, List

class IntentMandate(BaseModel):
    """User's delegated purchase authority."""
    user_cart_confirmation_required: bool
    natural_language_description: str
    merchants: Optional[List[str]] = None
    skus: Optional[List[str]] = None
    requires_refundability: bool = True
    intent_expiry: str  # ISO 8601
```

### Cart Mandate (Pydantic Schema)

```python
class CartContents(BaseModel):
    cart_id: str
    payment_request: dict
    expiry: str
    merchant_name: str

class CartMandate(BaseModel):
    """Merchant-signed, user-approved cart."""
    contents: CartContents
    merchant_authorization: str  # Base64url JWT
```

### Bob Integration Contract

```python
class BobBudgetMandate(BaseModel):
    """Adapted AP2 Intent Mandate for non-payment authorization."""
    task_description: str           # Natural language task
    authorized_operations: List[str]  # ["github_issue", "cloud_api"]
    budget_limit: Optional[float]   # API cost limit in USD
    repo_scope: List[str]           # Authorized repositories
    time_limit: str                 # ISO 8601 expiry
    requires_human_approval: bool   # For high-impact actions
```

---

## 4. Risks / Failure Modes / Anti-Patterns

### 4.1 Mandate Spoofing

Agent creates fake mandates without user authorization.

**Mitigation:**
- Hardware-backed key management
- Decentralized allowlists for authorized agents
- Cryptographic verification at every step

### 4.2 Agent Coercion

Malicious actor manipulates agent to exceed mandate bounds.

**Mitigation:**
- Intent Mandate TTL (time-to-live) expiration
- Explicit scope constraints (merchants, SKUs, budget)
- Human approval checkpoints for high-value actions

### 4.3 Hallucination Risk

Agent misinterprets user intent, takes wrong actions.

**Mitigation:**
- `natural_language_description` captures exact user words
- Cart Mandate requires explicit user signature on final cart
- "What you see is what you pay for" principle

### 4.4 Budget Overrun

Agent exceeds authorized spending.

**Mitigation:**
- `budget_limit` field in Intent Mandate
- Real-time budget tracking
- Hard stop when limit approached

### 4.5 Replay Attacks

Old mandate reused for unauthorized transactions.

**Mitigation:**
- `intent_expiry` / `expiry` fields
- Unique mandate IDs
- Nonce tracking

---

## 5. What to Copy vs Adapt

### Copy for Bob's Authorization Pattern

| AP2 Concept | Bob Adaptation |
|-------------|----------------|
| **Intent Mandate** | Task authorization with constraints |
| **Budget limit** | API cost limit per task |
| **Merchant scope** | Repository/operation scope |
| **Expiry** | Task timeout |
| **Natural language description** | User's original request |

### Adapt for Non-Payment Use Cases

| AP2 (Payments) | Bob (Operations) |
|----------------|------------------|
| `merchants: []` | `repos: []` (authorized repos) |
| `skus: []` | `operations: []` (authorized actions) |
| `budget: $700` | `api_budget: $50` (API cost limit) |
| `user_cart_confirmation` | `human_approval_required` |
| Cart Mandate | Fix Approval Gate |

### New Patterns for Bob

**1. Operation Mandate (Bob's Intent Mandate):**
```python
class OperationMandate(BaseModel):
    """User's delegated authority for Bob operations."""
    task_description: str
    authorized_repos: List[str]
    authorized_operations: List[str]  # ["audit", "fix", "issue"]
    api_cost_limit: float  # USD
    human_approval_threshold: float  # Actions above this need approval
    expiry: datetime
    created_at: datetime
    user_signature: str  # Cryptographic proof
```

**2. Fix Approval Mandate (Bob's Cart Mandate):**
```python
class FixApprovalMandate(BaseModel):
    """User approval for specific fix implementation."""
    fix_plan_id: str
    files_to_modify: List[str]
    estimated_changes: int
    tests_to_run: List[str]
    user_approval_signature: str
    approved_at: datetime
```

**3. Budget Tracking:**
```python
class BudgetTracker(BaseModel):
    """Real-time budget monitoring."""
    mandate_id: str
    budget_limit: float
    spent: float
    remaining: float
    operations: List[dict]  # Audit trail
```

---

## 6. Integration Notes for Bob

### 6.1 Mandate Pattern for Autonomous Operations

**User Request:**
```
"Audit all my ADK repos and fix any R1-R8 violations. Budget: $100."
```

**Bob creates Operation Mandate:**
```python
operation_mandate = OperationMandate(
    task_description="Audit all ADK repos, fix R1-R8 violations",
    authorized_repos=["bobs-brain", "iam-senior-adk", "iam-adk"],
    authorized_operations=["audit", "fix-plan", "fix-impl", "qa"],
    api_cost_limit=100.0,
    human_approval_threshold=25.0,  # Fixes over $25 need approval
    expiry=datetime.now() + timedelta(hours=24),
    user_signature=sign_with_user_key(mandate)
)
```

### 6.2 Budget-Aware Orchestration

**Foreman tracks budget:**
```python
class ForemanWithBudget:
    def execute_with_budget(self, mandate, task):
        if self.budget_tracker.remaining < estimated_cost(task):
            return {"status": "BUDGET_EXHAUSTED", "remaining": 0}

        result = self.invoke_specialist(task)

        self.budget_tracker.record(
            operation=task.type,
            cost=actual_cost(result),
            specialist=task.specialist
        )

        return result
```

### 6.3 Human Approval Gates

**High-impact operations require approval:**
```python
if fix_plan.estimated_cost > mandate.human_approval_threshold:
    # Send to Slack for approval
    approval_request = FixApprovalMandate(
        fix_plan_id=fix_plan.id,
        files_to_modify=fix_plan.files,
        estimated_changes=fix_plan.lines_changed,
        tests_to_run=fix_plan.tests
    )

    # Wait for user signature
    user_approval = await slack_approval_flow(approval_request)

    if not user_approval.approved:
        return {"status": "APPROVAL_DENIED"}
```

### 6.4 R1-R8 Compliance

| Rule | AP2 Impact |
|------|------------|
| R1 (ADK-only) | AP2 is pattern, not dependency |
| R2 (Agent Engine) | Mandates stored in session/memory |
| R3 (Gateway) | Approval flows go through Slack gateway |
| R4 (CI-only) | Mandate creation in production only |
| R5 (Memory) | Mandate audit trail in Memory Bank |

### 6.5 Audit Trail Pattern

**Every operation recorded:**
```python
class OperationAuditEntry(BaseModel):
    """AP2-style audit trail for Bob operations."""
    mandate_id: str
    operation_type: str
    specialist: str
    input_hash: str
    output_hash: str
    cost: float
    timestamp: datetime
    human_present: bool
    success: bool
```

---

## 7. Open Questions

1. **Cryptographic signing in Agent Engine?**
   - Need key management strategy for Vertex
   - Hardware-backed keys not available in serverless

2. **Slack approval as signature?**
   - Slack message approval = user signature?
   - Need cryptographic equivalence or just trust?

3. **Budget tracking persistence?**
   - Session memory vs Memory Bank?
   - Real-time vs batch tracking?

4. **Multi-mandate coordination?**
   - User has multiple active mandates
   - How to select appropriate mandate per task?

5. **Mandate revocation?**
   - User cancels mandate mid-task
   - Graceful termination pattern

---

## 8. References

### External
- **Official Site**: https://ap2-protocol.org/
- **GitHub**: https://github.com/google-agentic-commerce/AP2
- **Announcement**: https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol
- **Security Framework**: https://cloudsecurityalliance.org/blog/2025/10/06/secure-use-of-the-agent-payments-protocol-ap2-a-framework-for-trustworthy-ai-driven-transactions

### Ecosystem
- **A2A x402** (Crypto): https://github.com/google-a2a/a2a-x402
- **60+ Partners**: Mastercard, PayPal, Coinbase, Shopify, Cloudflare

### Technologies
- **ADK**: Agent Development Kit (samples use Gemini 2.5 Flash)
- **VCs**: W3C Verifiable Credentials
- **SD-JWT**: Selective Disclosure JWT format

---

## 9. Key Takeaways for Bob Orchestrator

1. **Mandate pattern is universal** - Works for payments AND non-payment authorization
2. **Intent Mandate = Delegated authority with constraints** - Budget, scope, expiry
3. **Cart Mandate = Specific approval checkpoint** - "What you see is what you pay for"
4. **Budget tracking is essential** - Real-time monitoring, hard stops
5. **Audit trail is non-negotiable** - Every operation recorded
6. **Human approval gates** - High-impact actions need explicit signature
7. **Cryptographic trust optional** - Can start with trust-based, add crypto later

**User Decision:** Full mandate pattern for any authorized operations.

**Next Step:** Create Bob Brain Baseline document, then Synthesis.
