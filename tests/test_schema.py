import pytest
from pydantic import ValidationError

from schema import TriageDecision

VALID = {
    "category": "billing",
    "priority": "P2",
    "route": "billing-team",
    "rationale": "Customer was charged twice due to a billing system error.",
}


def test_valid_decision():
    d = TriageDecision(**VALID)
    assert d.category == "billing"
    assert d.priority == "P2"
    assert d.route == "billing-team"
    assert d.rationale == VALID["rationale"]


def test_all_categories():
    for cat in ("billing", "bug", "access", "performance", "how-to"):
        TriageDecision(**{**VALID, "category": cat})


def test_all_priorities():
    for pri in ("P1", "P2", "P3", "P4"):
        TriageDecision(**{**VALID, "priority": pri})


def test_all_routes():
    for route in ("billing-team", "bug-team", "access-team", "performance-team", "how-to-team"):
        TriageDecision(**{**VALID, "route": route})


def test_invalid_category():
    with pytest.raises(ValidationError):
        TriageDecision(**{**VALID, "category": "unknown"})


def test_invalid_priority():
    with pytest.raises(ValidationError):
        TriageDecision(**{**VALID, "priority": "P5"})


def test_invalid_route():
    with pytest.raises(ValidationError):
        TriageDecision(**{**VALID, "route": "sales-team"})


def test_missing_field():
    with pytest.raises(ValidationError):
        TriageDecision(category="billing", priority="P1", route="billing-team")


def test_empty_rationale_rejected():
    with pytest.raises(ValidationError):
        TriageDecision(**{**VALID, "rationale": ""})


def test_extra_field_rejected():
    with pytest.raises(ValidationError):
        TriageDecision(**VALID, extra_field="surprise")
