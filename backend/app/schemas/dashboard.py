from pydantic import BaseModel, Field


class AspectStats(BaseModel):
    applicable: int = 0
    partial: int = 0
    not_applicable: int = 0


class RiskConfidenceOut(BaseModel):
    level: str
    primary_reason: str
    evidence_coverage: int
    trace_coverage: int
    official_assessment_coverage: int
    review_freshness: int
    critical_unknown_count: int


class DashboardOut(BaseModel):
    project_id: str
    recommended_attention_level: str = "Unknown"
    product_risk: str = "Unknown"
    process_maturity_risk: str = "Unknown"
    gate_progression_signal: str = "Unknown"
    risk_confidence: RiskConfidenceOut | None = None
    current_gate: str = "Unknown"
    current_gate_official_maturity: int = 0
    current_gate_p0_status: str = "Unknown"
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


class GateReadinessOut(BaseModel):
    official_maturity: int
    p0_status: str
    blocking_gap_count: int
    gate_progression_signal: str


class AuditSnapshotOut(BaseModel):
    recommended_attention_level: str
    product_risk: str
    process_maturity_risk: str
    gate_readiness: GateReadinessOut
    risk_confidence: RiskConfidenceOut
    official_integrated_score: int
    draft_integrated_score: int
    pending_human_confirmation_count: int
    open_risk_count: int
    evidence_gap_count: int


class AuditReportDashboardOut(BaseModel):
    project_id: str
    snapshot_at: str
    current_gate: str
    audit_snapshot: AuditSnapshotOut
    quality_gate_maturity: list[dict] = Field(default_factory=list)
    project_risk_posture: dict = Field(default_factory=dict)
    lifecycle_process_maturity: list[dict] = Field(default_factory=list)
