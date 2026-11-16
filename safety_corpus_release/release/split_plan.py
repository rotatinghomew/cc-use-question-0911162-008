from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from safety_corpus_release.submissions.sample import Decision, DomainRecord, stable_hash
from safety_corpus_release.dedupe.stable_split import (
    DUPLICATE_IDENTITY_FIELDS,
    coverage_lattice,
    duplicate_identity,
    sequence_health,
    split_assignment,
)
from safety_corpus_release.quality_signal.release_quality import release_quality

DEFAULT_VALIDATION_RATIO = 0.25
SUPPORTED_PARTITIONS = ("train", "validation")


def quality_summary(records: list[DomainRecord]) -> dict[str, Any]:
    """Quality口径 derived only from the released records, fully reproducible."""
    signals = [release_quality(record.payload) for record in records]
    if not signals:
        return {"count": 0, "average_score": 0.0, "minimum_score": 0.0,
                "maximum_score": 0.0, "severity_counts": {}, "blocked_count": 0}
    scores = [signal.score for signal in signals]
    severity_counts = Counter(signal.severity for signal in signals)
    return {"count": len(signals),
            "average_score": sum(scores) / len(scores),
            "minimum_score": min(scores), "maximum_score": max(scores),
            "severity_counts": dict(sorted(severity_counts.items())),
            "blocked_count": severity_counts.get("critical", 0)}


def build_split_plan(records: list[DomainRecord], decisions: Mapping[str, Decision],
                     validation_ratio: float = DEFAULT_VALIDATION_RATIO) -> dict[str, Any]:
    """Build the versioned train/validation basis that ships inside a bundle.

    It captures duplicate cluster boundaries, the deterministic partition of
    every record, the actual condition coverage, and the quality口径, so the
    downstream split references the exact same material as the manifest.
    """
    assignment = split_assignment(records, validation_ratio=validation_ratio)
    coverage = coverage_lattice(records)
    health = sequence_health(records)
    quality = quality_summary(records)
    outcomes = Counter(decision.outcome for decision in decisions.values())

    cluster_by_id = {cluster["cluster_id"]: cluster for cluster in assignment["clusters"]}
    partition_of_cluster: dict[str, str] = {}
    for cluster in assignment["clusters"]:
        first_record = cluster["record_ids"][0]
        partition_of_cluster[cluster["cluster_id"]] = assignment["assignments"][first_record]

    partitions = []
    for partition in SUPPORTED_PARTITIONS:
        member_ids = assignment["partitions"].get(partition, [])
        member_set = set(member_ids)
        partitions.append({
            "partition": partition,
            "record_ids": member_ids,
            "record_count": len(member_ids),
            "cluster_ids": sorted(cid for cid, part in partition_of_cluster.items() if part == partition),
            "outcomes": dict(sorted(Counter(
                decisions[record_id].outcome for record_id in member_ids if record_id in decisions).items())),
        })

    plan = {
        "schema": "safety-corpus-split-plan/1",
        "validation_ratio": validation_ratio,
        "duplicate_identity_fields": list(DUPLICATE_IDENTITY_FIELDS),
        "record_count": assignment["record_count"],
        "cluster_count": assignment["cluster_count"],
        "duplicate_record_count": sum(
            cluster["duplicate_count"] for cluster in assignment["clusters"]),
        "clusters": assignment["clusters"],
        "partitions": partitions,
        "assignments": dict(sorted(assignment["assignments"].items())),
        "coverage": coverage,
        "sequence_health": health,
        "quality": quality,
        "outcomes": dict(sorted(outcomes.items())),
    }
    plan["plan_hash"] = stable_hash({key: value for key, value in plan.items()})
    # bundle_id is stamped by the exporter once the manifest identity is known.
    plan["bundle_id"] = ""
    return plan


def verify_split_plan(plan: Any) -> list[str]:
    """Validate the internal consistency of a split plan loaded from a bundle."""
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["split-plan.json has an invalid structure"]

    clusters = plan.get("clusters")
    assignments = plan.get("assignments")
    partitions = plan.get("partitions")
    if not isinstance(clusters, list) or not isinstance(assignments, dict) or not isinstance(partitions, list):
        return ["split-plan.json is missing clusters, assignments or partitions"]

    cluster_ids: list[str] = []
    clustered_records: set[str] = set()
    for cluster in clusters:
        if not isinstance(cluster, dict):
            errors.append("split-plan.json contains a malformed cluster")
            continue
        cluster_ids.append(cluster.get("cluster_id"))
        record_ids = cluster.get("record_ids")
        if not isinstance(record_ids, list) or not record_ids:
            errors.append("split-plan.json contains a cluster without records")
            continue
        # A duplicate cluster must be an intact boundary inside one partition.
        target_partitions = {assignments.get(record_id) for record_id in record_ids}
        if target_partitions != set() and (len(target_partitions) != 1
                                           or target_partitions & {None}):
            errors.append(f"cluster {cluster.get('cluster_id')} spans multiple partitions")
        clustered_records.update(record_ids)

    if len(cluster_ids) != len(set(cluster_ids)):
        errors.append("split-plan.json contains duplicate cluster identifiers")
    if set(assignments) != clustered_records:
        errors.append("split-plan.json assignments do not cover the clustered records")
    if any(partition not in SUPPORTED_PARTITIONS for partition in assignments.values()):
        errors.append("split-plan.json contains an unknown partition name")

    partitioned_records: set[str] = set()
    seen_partitions: set[str] = set()
    for entry in partitions:
        if not isinstance(entry, dict):
            errors.append("split-plan.json contains a malformed partition")
            continue
        name = entry.get("partition")
        seen_partitions.add(name)
        member_ids = entry.get("record_ids", [])
        if any(assignments.get(record_id) != name for record_id in member_ids):
            errors.append(f"partition {name} disagrees with the cluster assignments")
        partitioned_records.update(member_ids)
    if seen_partitions != set(SUPPORTED_PARTITIONS):
        errors.append("split-plan.json must contain both train and validation partitions")
    if partitioned_records != clustered_records:
        errors.append("split-plan.json partitions do not cover every clustered record")

    if plan.get("record_count") != len(assignments):
        errors.append("split-plan.json record_count does not match its assignments")
    if plan.get("cluster_count") != len(clusters):
        errors.append("split-plan.json cluster_count does not match its clusters")

    expected_duplicates = sum(
        max(0, len(cluster.get("record_ids", [])) - 1)
        for cluster in clusters if isinstance(cluster, dict))
    if plan.get("duplicate_record_count") != expected_duplicates:
        errors.append("split-plan.json duplicate_record_count is inconsistent")

    return errors


def membership_for(plan: Mapping[str, Any], record_id: str) -> str | None:
    """Return the trusted partition of a record according to the released plan."""
    assignments = plan.get("assignments")
    return assignments.get(record_id) if isinstance(assignments, dict) else None
