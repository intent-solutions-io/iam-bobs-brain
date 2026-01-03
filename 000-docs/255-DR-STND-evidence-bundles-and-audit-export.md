# Evidence Bundles and Audit Export Standard

**Document ID:** 255-DR-STND-evidence-bundles-and-audit-export
**Status:** ACTIVE
**Created:** 2026-01-02
**Author:** Claude Code
**Phase:** E (Enterprise Controls)

---

## 1. Purpose

This document defines the **evidence bundle system** for Bob's Brain. Evidence bundles provide:

- Complete audit trail for every pipeline run
- Artifact hashing for integrity verification
- Mandate snapshots for compliance
- Task and tool execution records

---

## 2. Storage Strategy

Evidence bundles use a dual-storage approach:

### 2.1 Local Storage

```
.evidence/
└── evb-abc123def456/
    ├── manifest.json      # Bundle manifest
    └── artifacts/         # (Future) Artifact files
```

### 2.2 GCS Export

GitHub Actions workflow exports bundles to GCS:

```yaml
# .github/workflows/evidence-export.yml (future)
- name: Export evidence bundles
  run: gsutil -m cp -r .evidence/* gs://${BUCKET}/evidence/
```

---

## 3. Bundle Manifest Structure

### 3.1 EvidenceBundleManifest

```python
@dataclass
class EvidenceBundleManifest:
    # Identifiers
    bundle_id: str          # evb-{uuid}
    mission_id: Optional[str]  # If from Mission Spec
    pipeline_run_id: str    # run-{uuid}

    # Timestamps
    created_at: str         # ISO 8601
    completed_at: Optional[str]

    # Mandate snapshot (frozen at execution time)
    mandate_snapshot: Dict[str, Any]

    # Execution tracking
    tasks_planned: List[str]
    tasks_executed: List[str]
    tasks_skipped: List[str]
    agents_invoked: List[str]

    # Detailed records
    tool_calls: List[Dict]
    artifacts: List[Dict]
    tests_run: List[Dict]
    checkpoints: List[str]

    # Status
    status: str  # "in_progress", "completed", "failed", "aborted"
    error_message: Optional[str]

    # Integrity
    manifest_version: str  # "1.0.0"
```

---

## 4. Record Types

### 4.1 ArtifactRecord

Records file artifacts with integrity hashes:

```python
@dataclass
class ArtifactRecord:
    path: str           # File path
    sha256: str         # SHA-256 hash
    size_bytes: int     # File size
    artifact_type: str  # "file", "log", "output", "checkpoint"
    created_at: str     # ISO 8601
```

### 4.2 ToolCallRecord

Records tool invocations:

```python
@dataclass
class ToolCallRecord:
    tool_name: str       # Tool identifier
    specialist: str      # Agent that called
    timestamp: str       # ISO 8601
    duration_ms: int     # Execution time
    success: bool        # Success/failure
    input_hash: str      # SHA-256 of input
    output_hash: str     # SHA-256 of output
    error_message: Optional[str]
```

### 4.3 UnitTestRecord

Records test executions:

```python
@dataclass
class UnitTestRecord:
    test_name: str       # Test identifier
    status: str          # "passed", "failed", "skipped", "error"
    duration_ms: int     # Execution time
    timestamp: str       # ISO 8601
    error_message: Optional[str]
```

---

## 5. Creating Evidence Bundles

### 5.1 Basic Usage

```python
from agents.shared_contracts import create_evidence_bundle

# Create bundle
bundle = create_evidence_bundle(
    mission_id="audit-compliance",
    mandate_snapshot={"mandate_id": "m-001", "risk_tier": "R2"}
)

# Record execution
bundle.record_task_planned("check-compliance")
bundle.record_agent_invoked("iam-compliance")
bundle.record_task_executed("check-compliance")

# Mark completion
bundle.mark_completed()

# Save to disk
path = bundle.save()
print(f"Bundle saved to: {path}")
```

### 5.2 Recording Tool Calls

```python
from agents.shared_contracts import ToolCallRecord, EvidenceBundle

bundle = EvidenceBundle()

record = ToolCallRecord(
    tool_name="search_code",
    specialist="iam-compliance",
    timestamp=datetime.now(timezone.utc).isoformat(),
    duration_ms=150,
    success=True,
    input_hash=EvidenceBundle.compute_sha256(b'{"query": "import"}'),
    output_hash=EvidenceBundle.compute_sha256(b'{"results": [...]}')
)
bundle.record_tool_call(record)
```

### 5.3 Recording Artifacts

```python
from pathlib import Path

# Add file artifact with automatic hashing
artifact = bundle.add_artifact_file(
    Path("reports/compliance.json"),
    artifact_type="output"
)
print(f"Artifact SHA256: {artifact.sha256}")
```

---

## 6. Loading Evidence Bundles

```python
from agents.shared_contracts import EvidenceBundle
from pathlib import Path

# Load from disk
bundle = EvidenceBundle.load(Path(".evidence/evb-abc123"))

# Access manifest
print(f"Bundle ID: {bundle.manifest.bundle_id}")
print(f"Status: {bundle.manifest.status}")
print(f"Tasks executed: {bundle.manifest.tasks_executed}")
```

---

## 7. Validating Artifacts

```python
# Validate all artifact hashes
failures = bundle.validate_artifacts()

if failures:
    for fail in failures:
        print(f"Validation failed: {fail['artifact']}")
        print(f"  Error: {fail['error']}")
else:
    print("All artifacts validated successfully")
```

---

## 8. Manifest JSON Example

```json
{
  "bundle_id": "evb-abc123def456",
  "mission_id": "audit-adk-compliance",
  "pipeline_run_id": "run-789xyz",
  "created_at": "2026-01-02T15:30:00Z",
  "completed_at": "2026-01-02T15:35:00Z",
  "mandate_snapshot": {
    "mandate_id": "m-audit-001",
    "intent": "Audit all agents for ADK compliance",
    "risk_tier": "R1",
    "budget_limit": 5.0
  },
  "tasks_planned": [
    "analyze-iam-compliance",
    "analyze-iam-qa",
    "generate-report"
  ],
  "tasks_executed": [
    "analyze-iam-compliance",
    "analyze-iam-qa",
    "generate-report"
  ],
  "tasks_skipped": [],
  "agents_invoked": [
    "iam-compliance"
  ],
  "tool_calls": [
    {
      "tool_name": "search_code",
      "specialist": "iam-compliance",
      "timestamp": "2026-01-02T15:31:00Z",
      "duration_ms": 150,
      "success": true,
      "input_hash": "a1b2c3...",
      "output_hash": "d4e5f6...",
      "error_message": null
    }
  ],
  "artifacts": [
    {
      "path": "reports/compliance.json",
      "sha256": "7g8h9i...",
      "size_bytes": 4096,
      "artifact_type": "output",
      "created_at": "2026-01-02T15:34:00Z"
    }
  ],
  "tests_run": [
    {
      "test_name": "test_agent_card_valid",
      "status": "passed",
      "duration_ms": 50,
      "timestamp": "2026-01-02T15:33:00Z",
      "error_message": null
    }
  ],
  "checkpoints": [],
  "status": "completed",
  "error_message": null,
  "manifest_version": "1.0.0"
}
```

---

## 9. Status Values

| Status | Description |
|--------|-------------|
| `in_progress` | Bundle is being populated |
| `completed` | Execution finished successfully |
| `failed` | Execution encountered an error |
| `aborted` | Execution was manually stopped |

---

## 10. Hashing

All hashes use SHA-256:

```python
# Hash bytes content
hash = EvidenceBundle.compute_sha256(b"content")

# Hash file
hash = EvidenceBundle.compute_file_sha256(Path("file.txt"))
```

---

## 11. Testing

### 11.1 Unit Tests

Located at: `tests/unit/test_enterprise_controls.py`

Run:
```bash
pytest tests/unit/test_enterprise_controls.py::TestEvidenceBundle* -v
```

### 11.2 Test Coverage

- Manifest auto-generated IDs
- JSON serialization roundtrip
- Task/agent recording
- Artifact hashing
- Save/load from disk
- Status marking

---

## 12. Future Enhancements

### 12.1 Artifact Copying

Copy artifacts into bundle directory for full containment:

```python
bundle.copy_artifact(Path("report.json"))  # Future
```

### 12.2 Signature Verification

Add cryptographic signatures for tamper-proofing:

```python
bundle.sign(private_key)  # Future
bundle.verify(public_key)  # Future
```

### 12.3 GCS Integration

Direct upload to GCS:

```python
bundle.upload_to_gcs("gs://bucket/evidence/")  # Future
```

---

## 13. Related Documents

- `000-docs/252-DR-STND-agent-identity-standard.md` - Agent ID standard
- `000-docs/253-DR-STND-mandates-budgets-approvals.md` - Mandate enterprise fields
- `000-docs/254-DR-STND-policy-gates-risk-tiers.md` - Policy gates
- `000-docs/251-AA-PLAN-bob-orchestrator-implementation.md` - Vision Alignment plan

---

## 14. Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-02 | 1.0.0 | Initial release (Phase E) |
