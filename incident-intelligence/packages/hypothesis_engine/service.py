from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session
import yaml

from packages.domain_models.models import DataQualityIssue, EvidenceLink, Incident, RootCauseHypothesis


ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def confidence_policy() -> dict:
    return yaml.safe_load((ROOT / "config/confidence_policy_v1.yaml").read_text())


def recalculate_confidence(session: Session, hypothesis: RootCauseHypothesis) -> float:
    policy = confidence_policy()
    evidence = session.scalars(select(EvidenceLink).where(EvidenceLink.hypothesis_id == hypothesis.id)).all()
    incident = session.get(Incident, hypothesis.incident_id)
    issues = session.scalars(select(DataQualityIssue).where(DataQualityIssue.incident_id == hypothesis.incident_id)).all()
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    evidence_details = []
    for link in evidence:
        strength = policy["strength_weights"][link.strength]
        raw = strength * link.weight
        origin = f"evidence:{link.id}" if not link.evidence_origin_group or link.evidence_origin_group == "independent" else link.evidence_origin_group
        grouped[link.relation][origin] += raw
        evidence_details.append({"evidence_id": link.id, "relation": link.relation, "strength": link.strength, "origin_group": origin, "raw_contribution": raw})
    cap = float(policy["origin_group_contribution_cap"])
    effective = {
        relation: sum(min(value, cap) for value in origins.values())
        for relation, origins in grouped.items()
    }
    score = float(policy["base_score"])
    for relation, amount in effective.items():
        score += amount * float(policy["relation_multipliers"].get(relation, 0))
    score = max(0.0, min(1.0, score))
    caps: list[dict] = []
    configured = policy["caps"]
    if any(issue.issue_type in {"missing_expected_source", "incomplete_export"} and issue.resolution_status == "open" for issue in issues):
        caps.append({"reason": "missing critical source", "cap": configured["missing_critical_source"]})
    if any(issue.issue_type == "clock_drift" and issue.resolution_status == "open" for issue in issues):
        caps.append({"reason": "unresolved clock drift", "cap": configured["unresolved_clock_drift"]})
    if any(issue.issue_type == "ambiguous_asset_mapping" and issue.resolution_status == "open" for issue in issues):
        caps.append({"reason": "unreliable mapping", "cap": configured["unreliable_mapping"]})
    if any(link.relation == "contradicts" and link.review_status == "unreviewed" for link in evidence):
        caps.append({"reason": "unreviewed contradiction", "cap": configured["unreviewed_contradiction"]})
    for configured_cap in caps:
        score = min(score, float(configured_cap["cap"]))
    places = int(policy["rounding_decimal_places"])
    hypothesis.confidence = round(score, places)
    hypothesis.confidence_policy_version = policy["version"]
    hypothesis.confidence_derivation = {
        "policy_version": policy["version"],
        "base": policy["base_score"],
        "effective_contributions_by_relation": effective,
        "origin_group_cap": cap,
        "evidence": evidence_details,
        "caps": caps,
        "human_confirmation_required": policy["confirmation_requirements"]["human_confirmation_required"],
        "display": policy["display"],
    }
    if incident:
        incident.confidence = max((row.confidence for row in session.scalars(select(RootCauseHypothesis).where(RootCauseHypothesis.incident_id == incident.id)).all()), default=0)
    session.commit()
    return hypothesis.confidence
