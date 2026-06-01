"""Unit tests for scope_service business logic (no DB required)."""
import pytest
from app.services.scope_service import compute_risk_level
from app.schemas.risks import _derive_risk_level
from app.models.enums import RiskLevel


def test_risk_level_critical_severity():
    assert compute_risk_level("Critical", "Low") == "Critical"


def test_risk_level_critical_likelihood():
    assert compute_risk_level("Low", "Critical") == "Critical"


def test_risk_level_high_both():
    assert compute_risk_level("High", "High") == "High"


def test_risk_level_low_both():
    assert compute_risk_level("Low", "Low") == "Low"


def test_risk_level_medium_mixed():
    assert compute_risk_level("High", "Low") == "Medium"
    assert compute_risk_level("Low", "High") == "Medium"
    assert compute_risk_level("Medium", "Medium") == "Medium"


def test_derive_risk_level_pydantic():
    assert _derive_risk_level(RiskLevel.Critical, RiskLevel.Low) == RiskLevel.Critical
    assert _derive_risk_level(RiskLevel.High, RiskLevel.High) == RiskLevel.High
    assert _derive_risk_level(RiskLevel.Low, RiskLevel.Low) == RiskLevel.Low
    assert _derive_risk_level(RiskLevel.High, RiskLevel.Medium) == RiskLevel.Medium
