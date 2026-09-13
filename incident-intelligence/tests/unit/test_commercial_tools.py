import pytest

from scripts.calculate_reuse import calculate
from scripts.generate_proposal import generate


def test_proposal_contains_scope_data_boundary_acceptance_and_change_control():
    proposal = generate({
        "proposal_id": "P-001", "customer_name": "Example", "engagement_title": "Door incident",
        "offer": "incident_diagnostic", "scope": "One historical door interruption.",
        "required_sources": ["robot log", "operator note"], "timeline": "Ten working days after complete data receipt.",
        "price_eur": 1800, "acceptance_criteria": ["review meeting held", "report delivered"],
    })
    for section in ("Customer responsibilities", "Exclusions and product boundary", "Data handling", "Acceptance criteria", "Change control"):
        assert section in proposal
    assert "No robot commands" in proposal
    assert "qualified review" in proposal


def test_proposal_rejects_incomplete_or_unknown_offer():
    with pytest.raises(ValueError, match="missing proposal fields"): generate({})


def test_reuse_denominator_cannot_hide_manual_or_customer_specific_effort():
    result = calculate({
        "reused_hours": {"ingestion": 7, "timeline": 3},
        "customer_specific_hours": {"mapping": 2},
        "manual_transformation_hours": 3,
    })
    assert result["denominator_hours"] == 15
    assert result["reuse_percentage"] == 66.67
    assert result["passes_target"] is False
