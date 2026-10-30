from app.model_service import IntrusionModel


def test_risk_thresholds_are_deterministic():
    assert IntrusionModel.risk_level(0.0) == "LOW"
    assert IntrusionModel.risk_level(0.3499) == "LOW"
    assert IntrusionModel.risk_level(0.35) == "MEDIUM"
    assert IntrusionModel.risk_level(0.6999) == "MEDIUM"
    assert IntrusionModel.risk_level(0.70) == "HIGH"
    assert IntrusionModel.risk_level(1.0) == "HIGH"
