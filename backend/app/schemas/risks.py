from datetime import date
from typing import Optional
from pydantic import BaseModel, model_validator
from app.models.enums import RiskLevel, RiskItemStatus, EvidenceStatus, FindingStatus, ActionStatus


# ─── Risk Items ───────────────────────────────────────────────────────────────

class RiskItemCreate(BaseModel):
    risk_id: str
    title: str
    description: str
    quality_aspects: list[str] = []
    severity: RiskLevel
    likelihood: RiskLevel
    risk_level: Optional[RiskLevel] = None   # computed if omitted
    status: RiskItemStatus = RiskItemStatus.Open
    risk_reason: Optional[str] = None
    impact: Optional[str] = None
    mitigation_action: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[date] = None
    target_milestone: Optional[str] = None
    related_subchar_id: Optional[str] = None
    related_req_id: Optional[str] = None
    related_test_result_id: Optional[str] = None

    @model_validator(mode="after")
    def compute_risk_level(self) -> "RiskItemCreate":
        if self.risk_level is None:
            self.risk_level = _derive_risk_level(self.severity, self.likelihood)
        return self


class RiskItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    quality_aspects: Optional[list[str]] = None
    severity: Optional[RiskLevel] = None
    likelihood: Optional[RiskLevel] = None
    risk_level: Optional[RiskLevel] = None
    status: Optional[RiskItemStatus] = None
    risk_reason: Optional[str] = None
    impact: Optional[str] = None
    mitigation_action: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[date] = None
    target_milestone: Optional[str] = None
    related_subchar_id: Optional[str] = None
    related_req_id: Optional[str] = None
    related_test_result_id: Optional[str] = None

    @model_validator(mode="after")
    def recompute_if_needed(self) -> "RiskItemUpdate":
        if self.severity and self.likelihood and self.risk_level is None:
            self.risk_level = _derive_risk_level(self.severity, self.likelihood)
        return self


class RiskItemOut(BaseModel):
    id: str
    risk_id: str
    title: str
    description: str
    quality_aspects: list[str]
    severity: RiskLevel
    likelihood: RiskLevel
    risk_level: RiskLevel
    status: RiskItemStatus
    risk_reason: Optional[str] = None
    impact: Optional[str] = None
    mitigation_action: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[date] = None
    target_milestone: Optional[str] = None
    related_subchar_id: Optional[str] = None
    related_req_id: Optional[str] = None
    related_test_result_id: Optional[str] = None
    model_config = {"from_attributes": True}


# ─── Evidence Items ───────────────────────────────────────────────────────────

class EvidenceItemCreate(BaseModel):
    evidence_id: str
    title: str
    description: Optional[str] = None
    evidence_type: Optional[str] = None
    status: EvidenceStatus = EvidenceStatus.Missing
    source_link: Optional[str] = None
    related_req_id: Optional[str] = None
    related_test_result_id: Optional[str] = None


class EvidenceItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    evidence_type: Optional[str] = None
    status: Optional[EvidenceStatus] = None
    source_link: Optional[str] = None
    related_req_id: Optional[str] = None
    related_test_result_id: Optional[str] = None


class EvidenceItemOut(BaseModel):
    id: str
    evidence_id: str
    title: str
    description: Optional[str] = None
    evidence_type: Optional[str] = None
    status: EvidenceStatus
    source_link: Optional[str] = None
    related_req_id: Optional[str] = None
    related_test_result_id: Optional[str] = None
    model_config = {"from_attributes": True}


# ─── Assessment Findings ──────────────────────────────────────────────────────

class AssessmentFindingCreate(BaseModel):
    finding_id: str
    title: str
    description: str
    finding_type: Optional[str] = None
    severity: RiskLevel = RiskLevel.Low
    status: FindingStatus = FindingStatus.Open
    related_subchar_id: Optional[str] = None
    related_req_id: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[date] = None


class AssessmentFindingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    finding_type: Optional[str] = None
    severity: Optional[RiskLevel] = None
    status: Optional[FindingStatus] = None
    related_subchar_id: Optional[str] = None
    related_req_id: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[date] = None


class AssessmentFindingOut(BaseModel):
    id: str
    finding_id: str
    title: str
    description: str
    finding_type: Optional[str] = None
    severity: RiskLevel
    status: FindingStatus
    related_subchar_id: Optional[str] = None
    related_req_id: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[date] = None
    model_config = {"from_attributes": True}


# ─── Action Items ─────────────────────────────────────────────────────────────

class ActionItemCreate(BaseModel):
    action_id: str
    title: str
    description: Optional[str] = None
    status: ActionStatus = ActionStatus.Open
    priority: RiskLevel = RiskLevel.Medium
    owner: Optional[str] = None
    due_date: Optional[date] = None
    target_milestone: Optional[str] = None
    related_finding_id: Optional[str] = None
    related_risk_id: Optional[str] = None


class ActionItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ActionStatus] = None
    priority: Optional[RiskLevel] = None
    owner: Optional[str] = None
    due_date: Optional[date] = None
    target_milestone: Optional[str] = None
    related_finding_id: Optional[str] = None
    related_risk_id: Optional[str] = None


class ActionItemOut(BaseModel):
    id: str
    action_id: str
    title: str
    description: Optional[str] = None
    status: ActionStatus
    priority: RiskLevel
    owner: Optional[str] = None
    due_date: Optional[date] = None
    target_milestone: Optional[str] = None
    related_finding_id: Optional[str] = None
    related_risk_id: Optional[str] = None
    model_config = {"from_attributes": True}


# ─── Helper ───────────────────────────────────────────────────────────────────

def _derive_risk_level(severity: RiskLevel, likelihood: RiskLevel) -> RiskLevel:
    if severity == RiskLevel.Critical or likelihood == RiskLevel.Critical:
        return RiskLevel.Critical
    levels = {RiskLevel.High: 3, RiskLevel.Medium: 2, RiskLevel.Low: 1}
    score = levels.get(severity, 1) * levels.get(likelihood, 1)
    if score >= 9:
        return RiskLevel.High
    if score <= 1:
        return RiskLevel.Low
    return RiskLevel.Medium
