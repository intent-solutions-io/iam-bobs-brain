"""
Evidence Bundle for Audit Trails (Phase E - Vision Alignment).

This module implements evidence bundle creation and management for
enterprise auditability. Every pipeline run produces an evidence bundle
containing:
- Manifest with metadata and checksums
- Mandate snapshot at execution time
- Task execution history
- Tool call records
- Artifact hashes

Storage Strategy (per user decision: BOTH local + GCS):
1. Local: .evidence/<run_id>/ directory with manifest.json + artifacts
2. GCS Export: GitHub Actions uploads to GCS bucket (see evidence-export.yml)

See: 000-docs/255-DR-STND-evidence-bundles-and-audit-export.md
"""

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for non-standard types (datetime, etc.)."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


@dataclass
class ArtifactRecord:
    """Record of an artifact in the evidence bundle."""

    path: str
    sha256: str
    size_bytes: int
    artifact_type: str  # "file", "log", "output", "checkpoint"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ToolCallRecord:
    """Record of a tool invocation during execution."""

    tool_name: str
    specialist: str
    timestamp: str
    duration_ms: int
    success: bool
    input_hash: str  # SHA256 of input params
    output_hash: str  # SHA256 of output
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class UnitTestRecord:
    """Record of a unit test execution during pipeline run."""

    test_name: str
    status: str  # "passed", "failed", "skipped", "error"
    duration_ms: int
    timestamp: str
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class EvidenceBundleManifest:
    """
    Manifest for an evidence bundle.

    This is the root document that describes all evidence collected
    during a pipeline run. It enables:
    - Audit trail for compliance
    - Reproducibility verification
    - Post-mortem analysis
    """

    # Identifiers
    bundle_id: str = field(default_factory=lambda: f"evb-{uuid.uuid4().hex[:12]}")
    mission_id: Optional[str] = None  # If run via Mission Spec
    pipeline_run_id: str = field(default_factory=lambda: f"run-{uuid.uuid4().hex[:12]}")

    # Timestamps
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: Optional[str] = None

    # Mandate snapshot (frozen at execution time)
    mandate_snapshot: Dict[str, Any] = field(default_factory=dict)

    # Execution tracking
    tasks_planned: List[str] = field(default_factory=list)
    tasks_executed: List[str] = field(default_factory=list)
    tasks_skipped: List[str] = field(default_factory=list)
    agents_invoked: List[str] = field(default_factory=list)

    # Detailed records
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    tests_run: List[Dict[str, Any]] = field(default_factory=list)
    checkpoints: List[str] = field(default_factory=list)

    # Status
    status: str = "in_progress"  # "in_progress", "completed", "failed", "aborted"
    error_message: Optional[str] = None

    # Integrity
    manifest_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=_json_serializer)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceBundleManifest":
        """Create manifest from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "EvidenceBundleManifest":
        """Create manifest from JSON string."""
        return cls.from_dict(json.loads(json_str))


class EvidenceBundle:
    """
    Manager for evidence bundle creation and storage.

    Provides methods to:
    - Create new bundles
    - Record events during execution
    - Calculate artifact hashes
    - Save/load bundles to/from disk
    """

    EVIDENCE_DIR = ".evidence"

    def __init__(
        self,
        manifest: Optional[EvidenceBundleManifest] = None,
        base_path: Optional[Path] = None,
    ):
        """
        Initialize an evidence bundle.

        Args:
            manifest: Existing manifest or None to create new
            base_path: Base path for evidence storage (default: cwd)
        """
        self.manifest = manifest or EvidenceBundleManifest()
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self._bundle_path: Optional[Path] = None

    @property
    def bundle_path(self) -> Path:
        """Get the path to this bundle's directory."""
        if self._bundle_path is None:
            self._bundle_path = (
                self.base_path / self.EVIDENCE_DIR / self.manifest.bundle_id
            )
        return self._bundle_path

    def set_mandate_snapshot(self, mandate_dict: Dict[str, Any]) -> None:
        """Set the mandate snapshot at execution start."""
        self.manifest.mandate_snapshot = mandate_dict

    def record_task_planned(self, task_id: str) -> None:
        """Record a task that was planned."""
        if task_id not in self.manifest.tasks_planned:
            self.manifest.tasks_planned.append(task_id)

    def record_task_executed(self, task_id: str) -> None:
        """Record a task that was executed."""
        if task_id not in self.manifest.tasks_executed:
            self.manifest.tasks_executed.append(task_id)

    def record_task_skipped(self, task_id: str) -> None:
        """Record a task that was skipped."""
        if task_id not in self.manifest.tasks_skipped:
            self.manifest.tasks_skipped.append(task_id)

    def record_agent_invoked(self, agent_id: str) -> None:
        """Record an agent that was invoked."""
        if agent_id not in self.manifest.agents_invoked:
            self.manifest.agents_invoked.append(agent_id)

    def record_tool_call(self, record: ToolCallRecord) -> None:
        """Record a tool invocation."""
        self.manifest.tool_calls.append(record.to_dict())

    def record_artifact(self, record: ArtifactRecord) -> None:
        """Record an artifact."""
        self.manifest.artifacts.append(record.to_dict())

    def record_test_run(self, record: UnitTestRecord) -> None:
        """Record a test run."""
        self.manifest.tests_run.append(record.to_dict())

    def record_checkpoint(self, checkpoint_id: str) -> None:
        """Record a checkpoint."""
        if checkpoint_id not in self.manifest.checkpoints:
            self.manifest.checkpoints.append(checkpoint_id)

    def mark_completed(self) -> None:
        """Mark the bundle as completed."""
        self.manifest.status = "completed"
        self.manifest.completed_at = datetime.now(timezone.utc).isoformat()

    def mark_failed(self, error_message: str) -> None:
        """Mark the bundle as failed."""
        self.manifest.status = "failed"
        self.manifest.completed_at = datetime.now(timezone.utc).isoformat()
        self.manifest.error_message = error_message

    def mark_aborted(self, reason: str) -> None:
        """Mark the bundle as aborted."""
        self.manifest.status = "aborted"
        self.manifest.completed_at = datetime.now(timezone.utc).isoformat()
        self.manifest.error_message = reason

    @staticmethod
    def compute_sha256(content: bytes) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def compute_file_sha256(file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def add_artifact_file(
        self, file_path: Path, artifact_type: str = "file"
    ) -> ArtifactRecord:
        """
        Add a file as an artifact and record its hash.

        Args:
            file_path: Path to the file
            artifact_type: Type of artifact

        Returns:
            ArtifactRecord with computed hash
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Artifact file not found: {file_path}")

        sha256 = self.compute_file_sha256(file_path)
        size = file_path.stat().st_size

        record = ArtifactRecord(
            path=str(file_path),
            sha256=sha256,
            size_bytes=size,
            artifact_type=artifact_type,
        )
        self.record_artifact(record)
        return record

    def save(self) -> Path:
        """
        Save the evidence bundle to disk.

        Creates the bundle directory and writes manifest.json.

        Returns:
            Path to the bundle directory
        """
        self.bundle_path.mkdir(parents=True, exist_ok=True)

        manifest_path = self.bundle_path / "manifest.json"
        with open(manifest_path, "w") as f:
            f.write(self.manifest.to_json())

        return self.bundle_path

    @classmethod
    def load(cls, bundle_path: Path) -> "EvidenceBundle":
        """
        Load an evidence bundle from disk.

        Args:
            bundle_path: Path to the bundle directory

        Returns:
            EvidenceBundle instance
        """
        bundle_path = Path(bundle_path)
        manifest_path = bundle_path / "manifest.json"

        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_path) as f:
            manifest = EvidenceBundleManifest.from_json(f.read())

        bundle = cls(manifest=manifest, base_path=bundle_path.parent.parent)
        bundle._bundle_path = bundle_path
        return bundle

    def validate_artifacts(self) -> List[Dict[str, Any]]:
        """
        Validate all artifacts have matching hashes.

        Returns:
            List of validation failures (empty if all valid)
        """
        failures = []
        for artifact in self.manifest.artifacts:
            path = Path(artifact["path"])
            if not path.exists():
                failures.append(
                    {"artifact": artifact["path"], "error": "file_not_found"}
                )
                continue

            actual_hash = self.compute_file_sha256(path)
            if actual_hash != artifact["sha256"]:
                failures.append(
                    {
                        "artifact": artifact["path"],
                        "error": "hash_mismatch",
                        "expected": artifact["sha256"],
                        "actual": actual_hash,
                    }
                )

        return failures


def create_evidence_bundle(
    mission_id: Optional[str] = None,
    pipeline_run_id: Optional[str] = None,
    mandate_snapshot: Optional[Dict[str, Any]] = None,
    base_path: Optional[Path] = None,
) -> EvidenceBundle:
    """
    Convenience function to create a new evidence bundle.

    Args:
        mission_id: Optional mission ID if run via Mission Spec
        pipeline_run_id: Optional custom run ID
        mandate_snapshot: Mandate state at execution start
        base_path: Base path for evidence storage

    Returns:
        New EvidenceBundle instance
    """
    manifest = EvidenceBundleManifest(
        mission_id=mission_id,
        pipeline_run_id=pipeline_run_id or f"run-{uuid.uuid4().hex[:12]}",
        mandate_snapshot=mandate_snapshot or {},
    )
    return EvidenceBundle(manifest=manifest, base_path=base_path)
