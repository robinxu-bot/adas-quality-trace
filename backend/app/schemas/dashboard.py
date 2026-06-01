from pydantic import BaseModel


class AspectStats(BaseModel):
    applicable: int = 0
    partial: int = 0
    not_applicable: int = 0


class DashboardOut(BaseModel):
    project_id: str
    selected_characteristics_count: int
    selected_subchar_count: int
    excluded_count: int
    open_risk_count: int
    high_risk_count: int
    critical_risk_count: int
    evidence_gap_count: int
    missing_evidence_count: int
    failed_evidence_count: int
    open_finding_count: int
    open_action_count: int
    assessment_readiness: str
    aspect_distribution: dict[str, AspectStats]
