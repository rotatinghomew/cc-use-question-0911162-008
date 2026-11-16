全球人工智能安全语料发布与代表性验证站

运行验收：
python3 -m safety_corpus_release run --fixture fixtures/acceptance.json --database /tmp/safety_corpus_release.sqlite3 --output /tmp/safety_corpus_release-output

核验：
python3 -m safety_corpus_release verify --database /tmp/safety_corpus_release.sqlite3 --output /tmp/safety_corpus_release-output

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.quality_signal.test_release_quality -v

构建检查：
python3 -m compileall -q safety_corpus_release tests
