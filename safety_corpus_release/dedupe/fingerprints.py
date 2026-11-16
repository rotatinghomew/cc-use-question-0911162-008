from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from safety_corpus_release.submissions.sample import DomainRecord, RuleResult, bounded, finite_number, normalized_text

RuleFunction = Callable[[DomainRecord, Mapping[str, Any]], RuleResult]

def _number(record: DomainRecord, field: str) -> float:
    value = record.payload.get(field)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return finite_number(value)
    text = normalized_text(value)
    if not text:
        return 0.0
    try:
        return finite_number(text)
    except ValueError:
        tokens = [item for item in text.replace(',', ' ').replace(';', ' ').split() if item]
        return float(min(100, len(text) + len(set(tokens)) * 5))

def _context_number(context: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return finite_number(context.get(key, default))
    except ValueError:
        return default

def _result(code: str, value: float, threshold: float, higher_is_better: bool, message: str, evidence: dict[str, Any]) -> RuleResult:
    distance = (value - threshold) if higher_is_better else (threshold - value)
    passed = distance >= 0
    scale = max(1.0, abs(threshold))
    score = bounded(0.5 + distance / (2.0 * scale))
    severity = 'info' if passed else ('critical' if score < 0.2 else 'error')
    return RuleResult(code, passed, score, severity, message, evidence)

def check_sample_id_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_id')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_sample_id_presence_threshold', 10.333)
    return _result('check_sample_id_presence', adjusted, threshold, True, 'validates sample_id presence',
                   {'field': 'sample_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_id_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_id')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_sample_id_range_threshold', 12.667)
    return _result('check_sample_id_range', adjusted, threshold, True, 'validates sample_id range',
                   {'field': 'sample_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_id_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_id')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_sample_id_stability_threshold', 15.0)
    return _result('check_sample_id_stability', adjusted, threshold, False, 'validates sample_id stability',
                   {'field': 'sample_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_id_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_id')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_sample_id_freshness_threshold', 17.333)
    return _result('check_sample_id_freshness', adjusted, threshold, True, 'validates sample_id freshness',
                   {'field': 'sample_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_id_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_id')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_sample_id_coverage_threshold', 19.667)
    return _result('check_sample_id_coverage', adjusted, threshold, True, 'validates sample_id coverage',
                   {'field': 'sample_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_id_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_id')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_sample_id_consistency_threshold', 22.0)
    return _result('check_sample_id_consistency', adjusted, threshold, False, 'validates sample_id consistency',
                   {'field': 'sample_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_id_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_id')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_sample_id_risk_threshold', 24.333)
    return _result('check_sample_id_risk', adjusted, threshold, True, 'validates sample_id risk',
                   {'field': 'sample_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_id_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_id')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_sample_id_confidence_threshold', 26.667)
    return _result('check_sample_id_confidence', adjusted, threshold, True, 'validates sample_id confidence',
                   {'field': 'sample_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_id_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_id')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_sample_id_dependency_threshold', 29.0)
    return _result('check_sample_id_dependency', adjusted, threshold, False, 'validates sample_id dependency',
                   {'field': 'sample_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_id_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_id')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_sample_id_readiness_threshold', 31.333)
    return _result('check_sample_id_readiness', adjusted, threshold, True, 'validates sample_id readiness',
                   {'field': 'sample_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_risk_category_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'risk_category')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_risk_category_presence_threshold', 9.333)
    return _result('check_risk_category_presence', adjusted, threshold, True, 'validates risk_category presence',
                   {'field': 'risk_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_risk_category_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'risk_category')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_risk_category_range_threshold', 11.667)
    return _result('check_risk_category_range', adjusted, threshold, False, 'validates risk_category range',
                   {'field': 'risk_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_risk_category_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'risk_category')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_risk_category_stability_threshold', 14.0)
    return _result('check_risk_category_stability', adjusted, threshold, True, 'validates risk_category stability',
                   {'field': 'risk_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_risk_category_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'risk_category')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_risk_category_freshness_threshold', 16.333)
    return _result('check_risk_category_freshness', adjusted, threshold, True, 'validates risk_category freshness',
                   {'field': 'risk_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_risk_category_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'risk_category')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_risk_category_coverage_threshold', 18.667)
    return _result('check_risk_category_coverage', adjusted, threshold, False, 'validates risk_category coverage',
                   {'field': 'risk_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_risk_category_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'risk_category')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_risk_category_consistency_threshold', 21.0)
    return _result('check_risk_category_consistency', adjusted, threshold, True, 'validates risk_category consistency',
                   {'field': 'risk_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_risk_category_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'risk_category')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_risk_category_risk_threshold', 23.333)
    return _result('check_risk_category_risk', adjusted, threshold, True, 'validates risk_category risk',
                   {'field': 'risk_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_risk_category_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'risk_category')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_risk_category_confidence_threshold', 25.667)
    return _result('check_risk_category_confidence', adjusted, threshold, False, 'validates risk_category confidence',
                   {'field': 'risk_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_risk_category_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'risk_category')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_risk_category_dependency_threshold', 28.0)
    return _result('check_risk_category_dependency', adjusted, threshold, True, 'validates risk_category dependency',
                   {'field': 'risk_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_risk_category_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'risk_category')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_risk_category_readiness_threshold', 30.333)
    return _result('check_risk_category_readiness', adjusted, threshold, True, 'validates risk_category readiness',
                   {'field': 'risk_category', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_token_count_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'token_count')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_token_count_presence_threshold', 8.333)
    return _result('check_token_count_presence', adjusted, threshold, False, 'validates token_count presence',
                   {'field': 'token_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_token_count_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'token_count')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_token_count_range_threshold', 10.667)
    return _result('check_token_count_range', adjusted, threshold, True, 'validates token_count range',
                   {'field': 'token_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_token_count_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'token_count')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_token_count_stability_threshold', 13.0)
    return _result('check_token_count_stability', adjusted, threshold, True, 'validates token_count stability',
                   {'field': 'token_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_token_count_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'token_count')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_token_count_freshness_threshold', 15.333)
    return _result('check_token_count_freshness', adjusted, threshold, False, 'validates token_count freshness',
                   {'field': 'token_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_token_count_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'token_count')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_token_count_coverage_threshold', 17.667)
    return _result('check_token_count_coverage', adjusted, threshold, True, 'validates token_count coverage',
                   {'field': 'token_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_token_count_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'token_count')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_token_count_consistency_threshold', 20.0)
    return _result('check_token_count_consistency', adjusted, threshold, True, 'validates token_count consistency',
                   {'field': 'token_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_token_count_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'token_count')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_token_count_risk_threshold', 22.333)
    return _result('check_token_count_risk', adjusted, threshold, False, 'validates token_count risk',
                   {'field': 'token_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_token_count_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'token_count')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_token_count_confidence_threshold', 24.667)
    return _result('check_token_count_confidence', adjusted, threshold, True, 'validates token_count confidence',
                   {'field': 'token_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_token_count_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'token_count')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_token_count_dependency_threshold', 27.0)
    return _result('check_token_count_dependency', adjusted, threshold, True, 'validates token_count dependency',
                   {'field': 'token_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_token_count_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'token_count')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_token_count_readiness_threshold', 29.333)
    return _result('check_token_count_readiness', adjusted, threshold, False, 'validates token_count readiness',
                   {'field': 'token_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_duplicate_similarity_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'duplicate_similarity')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_duplicate_similarity_presence_threshold', 31.667)
    return _result('check_duplicate_similarity_presence', adjusted, threshold, True, 'validates duplicate_similarity presence',
                   {'field': 'duplicate_similarity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_duplicate_similarity_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'duplicate_similarity')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_duplicate_similarity_range_threshold', 9.667)
    return _result('check_duplicate_similarity_range', adjusted, threshold, True, 'validates duplicate_similarity range',
                   {'field': 'duplicate_similarity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_duplicate_similarity_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'duplicate_similarity')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_duplicate_similarity_stability_threshold', 12.0)
    return _result('check_duplicate_similarity_stability', adjusted, threshold, False, 'validates duplicate_similarity stability',
                   {'field': 'duplicate_similarity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_duplicate_similarity_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'duplicate_similarity')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_duplicate_similarity_freshness_threshold', 14.333)
    return _result('check_duplicate_similarity_freshness', adjusted, threshold, True, 'validates duplicate_similarity freshness',
                   {'field': 'duplicate_similarity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_duplicate_similarity_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'duplicate_similarity')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_duplicate_similarity_coverage_threshold', 16.667)
    return _result('check_duplicate_similarity_coverage', adjusted, threshold, True, 'validates duplicate_similarity coverage',
                   {'field': 'duplicate_similarity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_duplicate_similarity_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'duplicate_similarity')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_duplicate_similarity_consistency_threshold', 19.0)
    return _result('check_duplicate_similarity_consistency', adjusted, threshold, False, 'validates duplicate_similarity consistency',
                   {'field': 'duplicate_similarity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_duplicate_similarity_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'duplicate_similarity')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_duplicate_similarity_risk_threshold', 21.333)
    return _result('check_duplicate_similarity_risk', adjusted, threshold, True, 'validates duplicate_similarity risk',
                   {'field': 'duplicate_similarity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_duplicate_similarity_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'duplicate_similarity')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_duplicate_similarity_confidence_threshold', 23.667)
    return _result('check_duplicate_similarity_confidence', adjusted, threshold, True, 'validates duplicate_similarity confidence',
                   {'field': 'duplicate_similarity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_duplicate_similarity_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'duplicate_similarity')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_duplicate_similarity_dependency_threshold', 26.0)
    return _result('check_duplicate_similarity_dependency', adjusted, threshold, False, 'validates duplicate_similarity dependency',
                   {'field': 'duplicate_similarity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_duplicate_similarity_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'duplicate_similarity')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_duplicate_similarity_readiness_threshold', 28.333)
    return _result('check_duplicate_similarity_readiness', adjusted, threshold, True, 'validates duplicate_similarity readiness',
                   {'field': 'duplicate_similarity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_coverage_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_coverage')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_language_coverage_presence_threshold', 30.667)
    return _result('check_language_coverage_presence', adjusted, threshold, True, 'validates language_coverage presence',
                   {'field': 'language_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_coverage_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_coverage')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_language_coverage_range_threshold', 8.667)
    return _result('check_language_coverage_range', adjusted, threshold, False, 'validates language_coverage range',
                   {'field': 'language_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_coverage_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_coverage')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_language_coverage_stability_threshold', 11.0)
    return _result('check_language_coverage_stability', adjusted, threshold, True, 'validates language_coverage stability',
                   {'field': 'language_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_coverage_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_coverage')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_language_coverage_freshness_threshold', 13.333)
    return _result('check_language_coverage_freshness', adjusted, threshold, True, 'validates language_coverage freshness',
                   {'field': 'language_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_coverage_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_coverage')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_language_coverage_coverage_threshold', 15.667)
    return _result('check_language_coverage_coverage', adjusted, threshold, False, 'validates language_coverage coverage',
                   {'field': 'language_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_coverage_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_coverage')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_language_coverage_consistency_threshold', 18.0)
    return _result('check_language_coverage_consistency', adjusted, threshold, True, 'validates language_coverage consistency',
                   {'field': 'language_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_coverage_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_coverage')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_language_coverage_risk_threshold', 20.333)
    return _result('check_language_coverage_risk', adjusted, threshold, True, 'validates language_coverage risk',
                   {'field': 'language_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_coverage_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_coverage')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_language_coverage_confidence_threshold', 22.667)
    return _result('check_language_coverage_confidence', adjusted, threshold, False, 'validates language_coverage confidence',
                   {'field': 'language_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_coverage_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_coverage')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_language_coverage_dependency_threshold', 25.0)
    return _result('check_language_coverage_dependency', adjusted, threshold, True, 'validates language_coverage dependency',
                   {'field': 'language_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_coverage_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_coverage')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_language_coverage_readiness_threshold', 27.333)
    return _result('check_language_coverage_readiness', adjusted, threshold, True, 'validates language_coverage readiness',
                   {'field': 'language_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitive_entity_rate_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitive_entity_rate')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_sensitive_entity_rate_presence_threshold', 29.667)
    return _result('check_sensitive_entity_rate_presence', adjusted, threshold, False, 'validates sensitive_entity_rate presence',
                   {'field': 'sensitive_entity_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitive_entity_rate_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitive_entity_rate')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_sensitive_entity_rate_range_threshold', 32.0)
    return _result('check_sensitive_entity_rate_range', adjusted, threshold, True, 'validates sensitive_entity_rate range',
                   {'field': 'sensitive_entity_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitive_entity_rate_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitive_entity_rate')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_sensitive_entity_rate_stability_threshold', 10.0)
    return _result('check_sensitive_entity_rate_stability', adjusted, threshold, True, 'validates sensitive_entity_rate stability',
                   {'field': 'sensitive_entity_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitive_entity_rate_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitive_entity_rate')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_sensitive_entity_rate_freshness_threshold', 12.333)
    return _result('check_sensitive_entity_rate_freshness', adjusted, threshold, False, 'validates sensitive_entity_rate freshness',
                   {'field': 'sensitive_entity_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitive_entity_rate_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitive_entity_rate')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_sensitive_entity_rate_coverage_threshold', 14.667)
    return _result('check_sensitive_entity_rate_coverage', adjusted, threshold, True, 'validates sensitive_entity_rate coverage',
                   {'field': 'sensitive_entity_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitive_entity_rate_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitive_entity_rate')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_sensitive_entity_rate_consistency_threshold', 17.0)
    return _result('check_sensitive_entity_rate_consistency', adjusted, threshold, True, 'validates sensitive_entity_rate consistency',
                   {'field': 'sensitive_entity_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitive_entity_rate_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitive_entity_rate')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_sensitive_entity_rate_risk_threshold', 19.333)
    return _result('check_sensitive_entity_rate_risk', adjusted, threshold, False, 'validates sensitive_entity_rate risk',
                   {'field': 'sensitive_entity_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitive_entity_rate_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitive_entity_rate')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_sensitive_entity_rate_confidence_threshold', 21.667)
    return _result('check_sensitive_entity_rate_confidence', adjusted, threshold, True, 'validates sensitive_entity_rate confidence',
                   {'field': 'sensitive_entity_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitive_entity_rate_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitive_entity_rate')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_sensitive_entity_rate_dependency_threshold', 24.0)
    return _result('check_sensitive_entity_rate_dependency', adjusted, threshold, True, 'validates sensitive_entity_rate dependency',
                   {'field': 'sensitive_entity_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitive_entity_rate_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitive_entity_rate')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_sensitive_entity_rate_readiness_threshold', 26.333)
    return _result('check_sensitive_entity_rate_readiness', adjusted, threshold, False, 'validates sensitive_entity_rate readiness',
                   {'field': 'sensitive_entity_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_annotation_agreement_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'annotation_agreement')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_annotation_agreement_presence_threshold', 28.667)
    return _result('check_annotation_agreement_presence', adjusted, threshold, True, 'validates annotation_agreement presence',
                   {'field': 'annotation_agreement', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_annotation_agreement_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'annotation_agreement')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_annotation_agreement_range_threshold', 31.0)
    return _result('check_annotation_agreement_range', adjusted, threshold, True, 'validates annotation_agreement range',
                   {'field': 'annotation_agreement', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_annotation_agreement_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'annotation_agreement')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_annotation_agreement_stability_threshold', 9.0)
    return _result('check_annotation_agreement_stability', adjusted, threshold, False, 'validates annotation_agreement stability',
                   {'field': 'annotation_agreement', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_annotation_agreement_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'annotation_agreement')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_annotation_agreement_freshness_threshold', 11.333)
    return _result('check_annotation_agreement_freshness', adjusted, threshold, True, 'validates annotation_agreement freshness',
                   {'field': 'annotation_agreement', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_annotation_agreement_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'annotation_agreement')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_annotation_agreement_coverage_threshold', 13.667)
    return _result('check_annotation_agreement_coverage', adjusted, threshold, True, 'validates annotation_agreement coverage',
                   {'field': 'annotation_agreement', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_annotation_agreement_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'annotation_agreement')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_annotation_agreement_consistency_threshold', 16.0)
    return _result('check_annotation_agreement_consistency', adjusted, threshold, False, 'validates annotation_agreement consistency',
                   {'field': 'annotation_agreement', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_annotation_agreement_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'annotation_agreement')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_annotation_agreement_risk_threshold', 18.333)
    return _result('check_annotation_agreement_risk', adjusted, threshold, True, 'validates annotation_agreement risk',
                   {'field': 'annotation_agreement', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_annotation_agreement_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'annotation_agreement')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_annotation_agreement_confidence_threshold', 20.667)
    return _result('check_annotation_agreement_confidence', adjusted, threshold, True, 'validates annotation_agreement confidence',
                   {'field': 'annotation_agreement', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_annotation_agreement_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'annotation_agreement')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_annotation_agreement_dependency_threshold', 23.0)
    return _result('check_annotation_agreement_dependency', adjusted, threshold, False, 'validates annotation_agreement dependency',
                   {'field': 'annotation_agreement', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_annotation_agreement_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'annotation_agreement')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_annotation_agreement_readiness_threshold', 25.333)
    return _result('check_annotation_agreement_readiness', adjusted, threshold, True, 'validates annotation_agreement readiness',
                   {'field': 'annotation_agreement', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_license_compatibility_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'license_compatibility')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_license_compatibility_presence_threshold', 27.667)
    return _result('check_license_compatibility_presence', adjusted, threshold, True, 'validates license_compatibility presence',
                   {'field': 'license_compatibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_license_compatibility_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'license_compatibility')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_license_compatibility_range_threshold', 30.0)
    return _result('check_license_compatibility_range', adjusted, threshold, False, 'validates license_compatibility range',
                   {'field': 'license_compatibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_license_compatibility_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'license_compatibility')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_license_compatibility_stability_threshold', 8.0)
    return _result('check_license_compatibility_stability', adjusted, threshold, True, 'validates license_compatibility stability',
                   {'field': 'license_compatibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_license_compatibility_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'license_compatibility')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_license_compatibility_freshness_threshold', 10.333)
    return _result('check_license_compatibility_freshness', adjusted, threshold, True, 'validates license_compatibility freshness',
                   {'field': 'license_compatibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_license_compatibility_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'license_compatibility')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_license_compatibility_coverage_threshold', 12.667)
    return _result('check_license_compatibility_coverage', adjusted, threshold, False, 'validates license_compatibility coverage',
                   {'field': 'license_compatibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_license_compatibility_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'license_compatibility')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_license_compatibility_consistency_threshold', 15.0)
    return _result('check_license_compatibility_consistency', adjusted, threshold, True, 'validates license_compatibility consistency',
                   {'field': 'license_compatibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_license_compatibility_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'license_compatibility')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_license_compatibility_risk_threshold', 17.333)
    return _result('check_license_compatibility_risk', adjusted, threshold, True, 'validates license_compatibility risk',
                   {'field': 'license_compatibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_license_compatibility_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'license_compatibility')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_license_compatibility_confidence_threshold', 19.667)
    return _result('check_license_compatibility_confidence', adjusted, threshold, False, 'validates license_compatibility confidence',
                   {'field': 'license_compatibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_license_compatibility_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'license_compatibility')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_license_compatibility_dependency_threshold', 22.0)
    return _result('check_license_compatibility_dependency', adjusted, threshold, True, 'validates license_compatibility dependency',
                   {'field': 'license_compatibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_license_compatibility_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'license_compatibility')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_license_compatibility_readiness_threshold', 24.333)
    return _result('check_license_compatibility_readiness', adjusted, threshold, True, 'validates license_compatibility readiness',
                   {'field': 'license_compatibility', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_split_drift_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'split_drift')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_split_drift_presence_threshold', 26.667)
    return _result('check_split_drift_presence', adjusted, threshold, False, 'validates split_drift presence',
                   {'field': 'split_drift', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_split_drift_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'split_drift')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_split_drift_range_threshold', 29.0)
    return _result('check_split_drift_range', adjusted, threshold, True, 'validates split_drift range',
                   {'field': 'split_drift', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_split_drift_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'split_drift')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_split_drift_stability_threshold', 31.333)
    return _result('check_split_drift_stability', adjusted, threshold, True, 'validates split_drift stability',
                   {'field': 'split_drift', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_split_drift_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'split_drift')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_split_drift_freshness_threshold', 9.333)
    return _result('check_split_drift_freshness', adjusted, threshold, False, 'validates split_drift freshness',
                   {'field': 'split_drift', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_split_drift_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'split_drift')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_split_drift_coverage_threshold', 11.667)
    return _result('check_split_drift_coverage', adjusted, threshold, True, 'validates split_drift coverage',
                   {'field': 'split_drift', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_split_drift_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'split_drift')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_split_drift_consistency_threshold', 14.0)
    return _result('check_split_drift_consistency', adjusted, threshold, True, 'validates split_drift consistency',
                   {'field': 'split_drift', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_split_drift_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'split_drift')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_split_drift_risk_threshold', 16.333)
    return _result('check_split_drift_risk', adjusted, threshold, False, 'validates split_drift risk',
                   {'field': 'split_drift', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_split_drift_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'split_drift')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_split_drift_confidence_threshold', 18.667)
    return _result('check_split_drift_confidence', adjusted, threshold, True, 'validates split_drift confidence',
                   {'field': 'split_drift', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_split_drift_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'split_drift')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_split_drift_dependency_threshold', 21.0)
    return _result('check_split_drift_dependency', adjusted, threshold, True, 'validates split_drift dependency',
                   {'field': 'split_drift', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_split_drift_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'split_drift')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_split_drift_readiness_threshold', 23.333)
    return _result('check_split_drift_readiness', adjusted, threshold, False, 'validates split_drift readiness',
                   {'field': 'split_drift', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_rare_group_gap_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'rare_group_gap')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_rare_group_gap_presence_threshold', 25.667)
    return _result('check_rare_group_gap_presence', adjusted, threshold, True, 'validates rare_group_gap presence',
                   {'field': 'rare_group_gap', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_rare_group_gap_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'rare_group_gap')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_rare_group_gap_range_threshold', 28.0)
    return _result('check_rare_group_gap_range', adjusted, threshold, True, 'validates rare_group_gap range',
                   {'field': 'rare_group_gap', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_rare_group_gap_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'rare_group_gap')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_rare_group_gap_stability_threshold', 30.333)
    return _result('check_rare_group_gap_stability', adjusted, threshold, False, 'validates rare_group_gap stability',
                   {'field': 'rare_group_gap', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_rare_group_gap_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'rare_group_gap')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_rare_group_gap_freshness_threshold', 8.333)
    return _result('check_rare_group_gap_freshness', adjusted, threshold, True, 'validates rare_group_gap freshness',
                   {'field': 'rare_group_gap', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_rare_group_gap_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'rare_group_gap')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_rare_group_gap_coverage_threshold', 10.667)
    return _result('check_rare_group_gap_coverage', adjusted, threshold, True, 'validates rare_group_gap coverage',
                   {'field': 'rare_group_gap', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_rare_group_gap_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'rare_group_gap')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_rare_group_gap_consistency_threshold', 13.0)
    return _result('check_rare_group_gap_consistency', adjusted, threshold, False, 'validates rare_group_gap consistency',
                   {'field': 'rare_group_gap', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_rare_group_gap_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'rare_group_gap')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_rare_group_gap_risk_threshold', 15.333)
    return _result('check_rare_group_gap_risk', adjusted, threshold, True, 'validates rare_group_gap risk',
                   {'field': 'rare_group_gap', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_rare_group_gap_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'rare_group_gap')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_rare_group_gap_confidence_threshold', 17.667)
    return _result('check_rare_group_gap_confidence', adjusted, threshold, True, 'validates rare_group_gap confidence',
                   {'field': 'rare_group_gap', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_rare_group_gap_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'rare_group_gap')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_rare_group_gap_dependency_threshold', 20.0)
    return _result('check_rare_group_gap_dependency', adjusted, threshold, False, 'validates rare_group_gap dependency',
                   {'field': 'rare_group_gap', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_rare_group_gap_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'rare_group_gap')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_rare_group_gap_readiness_threshold', 22.333)
    return _result('check_rare_group_gap_readiness', adjusted, threshold, True, 'validates rare_group_gap readiness',
                   {'field': 'rare_group_gap', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_batch_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_batch')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_source_batch_presence_threshold', 24.667)
    return _result('check_source_batch_presence', adjusted, threshold, True, 'validates source_batch presence',
                   {'field': 'source_batch', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_batch_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_batch')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_source_batch_range_threshold', 27.0)
    return _result('check_source_batch_range', adjusted, threshold, False, 'validates source_batch range',
                   {'field': 'source_batch', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_batch_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_batch')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_source_batch_stability_threshold', 29.333)
    return _result('check_source_batch_stability', adjusted, threshold, True, 'validates source_batch stability',
                   {'field': 'source_batch', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_batch_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_batch')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_source_batch_freshness_threshold', 31.667)
    return _result('check_source_batch_freshness', adjusted, threshold, True, 'validates source_batch freshness',
                   {'field': 'source_batch', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_batch_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_batch')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_source_batch_coverage_threshold', 9.667)
    return _result('check_source_batch_coverage', adjusted, threshold, False, 'validates source_batch coverage',
                   {'field': 'source_batch', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_batch_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_batch')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_source_batch_consistency_threshold', 12.0)
    return _result('check_source_batch_consistency', adjusted, threshold, True, 'validates source_batch consistency',
                   {'field': 'source_batch', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_batch_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_batch')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_source_batch_risk_threshold', 14.333)
    return _result('check_source_batch_risk', adjusted, threshold, True, 'validates source_batch risk',
                   {'field': 'source_batch', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_batch_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_batch')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_source_batch_confidence_threshold', 16.667)
    return _result('check_source_batch_confidence', adjusted, threshold, False, 'validates source_batch confidence',
                   {'field': 'source_batch', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_batch_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_batch')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_source_batch_dependency_threshold', 19.0)
    return _result('check_source_batch_dependency', adjusted, threshold, True, 'validates source_batch dependency',
                   {'field': 'source_batch', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_source_batch_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'source_batch')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_source_batch_readiness_threshold', 21.333)
    return _result('check_source_batch_readiness', adjusted, threshold, True, 'validates source_batch readiness',
                   {'field': 'source_batch', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_basis_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_basis')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_consent_basis_presence_threshold', 23.667)
    return _result('check_consent_basis_presence', adjusted, threshold, False, 'validates consent_basis presence',
                   {'field': 'consent_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_basis_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_basis')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_consent_basis_range_threshold', 26.0)
    return _result('check_consent_basis_range', adjusted, threshold, True, 'validates consent_basis range',
                   {'field': 'consent_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_basis_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_basis')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_consent_basis_stability_threshold', 28.333)
    return _result('check_consent_basis_stability', adjusted, threshold, True, 'validates consent_basis stability',
                   {'field': 'consent_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_basis_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_basis')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_consent_basis_freshness_threshold', 30.667)
    return _result('check_consent_basis_freshness', adjusted, threshold, False, 'validates consent_basis freshness',
                   {'field': 'consent_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_basis_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_basis')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_consent_basis_coverage_threshold', 8.667)
    return _result('check_consent_basis_coverage', adjusted, threshold, True, 'validates consent_basis coverage',
                   {'field': 'consent_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_basis_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_basis')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_consent_basis_consistency_threshold', 11.0)
    return _result('check_consent_basis_consistency', adjusted, threshold, True, 'validates consent_basis consistency',
                   {'field': 'consent_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_basis_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_basis')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_consent_basis_risk_threshold', 13.333)
    return _result('check_consent_basis_risk', adjusted, threshold, False, 'validates consent_basis risk',
                   {'field': 'consent_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_basis_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_basis')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_consent_basis_confidence_threshold', 15.667)
    return _result('check_consent_basis_confidence', adjusted, threshold, True, 'validates consent_basis confidence',
                   {'field': 'consent_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_basis_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_basis')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_consent_basis_dependency_threshold', 18.0)
    return _result('check_consent_basis_dependency', adjusted, threshold, True, 'validates consent_basis dependency',
                   {'field': 'consent_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_basis_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_basis')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_consent_basis_readiness_threshold', 20.333)
    return _result('check_consent_basis_readiness', adjusted, threshold, False, 'validates consent_basis readiness',
                   {'field': 'consent_basis', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

RULES: tuple[RuleFunction, ...] = (
    check_sample_id_presence,
    check_sample_id_range,
    check_sample_id_stability,
    check_sample_id_freshness,
    check_sample_id_coverage,
    check_sample_id_consistency,
    check_sample_id_risk,
    check_sample_id_confidence,
    check_sample_id_dependency,
    check_sample_id_readiness,
    check_risk_category_presence,
    check_risk_category_range,
    check_risk_category_stability,
    check_risk_category_freshness,
    check_risk_category_coverage,
    check_risk_category_consistency,
    check_risk_category_risk,
    check_risk_category_confidence,
    check_risk_category_dependency,
    check_risk_category_readiness,
    check_token_count_presence,
    check_token_count_range,
    check_token_count_stability,
    check_token_count_freshness,
    check_token_count_coverage,
    check_token_count_consistency,
    check_token_count_risk,
    check_token_count_confidence,
    check_token_count_dependency,
    check_token_count_readiness,
    check_duplicate_similarity_presence,
    check_duplicate_similarity_range,
    check_duplicate_similarity_stability,
    check_duplicate_similarity_freshness,
    check_duplicate_similarity_coverage,
    check_duplicate_similarity_consistency,
    check_duplicate_similarity_risk,
    check_duplicate_similarity_confidence,
    check_duplicate_similarity_dependency,
    check_duplicate_similarity_readiness,
    check_language_coverage_presence,
    check_language_coverage_range,
    check_language_coverage_stability,
    check_language_coverage_freshness,
    check_language_coverage_coverage,
    check_language_coverage_consistency,
    check_language_coverage_risk,
    check_language_coverage_confidence,
    check_language_coverage_dependency,
    check_language_coverage_readiness,
    check_sensitive_entity_rate_presence,
    check_sensitive_entity_rate_range,
    check_sensitive_entity_rate_stability,
    check_sensitive_entity_rate_freshness,
    check_sensitive_entity_rate_coverage,
    check_sensitive_entity_rate_consistency,
    check_sensitive_entity_rate_risk,
    check_sensitive_entity_rate_confidence,
    check_sensitive_entity_rate_dependency,
    check_sensitive_entity_rate_readiness,
    check_annotation_agreement_presence,
    check_annotation_agreement_range,
    check_annotation_agreement_stability,
    check_annotation_agreement_freshness,
    check_annotation_agreement_coverage,
    check_annotation_agreement_consistency,
    check_annotation_agreement_risk,
    check_annotation_agreement_confidence,
    check_annotation_agreement_dependency,
    check_annotation_agreement_readiness,
    check_license_compatibility_presence,
    check_license_compatibility_range,
    check_license_compatibility_stability,
    check_license_compatibility_freshness,
    check_license_compatibility_coverage,
    check_license_compatibility_consistency,
    check_license_compatibility_risk,
    check_license_compatibility_confidence,
    check_license_compatibility_dependency,
    check_license_compatibility_readiness,
    check_split_drift_presence,
    check_split_drift_range,
    check_split_drift_stability,
    check_split_drift_freshness,
    check_split_drift_coverage,
    check_split_drift_consistency,
    check_split_drift_risk,
    check_split_drift_confidence,
    check_split_drift_dependency,
    check_split_drift_readiness,
    check_rare_group_gap_presence,
    check_rare_group_gap_range,
    check_rare_group_gap_stability,
    check_rare_group_gap_freshness,
    check_rare_group_gap_coverage,
    check_rare_group_gap_consistency,
    check_rare_group_gap_risk,
    check_rare_group_gap_confidence,
    check_rare_group_gap_dependency,
    check_rare_group_gap_readiness,
    check_source_batch_presence,
    check_source_batch_range,
    check_source_batch_stability,
    check_source_batch_freshness,
    check_source_batch_coverage,
    check_source_batch_consistency,
    check_source_batch_risk,
    check_source_batch_confidence,
    check_source_batch_dependency,
    check_source_batch_readiness,
    check_consent_basis_presence,
    check_consent_basis_range,
    check_consent_basis_stability,
    check_consent_basis_freshness,
    check_consent_basis_coverage,
    check_consent_basis_consistency,
    check_consent_basis_risk,
    check_consent_basis_confidence,
    check_consent_basis_dependency,
    check_consent_basis_readiness,
)

RULE_INDEX = {rule.__name__: rule for rule in RULES}

def evaluate(record: DomainRecord, context: Mapping[str, Any] | None = None) -> tuple[RuleResult, ...]:
    context = context or {}
    return tuple(rule(record, context) for rule in RULES)

def summarize(results: tuple[RuleResult, ...]) -> dict[str, Any]:
    if not results:
        return {'score': 0.0, 'passed': 0, 'failed': 0, 'critical': 0}
    return {'score': sum(item.score for item in results) / len(results),
            'passed': sum(item.passed for item in results),
            'failed': sum(not item.passed for item in results),
            'critical': sum(item.severity == 'critical' for item in results)}
