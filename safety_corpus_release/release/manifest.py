from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from safety_corpus_release.submissions.sample import Decision, DomainRecord, stable_hash, utc_now

MANIFEST_VERSION = "2.0"
MANIFEST_NAME = "manifest.json"
SPLIT_PLAN_NAME = "split-plan.json"
BUNDLE_ARTIFACTS = ("summary.json", "decisions.json", "audit-events.json", "records.csv", "rules.csv")


def ensure_output(path: str | Path) -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output


def hash_bytes(data: bytes) -> str:
    """Hash the exact bytes of an artifact so any on-disk edit is detectable."""
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path) -> str:
    return hash_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    path.write_text(body + "\n", encoding="utf-8")
    return hash_file(path)


def write_records(path: Path, records: Iterable[DomainRecord], decisions: Mapping[str, Decision]) -> int:
    rows = []
    for record in records:
        decision = decisions.get(record.record_id)
        rows.append({"record_id": record.record_id, "state": record.state, "version": record.version,
                     "source": record.source, "fingerprint": record.fingerprint,
                     "outcome": decision.outcome if decision else "", "score": decision.score if decision else ""})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "state", "version", "source", "fingerprint", "outcome", "score"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_rules(path: Path, decisions: Mapping[str, Decision]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "code", "passed", "score", "severity", "message"])
        writer.writeheader()
        for record_id, decision in sorted(decisions.items()):
            for result in decision.rule_results:
                writer.writerow({"record_id": record_id, "code": result.code, "passed": result.passed,
                                 "score": result.score, "severity": result.severity, "message": result.message})
                count += 1
    return count


def count_data_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def build_summary(records: list[DomainRecord], decisions: Mapping[str, Decision], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    outcomes: dict[str, int] = {}
    for decision in decisions.values():
        outcomes[decision.outcome] = outcomes.get(decision.outcome, 0) + 1
    scores = [decision.score for decision in decisions.values()]
    return {"product": '全球人工智能安全语料发布与代表性验证站', "entity": 'safety_sample', "generated_at": utc_now(),
            "record_count": len(records), "decision_count": len(decisions), "outcomes": outcomes,
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "minimum_score": min(scores) if scores else 0.0, "maximum_score": max(scores) if scores else 0.0,
            "repository": snapshot}


def _load_json(root: Path, name: str, errors: list[str]) -> Any:
    path = root / name
    if not path.is_file():
        errors.append(f"{name} is missing")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        errors.append(f"{name} is unreadable: {exc}")
        return None


def export_bundle(output: str | Path, records: list[DomainRecord], decisions: Mapping[str, Decision],
                  snapshot: Mapping[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    # Imported here to keep the manifest module free of a reverse dependency at import time.
    from safety_corpus_release.release.split_plan import build_split_plan

    root = ensure_output(output)
    summary = build_summary(records, decisions, snapshot)
    record_count = write_records(root / "records.csv", records, decisions)
    rule_count = write_rules(root / "rules.csv", decisions)
    summary_hash = write_json(root / "summary.json", summary)
    decision_hash = write_json(root / "decisions.json", [value.as_dict() for _, value in sorted(decisions.items())])
    event_hash = write_json(root / "audit-events.json", events)

    split_plan = build_split_plan(records, decisions)
    split_hash = write_json(root / SPLIT_PLAN_NAME, split_plan)

    # The bundle identity binds the stable corpus content and the split plan.
    # occurred_at is deliberately excluded: it is ingestion metadata regenerated
    # on each run, while the on-disk fingerprint column and file hash still
    # protect it from tampering.
    source_fingerprints = sorted(
        stable_hash({"record_id": record.record_id, "payload": record.payload,
                     "state": record.state, "version": record.version,
                     "source": record.source})
        for record in records)
    bundle_id = stable_hash({"manifest_version": MANIFEST_VERSION, "source_fingerprints": source_fingerprints,
                             "split_plan_hash": split_hash})
    split_plan["bundle_id"] = bundle_id
    split_hash = write_json(root / SPLIT_PLAN_NAME, split_plan)

    files = {
        "summary.json": summary_hash,
        "decisions.json": decision_hash,
        "audit-events.json": event_hash,
        "records.csv": hash_file(root / "records.csv"),
        "rules.csv": hash_file(root / "rules.csv"),
        SPLIT_PLAN_NAME: split_hash,
    }
    manifest = {"manifest_version": MANIFEST_VERSION, "bundle_id": bundle_id, "files": files,
                "record_rows": record_count, "rule_rows": rule_count, "created_at": utc_now()}
    manifest["manifest_hash"] = stable_hash(manifest)
    write_json(root / MANIFEST_NAME, manifest)
    return manifest


def verify_bundle(output: str | Path) -> list[str]:
    root = Path(output)
    errors: list[str] = []
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        return [f"{MANIFEST_NAME} is missing"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"{MANIFEST_NAME} is unreadable: {exc}"]
    if not isinstance(manifest, dict):
        return [f"{MANIFEST_NAME} has an invalid structure"]

    expected_manifest_hash = manifest.pop("manifest_hash", "")
    if stable_hash(manifest) != expected_manifest_hash:
        errors.append("manifest hash mismatch")

    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        errors.append("manifest file catalog is missing")
        return errors

    # Every catalogued artifact is hashed over its exact bytes, so edits to
    # records.csv or rules.csv cannot slip past verification.
    for name in sorted(files):
        expected = files[name]
        path = root / name
        if not path.is_file():
            errors.append(f"{name} is missing")
            continue
        if hash_file(path) != expected:
            errors.append(f"{name} hash mismatch")

    summary = _load_json(root, "summary.json", errors)
    decisions_payload = _load_json(root, "decisions.json", errors)
    split_plan = _load_json(root, SPLIT_PLAN_NAME, errors)

    records_csv = root / "records.csv"
    rules_csv = root / "rules.csv"
    if records_csv.is_file():
        try:
            actual_record_rows = count_data_rows(records_csv)
        except (csv.Error, OSError, UnicodeDecodeError) as exc:
            actual_record_rows = None
            errors.append(f"records.csv is unreadable: {exc}")
        if actual_record_rows is not None and actual_record_rows != manifest.get("record_rows"):
            errors.append("records.csv row count does not match manifest")
        if isinstance(summary, dict) and actual_record_rows is not None \
                and summary.get("record_count") != actual_record_rows:
            errors.append("summary record_count does not match records.csv")
        if isinstance(decisions_payload, list) and actual_record_rows is not None \
                and len(decisions_payload) != actual_record_rows:
            errors.append("decisions.json does not match records.csv row count")

    if rules_csv.is_file():
        try:
            actual_rule_rows = count_data_rows(rules_csv)
        except (csv.Error, OSError, UnicodeDecodeError) as exc:
            actual_rule_rows = None
            errors.append(f"rules.csv is unreadable: {exc}")
        if actual_rule_rows is not None and actual_rule_rows != manifest.get("rule_rows"):
            errors.append("rules.csv row count does not match manifest")
        if isinstance(decisions_payload, list):
            expected_rule_rows = sum(
                len(item.get("rules", ())) for item in decisions_payload if isinstance(item, dict))
            if actual_rule_rows is not None and expected_rule_rows != actual_rule_rows:
                errors.append("rules.csv does not match the rule evidence in decisions.json")

    if isinstance(split_plan, dict) and split_plan.get("bundle_id") != manifest.get("bundle_id"):
        errors.append("split-plan.json bundle_id does not match manifest")

    return errors


def trusted_artifacts(output: str | Path) -> dict[str, Any]:
    """Load the manifest and split plan only when the whole bundle verifies.

    Downstream train/validation grouping must call this instead of reading the
    CSV/JSON files directly, so tampered details or rule statistics can never be
    treated as trusted input.
    """
    from safety_corpus_release.release.split_plan import verify_split_plan

    root = Path(output)
    errors = verify_bundle(root)
    manifest_path = root / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    split_path = root / SPLIT_PLAN_NAME
    split_plan = json.loads(split_path.read_text(encoding="utf-8")) if split_path.is_file() else {}
    if isinstance(split_plan, dict):
        errors.extend(verify_split_plan(split_plan))
    else:
        errors.append(f"{SPLIT_PLAN_NAME} has an invalid structure")
    return {"ok": not errors, "errors": errors, "manifest": manifest, "split_plan": split_plan}
