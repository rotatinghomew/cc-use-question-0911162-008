from __future__ import annotations

import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from safety_corpus_release.submissions.sample import ContractError, Decision, DomainRecord, records_from_fixture, stable_hash
from safety_corpus_release.catalog.corpus_store import Repository
from safety_corpus_release.screening.release_cycle import STATES, advance_for_outcome, allowed_targets, apply_transition, decide, guard_report, plan_transition
from safety_corpus_release.release.manifest import export_bundle, verify_bundle
from safety_corpus_release.release_station import Application, load_fixture, run, verify


FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "acceptance.json"


def load_records() -> list[DomainRecord]:
    return records_from_fixture(json.loads(FIXTURE.read_text(encoding="utf-8")))


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "state.sqlite3"
        self.repository = Repository(self.database)
        self.record = load_records()[0]

    def test_initialize_creates_expected_tables(self):
        with sqlite3.connect(self.database) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"records", "record_versions", "decisions", "events", "runs"}.issubset(tables))

    def test_save_and_load_record_round_trip(self):
        fingerprint = self.repository.save_record(self.record)
        loaded = self.repository.get_record(self.record.record_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.fingerprint, fingerprint)
        self.assertEqual(loaded.payload, self.record.payload)

    def test_identical_record_replay_is_idempotent(self):
        first = self.repository.save_record(self.record)
        second = self.repository.save_record(self.record)
        self.assertEqual(first, second)
        self.assertEqual(self.repository.snapshot()["counts"]["records"], 1)
        self.assertEqual(self.repository.snapshot()["counts"]["record_versions"], 1)

    def test_conflicting_version_is_rejected(self):
        self.repository.save_record(self.record)
        changed = self.record.with_payload({'sample_id': 999})
        with self.assertRaisesRegex(ContractError, "version conflict"):
            self.repository.save_record(changed, expected_version=99)

    def test_version_must_advance(self):
        self.repository.save_record(self.record)
        changed = DomainRecord(self.record.record_id, dict(self.record.payload) | {'risk_category': "changed"},
                               self.record.state, self.record.version, self.record.occurred_at, self.record.source)
        with self.assertRaisesRegex(ContractError, "version must advance"):
            self.repository.save_record(changed)

    def test_decision_requires_existing_record(self):
        decision = decide(self.record)
        with self.assertRaisesRegex(ContractError, "does not exist"):
            self.repository.save_decision(decision)

    def test_decision_replay_is_idempotent(self):
        self.repository.save_record(self.record)
        decision = decide(self.record)
        first = self.repository.save_decision(decision)
        second = self.repository.save_decision(decision)
        self.assertEqual(first, second)
        self.assertEqual(self.repository.snapshot()["counts"]["decisions"], 1)

    def test_audit_chain_detects_payload_tampering(self):
        self.repository.save_record(self.record)
        self.assertEqual(self.repository.verify_chain(), [])
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE events SET payload_json='{}' WHERE event_id=1")
        self.assertTrue(self.repository.verify_chain())

    def test_run_lifecycle_is_recorded(self):
        run_id = self.repository.begin_run("a" * 64, 3)
        self.repository.finish_run(run_id, {"ok": True})
        snapshot = self.repository.snapshot()
        self.assertEqual(snapshot["counts"]["runs"], 1)
        self.assertGreaterEqual(snapshot["counts"]["events"], 1)

    def test_list_records_filters_state(self):
        self.repository.save_record(self.record)
        advanced = self.record.with_state(STATES[1])
        self.repository.save_record(advanced, expected_version=1)
        self.assertEqual(len(self.repository.list_records(STATES[1])), 1)
        self.assertEqual(self.repository.list_records(STATES[1])[0].version, 2)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.record = load_records()[0]

    def test_allowed_targets_are_forward_only(self):
        targets = allowed_targets(STATES[0])
        self.assertTrue(targets)
        self.assertNotIn(STATES[0], targets)

    def test_unknown_state_is_rejected(self):
        with self.assertRaisesRegex(ContractError, "unknown workflow"):
            allowed_targets("unknown")

    def test_non_adjacent_transition_is_blocked(self):
        plan = plan_transition(self.record, STATES[-1], {"transition_threshold": 0.0})
        self.assertFalse(plan.allowed)
        self.assertTrue(any("not adjacent" in reason for reason in plan.reasons))

    def test_adjacent_transition_can_be_applied(self):
        plan = plan_transition(self.record, STATES[1], {"transition_threshold": 0.0})
        self.assertTrue(plan.allowed)
        changed = apply_transition(self.record, STATES[1], {"transition_threshold": 0.0})
        self.assertEqual(changed.state, STATES[1])
        self.assertEqual(changed.version, 2)

    def test_decision_contains_full_rule_evidence(self):
        decision = decide(self.record)
        self.assertEqual(decision.record_id, self.record.record_id)
        self.assertGreater(len(decision.rule_results), 100)
        self.assertEqual(set(decision.metrics), {'dataset_novelty', 'reuse_readiness', 'quarantine_pressure', 'condition_coverage', 'sequence_integrity', 'operator_balance', 'sensor_alignment', 'catalog_completeness'})

    def test_guard_report_counts_every_guard(self):
        result = guard_report(self.record)
        self.assertEqual(result["passed"] + result["failed"], len(result["messages"]))
        self.assertGreater(len(result["messages"]), 50)

    def test_outcome_advancement_is_deterministic(self):
        decision = decide(self.record)
        first = advance_for_outcome(self.record, decision)
        second = advance_for_outcome(self.record, decision)
        self.assertEqual(first, second)


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "run.sqlite3"
        self.output = self.root / "output"

    def test_acceptance_run_writes_verified_bundle(self):
        result = run(FIXTURE, self.database, self.output)
        self.assertEqual(result["records"], len(load_records()))
        self.assertTrue((self.output / "manifest.json").is_file())
        self.assertEqual(verify_bundle(self.output), [])
        self.assertTrue(verify(self.database, self.output)["ok"])

    def test_repeated_run_preserves_record_count(self):
        first = run(FIXTURE, self.database, self.output)
        second = run(FIXTURE, self.database, self.output)
        self.assertEqual(first["records"], second["records"])
        self.assertEqual(Repository(self.database).snapshot()["counts"]["records"], len(load_records()))

    def test_manifest_lists_all_json_artifacts(self):
        run(FIXTURE, self.database, self.output)
        manifest = json.loads((self.output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["files"]), {"summary.json", "decisions.json", "audit-events.json"})
        self.assertGreater(manifest["rule_rows"], 500)

    def test_records_csv_has_one_row_per_record(self):
        run(FIXTURE, self.database, self.output)
        with (self.output / "records.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), len(load_records()))
        self.assertTrue(all(row["fingerprint"] for row in rows))

    def test_rules_csv_contains_business_evidence(self):
        run(FIXTURE, self.database, self.output)
        with (self.output / "rules.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertGreater(len(rows), 500)
        self.assertTrue(all(row["code"] and row["message"] for row in rows))

    def test_bundle_tampering_is_detected(self):
        run(FIXTURE, self.database, self.output)
        summary = json.loads((self.output / "summary.json").read_text(encoding="utf-8"))
        summary["record_count"] = 999
        (self.output / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        self.assertIn("summary.json hash mismatch", verify_bundle(self.output))

    def test_load_fixture_rejects_non_object(self):
        path = self.root / "invalid.json"
        path.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "root must be an object"):
            load_fixture(path)

    def test_application_inspect_returns_decisions(self):
        application = Application(self.database)
        application.run_fixture(json.loads(FIXTURE.read_text(encoding="utf-8")), self.output)
        result = application.inspect()
        self.assertEqual(len(result["records"]), len(load_records()))
        self.assertEqual(len(result["decisions"]), len(load_records()))


class ScenarioVariationTests(unittest.TestCase):
    def setUp(self):
        self.records = load_records()

    def test_scenario_01_sample_id(self):
        base = self.records[0]
        changed = base.with_payload({'sample_id': 3.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('sample_id', changed.payload)

    def test_scenario_02_risk_category(self):
        base = self.records[1]
        changed = base.with_payload({'risk_category': 6.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('risk_category', changed.payload)

    def test_scenario_03_token_count(self):
        base = self.records[2]
        changed = base.with_payload({'token_count': 9.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('token_count', changed.payload)

    def test_scenario_04_duplicate_similarity(self):
        base = self.records[3]
        changed = base.with_payload({'duplicate_similarity': 13.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('duplicate_similarity', changed.payload)

    def test_scenario_05_language_coverage(self):
        base = self.records[4]
        changed = base.with_payload({'language_coverage': 16.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('language_coverage', changed.payload)

    def test_scenario_06_sensitive_entity_rate(self):
        base = self.records[5]
        changed = base.with_payload({'sensitive_entity_rate': 19.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('sensitive_entity_rate', changed.payload)

    def test_scenario_07_annotation_agreement(self):
        base = self.records[6]
        changed = base.with_payload({'annotation_agreement': 22.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('annotation_agreement', changed.payload)

    def test_scenario_08_license_compatibility(self):
        base = self.records[7]
        changed = base.with_payload({'license_compatibility': 26.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('license_compatibility', changed.payload)

    def test_scenario_09_split_drift(self):
        base = self.records[0]
        changed = base.with_payload({'split_drift': 29.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('split_drift', changed.payload)

    def test_scenario_10_rare_group_gap(self):
        base = self.records[1]
        changed = base.with_payload({'rare_group_gap': 32.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('rare_group_gap', changed.payload)

    def test_scenario_11_source_batch(self):
        base = self.records[2]
        changed = base.with_payload({'source_batch': 35.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('source_batch', changed.payload)

    def test_scenario_12_consent_basis(self):
        base = self.records[3]
        changed = base.with_payload({'consent_basis': 39.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('consent_basis', changed.payload)

    def test_scenario_13_sample_id(self):
        base = self.records[4]
        changed = base.with_payload({'sample_id': 42.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('sample_id', changed.payload)

    def test_scenario_14_risk_category(self):
        base = self.records[5]
        changed = base.with_payload({'risk_category': 45.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('risk_category', changed.payload)

    def test_scenario_15_token_count(self):
        base = self.records[6]
        changed = base.with_payload({'token_count': 48.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('token_count', changed.payload)

    def test_scenario_16_duplicate_similarity(self):
        base = self.records[7]
        changed = base.with_payload({'duplicate_similarity': 52.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('duplicate_similarity', changed.payload)

    def test_scenario_17_language_coverage(self):
        base = self.records[0]
        changed = base.with_payload({'language_coverage': 55.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('language_coverage', changed.payload)

    def test_scenario_18_sensitive_entity_rate(self):
        base = self.records[1]
        changed = base.with_payload({'sensitive_entity_rate': 58.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('sensitive_entity_rate', changed.payload)

    def test_scenario_19_annotation_agreement(self):
        base = self.records[2]
        changed = base.with_payload({'annotation_agreement': 61.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('annotation_agreement', changed.payload)

    def test_scenario_20_license_compatibility(self):
        base = self.records[3]
        changed = base.with_payload({'license_compatibility': 65.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('license_compatibility', changed.payload)

    def test_scenario_21_split_drift(self):
        base = self.records[4]
        changed = base.with_payload({'split_drift': 68.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('split_drift', changed.payload)

    def test_scenario_22_rare_group_gap(self):
        base = self.records[5]
        changed = base.with_payload({'rare_group_gap': 71.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('rare_group_gap', changed.payload)

    def test_scenario_23_source_batch(self):
        base = self.records[6]
        changed = base.with_payload({'source_batch': 74.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('source_batch', changed.payload)

    def test_scenario_24_consent_basis(self):
        base = self.records[7]
        changed = base.with_payload({'consent_basis': 78.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('consent_basis', changed.payload)

    def test_scenario_25_sample_id(self):
        base = self.records[0]
        changed = base.with_payload({'sample_id': 81.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('sample_id', changed.payload)

    def test_scenario_26_risk_category(self):
        base = self.records[1]
        changed = base.with_payload({'risk_category': 84.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('risk_category', changed.payload)

    def test_scenario_27_token_count(self):
        base = self.records[2]
        changed = base.with_payload({'token_count': 87.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('token_count', changed.payload)

    def test_scenario_28_duplicate_similarity(self):
        base = self.records[3]
        changed = base.with_payload({'duplicate_similarity': 91.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('duplicate_similarity', changed.payload)

    def test_scenario_29_language_coverage(self):
        base = self.records[4]
        changed = base.with_payload({'language_coverage': 94.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('language_coverage', changed.payload)

    def test_scenario_30_sensitive_entity_rate(self):
        base = self.records[5]
        changed = base.with_payload({'sensitive_entity_rate': 97.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('sensitive_entity_rate', changed.payload)

    def test_scenario_31_annotation_agreement(self):
        base = self.records[6]
        changed = base.with_payload({'annotation_agreement': 100.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('annotation_agreement', changed.payload)

    def test_scenario_32_license_compatibility(self):
        base = self.records[7]
        changed = base.with_payload({'license_compatibility': 104.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('license_compatibility', changed.payload)

    def test_scenario_33_split_drift(self):
        base = self.records[0]
        changed = base.with_payload({'split_drift': 107.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('split_drift', changed.payload)

    def test_scenario_34_rare_group_gap(self):
        base = self.records[1]
        changed = base.with_payload({'rare_group_gap': 110.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('rare_group_gap', changed.payload)

    def test_scenario_35_source_batch(self):
        base = self.records[2]
        changed = base.with_payload({'source_batch': 113.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('source_batch', changed.payload)

    def test_scenario_36_consent_basis(self):
        base = self.records[3]
        changed = base.with_payload({'consent_basis': 117.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('consent_basis', changed.payload)

    def test_scenario_37_sample_id(self):
        base = self.records[4]
        changed = base.with_payload({'sample_id': 120.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('sample_id', changed.payload)

    def test_scenario_38_risk_category(self):
        base = self.records[5]
        changed = base.with_payload({'risk_category': 123.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('risk_category', changed.payload)

    def test_scenario_39_token_count(self):
        base = self.records[6]
        changed = base.with_payload({'token_count': 126.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('token_count', changed.payload)

    def test_scenario_40_duplicate_similarity(self):
        base = self.records[7]
        changed = base.with_payload({'duplicate_similarity': 130.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('duplicate_similarity', changed.payload)

    def test_scenario_41_language_coverage(self):
        base = self.records[0]
        changed = base.with_payload({'language_coverage': 133.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('language_coverage', changed.payload)

    def test_scenario_42_sensitive_entity_rate(self):
        base = self.records[1]
        changed = base.with_payload({'sensitive_entity_rate': 136.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('sensitive_entity_rate', changed.payload)

    def test_scenario_43_annotation_agreement(self):
        base = self.records[2]
        changed = base.with_payload({'annotation_agreement': 139.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('annotation_agreement', changed.payload)

    def test_scenario_44_license_compatibility(self):
        base = self.records[3]
        changed = base.with_payload({'license_compatibility': 143.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('license_compatibility', changed.payload)

    def test_scenario_45_split_drift(self):
        base = self.records[4]
        changed = base.with_payload({'split_drift': 146.25})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('split_drift', changed.payload)

    def test_scenario_46_rare_group_gap(self):
        base = self.records[5]
        changed = base.with_payload({'rare_group_gap': 149.5})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('rare_group_gap', changed.payload)

    def test_scenario_47_source_batch(self):
        base = self.records[6]
        changed = base.with_payload({'source_batch': 152.75})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('source_batch', changed.payload)

    def test_scenario_48_consent_basis(self):
        base = self.records[7]
        changed = base.with_payload({'consent_basis': 156.0})
        original_decision = decide(base)
        changed_decision = decide(changed)
        self.assertEqual(original_decision.record_id, changed_decision.record_id)
        self.assertNotEqual(original_decision.fingerprint, changed_decision.fingerprint)
        self.assertTrue(0.0 <= changed_decision.score <= 1.0)
        self.assertIn('consent_basis', changed.payload)

if __name__ == '__main__':
    unittest.main()
