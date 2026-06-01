from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field
from app.models.enums import (
    ProductLine, ProjectPhase, ApplicabilityValue,
    QualityAspect, ReviewStatus,
)


# --- Scope ---

class ScopeDecisionIn(BaseModel):
    subchar_id: str
    applicability: ApplicabilityValue
    rationale: Optional[str] = None
    selected_quality_aspects: list[str] = Field(default_factory=list)
    manual_override: bool = False
    decision_owner: Optional[str] = None
    decision_date: Optional[date] = None
    review_status: ReviewStatus = ReviewStatus.Draft


class ScopeDecisionOut(BaseModel):
    id: str
    subchar_id: str
    subchar_name: Optional[str] = None
    characteristic_id: Optional[str] = None
    characteristic_name: Optional[str] = None
    applicability: ApplicabilityValue
    rationale: Optional[str] = None
    recommended_applicability: Optional[ApplicabilityValue] = None
    recommendation_reason: Optional[str] = None
    selected_quality_aspects: list[str]
    manual_override: bool
    decision_owner: Optional[str] = None
    decision_date: Optional[date] = None
    review_status: ReviewStatus
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Projects ---

class ProjectCreate(BaseModel):
    project_id: str
    name: str
    product_type: str
    product_line: ProductLine
    phase: ProjectPhase
    system_boundary: str
    assessment_target: Optional[str] = None
    customer: Optional[str] = None
    selected_aspects: list[str] = Field(default_factory=list)
    scope: Optional[list[ScopeDecisionIn]] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    product_type: Optional[str] = None
    phase: Optional[ProjectPhase] = None
    system_boundary: Optional[str] = None
    assessment_target: Optional[str] = None
    customer: Optional[str] = None
    selected_aspects: Optional[list[str]] = None


class ProjectSummary(BaseModel):
    id: str
    project_id: str
    name: str
    product_type: str
    product_line: ProductLine
    phase: ProjectPhase
    system_boundary: str
    assessment_target: Optional[str] = None
    customer: Optional[str] = None
    selected_aspects: list[str]
    selected_subchar_count: int = 0
    open_risk_count: int = 0
    evidence_gap_count: int = 0
    assessment_readiness: str = "Not ready"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetail(ProjectSummary):
    scope: list[ScopeDecisionOut] = Field(default_factory=list)
