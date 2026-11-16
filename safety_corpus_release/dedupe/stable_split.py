from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Iterable

from safety_corpus_release.submissions.sample import DomainRecord, bounded, finite_number, stable_hash

# Fields that identify the reusable sampling unit: records sharing this identity
# are duplicate samples and must never be split across train/validation groups.
DUPLICATE_IDENTITY_FIELDS = ("sample_id", "risk_category", "source_batch", "consent_basis")


@dataclass(frozen=True)
class AlignmentWindow:
    submissions_id: str
    skew_ms: float
    frame_loss: float
    quality: float
    quarantine: bool


def alignment(record: DomainRecord) -> AlignmentWindow:
    skew = abs(finite_number(record.payload.get("split_drift", 0.0)))
    drops = max(0.0, finite_number(record.payload.get("rare_group_gap", 0.0)))
    camera_rate = max(1.0, finite_number(record.payload.get("annotation_agreement", 1.0)))
    force_rate = max(1.0, finite_number(record.payload.get("license_compatibility", 1.0)))
    normalized_skew = bounded(skew / 250.0)
    loss = bounded(drops / (camera_rate * 30.0))
    rate_fit = bounded(min(camera_rate, force_rate) / max(camera_rate, force_rate))
    quality = bounded(rate_fit * 0.45 + (1.0 - normalized_skew) * 0.35 + (1.0 - loss) * 0.20)
    return AlignmentWindow(record.record_id, skew, loss, quality, quality < 0.55 or skew > 150.0)


def condition_cell(record: DomainRecord) -> tuple[int, int, int, int]:
    angle = int(finite_number(record.payload.get("token_count", 0.0)) // 15)
    duplicate_similarity = int(finite_number(record.payload.get("duplicate_similarity", 0.0)) // 5)
    language_coverage = int(finite_number(record.payload.get("language_coverage", 0.0)) // 100)
    dust = int(finite_number(record.payload.get("sensitive_entity_rate", 0.0)) // 10)
    return angle, duplicate_similarity, language_coverage, dust


def coverage_lattice(records: Iterable[DomainRecord]) -> dict[str, float]:
    rows = list(records)
    cells = {condition_cell(row) for row in rows}
    robots = {str(row.payload.get("sample_id", "unknown")) for row in rows}
    parts = {str(row.payload.get("risk_category", "unknown")) for row in rows}
    clustered = sum(alignment(row).quarantine for row in rows)
    theoretical = max(1, len(robots) * len(parts) * 4)
    return {"cell_count": float(len(cells)), "robot_count": float(len(robots)), "part_count": float(len(parts)),
            "coverage": bounded(len(cells) / theoretical), "quarantine_rate": clustered / max(1, len(rows))}


def sequence_health(records: Iterable[DomainRecord]) -> dict[str, float]:
    windows = [alignment(row) for row in records]
    qualities = [window.quality for window in windows]
    return {"mean_alignment": statistics.fmean(qualities) if qualities else 0.0,
            "alignment_jitter": statistics.pstdev(qualities) if len(qualities) > 1 else 0.0,
            "clustered": float(sum(window.quarantine for window in windows))}


def derive_context(record: DomainRecord, repository: Any) -> dict[str, float]:
    rows = repository.list_records() or [record]
    window = alignment(record)
    coverage = coverage_lattice(rows)
    health = sequence_health(rows)
    return {"sensor_alignment_weight": 0.6 + window.quality * 0.6,
            "condition_coverage_weight": 0.7 + coverage["coverage"] * 0.5,
            "sequence_integrity_weight": 0.7 + health["mean_alignment"] * 0.4,
            "quarantine_pressure_weight": 0.7 + coverage["quarantine_rate"] * 0.8,
            "reuse_readiness_weight": 0.6 + (1.0 - health["alignment_jitter"]) * 0.5}


def duplicate_identity(record: DomainRecord) -> tuple[str, ...]:
    """Stable identity of the reusable sampling unit behind a record."""
    return tuple(str(record.payload.get(field, "")).strip() for field in DUPLICATE_IDENTITY_FIELDS)


def duplicate_clusters(records: Iterable[DomainRecord]) -> list[dict[str, Any]]:
    """Group records by their duplicate identity while preserving record order.

    Each returned cluster is the grouping boundary that downstream splitting must
    keep intact: every record sharing the identity lands in one partition only.
    """
    grouped: dict[tuple[str, ...], list[str]] = {}
    for record in records:
        grouped.setdefault(duplicate_identity(record), []).append(record.record_id)
    clusters = [
        {"cluster_id": stable_hash({"identity": list(identity)})[:24],
         "identity": dict(zip(DUPLICATE_IDENTITY_FIELDS, identity)),
         "record_ids": sorted(record_ids),
         "record_count": len(record_ids),
         "duplicate_count": len(record_ids) - 1}
        for identity, record_ids in grouped.items()
    ]
    return sorted(clusters, key=lambda item: item["cluster_id"])


def assign_partitions(clusters: list[dict[str, Any]], validation_ratio: float = 0.25,
                      salt: str = "safety-corpus-split-v1") -> dict[str, str]:
    """Deterministically assign whole duplicate clusters to a partition.

    The decision uses only the cluster id and a fixed salt, so the same released
    manifest always yields the same membership and no cluster is ever torn apart.
    """
    if not 0.0 < validation_ratio < 1.0:
        raise ValueError("validation_ratio must be strictly between 0 and 1")
    assignments: dict[str, str] = {}
    cluster_count = len(clusters)
    target_validation = min(cluster_count - 1, max(1, round(cluster_count * validation_ratio))) if cluster_count > 1 else 0
    ranked = sorted(
        clusters,
        key=lambda cluster: (int(stable_hash({"salt": salt, "cluster_id": cluster["cluster_id"]}), 16),
                             cluster["cluster_id"]),
    )
    for index, cluster in enumerate(ranked):
        partition = "validation" if index < target_validation else "train"
        for record_id in cluster["record_ids"]:
            assignments[record_id] = partition
    return assignments


def split_assignment(records: Iterable[DomainRecord], validation_ratio: float = 0.25) -> dict[str, Any]:
    """Produce the stable train/validation assignment with duplicate boundaries."""
    rows = list(records)
    clusters = duplicate_clusters(rows)
    assignments = assign_partitions(clusters, validation_ratio=validation_ratio)
    partitions = {"train": sorted(rid for rid, part in assignments.items() if part == "train"),
                  "validation": sorted(rid for rid, part in assignments.items() if part == "validation")}
    return {"clusters": clusters, "assignments": assignments, "partitions": partitions,
            "cluster_count": len(clusters), "record_count": len(rows)}
