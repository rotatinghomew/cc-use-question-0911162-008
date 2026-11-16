from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class DomainSignal:
    code: str
    score: float
    severity: str
    evidence: dict[str, Any]

def number(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = float(payload.get(key, default))
    except (TypeError, ValueError):
        return default
    return default if value != value or value in (float('inf'), float('-inf')) else value

def ratio(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    value = number(payload, key, default)
    if value > 1.0:
        value /= 100.0
    return max(0.0, min(1.0, value))

def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

def release_quality(payload:Mapping[str,Any])->DomainSignal:
    duplicate=ratio(payload,'duplicate_similarity'); language=ratio(payload,'language_coverage'); sensitive=ratio(payload,'sensitive_entity_rate'); agreement=ratio(payload,'annotation_agreement'); license_ok=ratio(payload,'license_compatibility'); drift=ratio(payload,'split_drift'); rare=ratio(payload,'rare_group_gap')
    consent=bool(str(payload.get('consent_basis','')).strip()); score=clamp((1-duplicate)*.20+language*.15+(1-sensitive)*.15+agreement*.18+license_ok*.20+(1-drift)*.07+(1-rare)*.05)
    severity='critical' if not consent or license_ok<.5 or duplicate>.97 else 'warning' if drift>.3 or rare>.4 else 'info'
    return DomainSignal('release_quality',score,severity,{'duplicate_similarity':duplicate,'license_compatibility':license_ok,'split_drift':drift,'rare_group_gap':rare,'consent_present':consent})

def peer_distribution(records:Iterable[Any],group_field:str='risk_category')->dict[str,Any]:
    rows=[release_quality(getattr(r,'payload',r)) for r in records]
    return {'count':len(rows),'blocked':sum(s.severity=='critical' for s in rows),'minimum':min((s.score for s in rows),default=0.0)}

def augment_context(record:Any,repository:Any)->dict[str,Any]:
    signal=release_quality(record.payload); peers=peer_distribution(repository.list_records())
    return {'domain_signal':signal.score,'domain_severity':signal.severity,'blocked_samples':peers['blocked'],'minimum_quality':peers['minimum']}
