from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from safety_corpus_release.release_station import Application, run, verify
from safety_corpus_release.release.manifest import trusted_artifacts


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='safety_corpus_release', description='全球人工智能安全语料发布与代表性验证站')
    commands = root.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("run")
    execute.add_argument("--fixture", required=True)
    execute.add_argument("--database", required=True)
    execute.add_argument("--output", required=True)
    check = commands.add_parser("verify")
    check.add_argument("--database", required=True)
    check.add_argument("--output", required=True)
    split = commands.add_parser("split", help="导出训练/验证分组依据，仅信任通过完整性校验的发布包")
    split.add_argument("--output", required=True)
    split.add_argument("--record-id", help="查询单个记录的可信分组成员身份")
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--database", required=True)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "run":
        result = run(args.fixture, args.database, args.output)
        exit_ok = result.get("ok", True)
    elif args.command == "verify":
        result = verify(args.database, args.output)
        exit_ok = result["ok"]
    elif args.command == "split":
        trusted = trusted_artifacts(args.output)
        if not trusted["ok"]:
            result = trusted
        elif args.record_id:
            from safety_corpus_release.release.split_plan import membership_for
            result = {"ok": True, "record_id": args.record_id,
                      "partition": membership_for(trusted["split_plan"], args.record_id),
                      "bundle_id": trusted["manifest"].get("bundle_id")}
        else:
            plan = trusted["split_plan"]
            result = {"ok": True, "bundle_id": trusted["manifest"].get("bundle_id"),
                      "manifest_hash": trusted["manifest"].get("manifest_hash"),
                      "record_count": plan.get("record_count"),
                      "cluster_count": plan.get("cluster_count"),
                      "duplicate_record_count": plan.get("duplicate_record_count"),
                      "partitions": [
                          {"partition": entry["partition"], "record_count": entry["record_count"]}
                          for entry in plan.get("partitions", [])],
                      "coverage": plan.get("coverage"),
                      "quality": plan.get("quality")}
        exit_ok = bool(result["ok"])
    else:
        result = Application(args.database).inspect()
        exit_ok = True
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if exit_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
