全球人工智能安全语料发布与代表性验证站

运行验收：
python3 -m safety_corpus_release run --fixture fixtures/acceptance.json --database /tmp/safety_corpus_release.sqlite3 --output /tmp/safety_corpus_release-output

核验（审计链 + 发布包逐文件完整性，含 records.csv / rules.csv / split-plan.json）：
python3 -m safety_corpus_release verify --database /tmp/safety_corpus_release.sqlite3 --output /tmp/safety_corpus_release-output

训练/验证分组依据（只信任通过完整性校验的发布包，校验失败时以退出码 1 拒绝）：
python3 -m safety_corpus_release split --output /tmp/safety_corpus_release-output
python3 -m safety_corpus_release split --output /tmp/safety_corpus_release-output --record-id safety_sample-001

发布包完整性与分组衔接说明：
1. manifest.json 对全部产物（summary.json、decisions.json、audit-events.json、
   records.csv、rules.csv、split-plan.json）按文件原始字节计算 SHA-256，
   明细或规则统计被任何方式改动都会在 verify / split 阶段报 hash mismatch。
2. manifest 同时封存 record_rows / rule_rows，复核时与 CSV 实际行数、
   summary 计数、decisions.json 证据行数交叉核对。
3. split-plan.json 固化重复样本簇边界（同 sample_id/risk_category/source_batch/
   consent_basis 的记录永不跨训练/验证集）、确定性分组结果、实际覆盖（coverage）
   与质量口径（quality），并回链 manifest 的 bundle_id；分组只能经
   trusted_artifacts / split 命令在整包校验通过后读取。
4. bundle_id 仅由稳定语料内容与分组计划派生，同一份资料重新生成得到相同身份，
   可对照当时的清单版本复核；恢复手段是重新生成合法发布包，不删除合法明细、
   不抹去已发布的审计记录。

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.quality_signal.test_release_quality -v
python3 -m unittest tests.release.test_split_plan -v

构建检查：
python3 -m compileall -q safety_corpus_release tests
