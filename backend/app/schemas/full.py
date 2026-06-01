"""Schema for GET /projects/:id/full — flat structure for Sankey rendering."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import (
    ApplicabilityValue, RiskLevel, EvidenceStatus,
    TestResultValue, RiskItemStatus,
)


class FullProjectMeta(BaseModel):
    id: str
    project_id: str
    name: str
    product_line: str
    phase: str
    selected_aspects: list[str]
    model_config = {"from_attributes": True}


class FullScopeDecision(BaseModel):
    id: str
    subchar_id: str
    subchar_name: Optional[str] = None
    characteristic_id: Optional[str] = None
    characteristic_name: Optional[str] = None
    applicability: ApplicabilityValue
    selected_quality_aspects: list[str] = []
    model_config = {"from_attributes": True}


class FullGoal(BaseModel):
    id: str
    goal_id: str
    goal_text: str
    scope_decision_id: str
    model_config = {"from_attributes": True}


class FullRequirement(BaseModel):
    id: str
    req_id: str
    requirement_text: str
    goal_id: str
    architecture_element_id: Optional[str] = None
    applicable_aspects: list[str] = []
    risk_level: RiskLevel
    evidence_status: EvidenceStatus
    model_config = {"from_attributes": True}


class FullSubRequirement(BaseModel):
    id: str
    sub_req_id: str
    req_id: str
    acceptance_criterion: Optional[str] = None
    architecture_element_id: Optional[str] = None
    model_config = {"from_attributes": True}


class FullArchElement(BaseModel):
    id: str
    element_id: str
    name: str
    description: Optional[str] = None
    model_config = {"from_attributes": True}


class FullSoftwareModule(BaseModel):
    id: str
    module_id: str
    name: str
    architecture_element_id: str
    model_config = {"from_attributes": True}


class FullTestCase(BaseModel):
    id: str
    tc_id: str
    description: str
    software_module_id: str
    sub_req_id: Optional[str] = None
    model_config = {"from_attributes": True}


class FullTestResult(BaseModel):
    id: str
    tc_id: str
    result: TestResultValue
    evidence_link: Optional[str] = None
    model_config = {"from_attributes": True}


class FullRiskItem(BaseModel):
    id: str
    risk_id: str
    title: str
    risk_level: RiskLevel
    status: RiskItemStatus
    quality_aspects: list[str] = []
    related_req_id: Optional[str] = None
    related_subchar_id: Optional[str] = None
    model_config = {"from_attributes": True}


class ProjectFullOut(BaseModel):
    project: FullProjectMeta
    scope: list[FullScopeDecision]
    goals: list[FullGoal]
    requirements: list[FullRequirement]
    sub_requirements: list[FullSubRequirement]
    architecture_elements: list[FullArchElement]
    software_modules: list[FullSoftwareModule]
    test_cases: list[FullTestCase]
    test_results: list[FullTestResult]
    risks: list[FullRiskItem]
