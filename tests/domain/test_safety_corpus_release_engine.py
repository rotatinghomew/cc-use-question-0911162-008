from __future__ import annotations

import unittest
from safety_corpus_release.submissions.sample import DomainRecord
from safety_corpus_release.dedupe.stable_split import alignment, condition_cell, coverage_lattice, sequence_health


class TimelineTests(unittest.TestCase):
    def record(self, key, skew=5, drops=0):
        return DomainRecord(key, {"sample_id": "r1", "risk_category": "axle", "token_count": 32, "duplicate_similarity": 4,
            "language_coverage": 500, "sensitive_entity_rate": 8, "annotation_agreement": 30, "license_compatibility": 100,
            "split_drift": skew, "rare_group_gap": drops, "source_batch": "op", "consent_basis": "training"})

    def test_large_skew_quarantines(self):
        self.assertFalse(alignment(self.record("a")).quarantine)
        self.assertTrue(alignment(self.record("b", skew=220)).quarantine)

    def test_lattice_and_sequence_health(self):
        rows = [self.record("a"), self.record("b", drops=900)]
        self.assertEqual(len(condition_cell(rows[0])), 4)
        self.assertGreater(coverage_lattice(rows)["cell_count"], 0)
        self.assertEqual(sequence_health(rows)["clustered"], 1.0)
