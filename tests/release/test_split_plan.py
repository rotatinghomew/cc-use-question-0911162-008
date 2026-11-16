from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from safety_corpus_release.submissions.sample import Decision, DomainRecord
from safety_corpus_release.dedupe.stable_split import (
    DUPLICATE_IDENTITY_FIELDS,
    assign_partitions,
    duplicate_clusters,
    duplicate_identity,
    split_assignment,
)
from safety_corpus_release.release.split_plan import (
    build_split_plan,
    membership_for,
    verify_split_plan,
)


def make_record(record_id: str, sample_id: str, batch: str = "batch-a") -> DomainRecord:
    payload = {field: f"{field}-x" for field in DUPLICATE_IDENTITY_FIELDS}
    payload["sample_id"] = sample_id
    payload["source_batch"] = batch
    payload["risk_category"] = "risk-x"
    payload["consent_basis"] = "consent-x"
    return DomainRecord(record_id, payload)


class DuplicateClusterTests(unittest.TestCase):
    def test_records_sharing_identity_form_one_cluster(self):
        records = [make_record("r1", "dup"), make_record("r2", "dup"), make_record("r3", "other")]
        clusters = duplicate_clusters(records)
        self.assertEqual(len(clusters), 2)
        paired = next(cluster for cluster in clusters if cluster["record_count"] == 2)
        self.assertEqual(paired["record_ids"], ["r1", "r2"])
        self.assertEqual(paired["duplicate_count"], 1)
        self.assertEqual(duplicate_identity(records[0]), duplicate_identity(records[1]))

    def test_assignment_never_splits_a_cluster(self):
        records = [make_record(f"r{i}", f"sample-{i % 4}") for i in range(12)]
        assignment = split_assignment(records, validation_ratio=0.3)
        for cluster in assignment["clusters"]:
            partitions = {assignment["assignments"][rid] for rid in cluster["record_ids"]}
            self.assertEqual(len(partitions), 1)
        self.assertEqual(set(assignment["partitions"]), {"train", "validation"})
        self.assertTrue(assignment["partitions"]["validation"])
        self.assertTrue(assignment["partitions"]["train"])

    def test_assignment_is_deterministic(self):
        records = [make_record(f"r{i}", f"sample-{i % 5}") for i in range(20)]
        first = assign_partitions(duplicate_clusters(records))
        second = assign_partitions(duplicate_clusters(records))
        self.assertEqual(first, second)

    def test_validation_ratio_is_validated(self):
        with self.assertRaises(ValueError):
            assign_partitions(duplicate_clusters([make_record("r1", "s1")]), validation_ratio=0)


class SplitPlanTests(unittest.TestCase):
    def setUp(self):
        self.records = [make_record(f"r{i}", f"sample-{i % 3}", batch=f"batch-{i % 2}") for i in range(9)]

    def test_plan_preserves_cluster_boundaries_and_quality_basis(self):
        decisions = {record.record_id: Decision(record.record_id, "approve", 0.7, ("ok",), (), {})
                     for record in self.records}
        plan = build_split_plan(self.records, decisions)
        self.assertEqual(verify_split_plan(plan), [])
        self.assertEqual(plan["record_count"], 9)
        self.assertEqual(plan["cluster_count"], 6)
        self.assertEqual(plan["duplicate_record_count"], 3)
        self.assertEqual(plan["outcomes"], {"approve": 9})
        self.assertIn("coverage", plan)
        self.assertIn("quality", plan)
        self.assertEqual(plan["quality"]["count"], 9)
        for record_id in (record.record_id for record in self.records):
            self.assertIn(membership_for(plan, record_id), {"train", "validation"})

    def test_plan_hash_changes_when_membership_changes(self):
        decisions = {record.record_id: Decision(record.record_id, "review", 0.4, ("check",), (), {})
                     for record in self.records}
        base = build_split_plan(self.records, decisions)
        changed = build_split_plan(self.records, decisions, validation_ratio=0.4)
        self.assertNotEqual(base["plan_hash"], changed["plan_hash"])
        self.assertEqual(verify_split_plan(changed), [])

    def test_verify_rejects_plan_with_split_cluster(self):
        decisions = {record.record_id: Decision(record.record_id, "approve", 0.7, ("ok",), (), {})
                     for record in self.records}
        plan = build_split_plan(self.records, decisions)
        cluster = next(item for item in plan["clusters"] if item["record_count"] > 1)
        plan["assignments"][cluster["record_ids"][0]] = "train"
        plan["assignments"][cluster["record_ids"][1]] = "validation"
        self.assertTrue(verify_split_plan(plan))

    def test_verify_rejects_plan_with_inconsistent_counts(self):
        decisions = {record.record_id: Decision(record.record_id, "approve", 0.7, ("ok",), (), {})
                     for record in self.records}
        plan = build_split_plan(self.records, decisions)
        plan["record_count"] = plan["record_count"] + 1
        self.assertIn("split-plan.json record_count does not match its assignments",
                      verify_split_plan(plan))

    def test_bundle_round_trip_rejects_edited_plan(self):
        from safety_corpus_release.release.manifest import export_bundle, trusted_artifacts, verify_bundle

        decisions = {record.record_id: Decision(record.record_id, "approve", 0.7, ("ok",), (), {})
                     for record in self.records}
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "bundle"
            export_bundle(output, self.records, decisions, {"chain_errors": []}, [])
            self.assertEqual(verify_bundle(output), [])
            trusted = trusted_artifacts(output)
            self.assertTrue(trusted["ok"], trusted["errors"])
            plan_path = output / "split-plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["validation_ratio"] = 0.9
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            self.assertFalse(trusted_artifacts(output)["ok"])
            self.assertIn("split-plan.json hash mismatch", verify_bundle(output))


if __name__ == "__main__":
    unittest.main()
