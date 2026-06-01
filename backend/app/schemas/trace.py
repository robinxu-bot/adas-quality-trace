"""Pydantic schemas for the trace chain entities."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.enums import RiskLevel, EvidenceStatus, ReviewStatus


# ─── Architecture Elements ────────────────────────────────────────────────────

class ArchElementCreate(BaseModel):
    element_id: str
    name: str
    description: Optional[str] = None


class ArchElementUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SoftwareModuleOut(BaseModel):
    id: str
    module_id: str
    name: str
    description: Optional[str] = None
    model_config = {"from_attributes": True}


class ArchElementOut(BaseModel):
    id: str
    element_id: str
    name: str
    description: Optional[str] = None
    software_modules: list[SoftwareModuleOut] = []
    model_config = {"from_attributes": True}


# ─── Software Modules ────────────────────────────────────────────────────────

class SoftwareModuleCreate(BaseModel):
    module_id: str
    name: str
    description: Optional[str] = None


class SoftwareModuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# ─── Quality Goals ────────────────────────────────────────────────────────────

class QualityGoalCreate(BaseModel):
    goal_id: str
    goal_text: str
    description: Optional[str] = None


class QualityGoalUpdate(BaseModel):
    goal_text: Optional[str] = None
    description: Optional[str] = None


class QualityGoalOut(BaseModel):
    id: str
    goal_id: str
    goal_text: str
    description: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Quality Requirements ─────────────────────────────────────────────────────

class QualityRequirementCreate(BaseModel):
    req_id: str
    requirement_text: str
    scenario: Optional[str] = None
    applicable_aspects: list[str] = []
    architecture_element_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.Low
    evidence_status: EvidenceStatus = EvidenceStatus.Missing
    owner: Optional[str] = None
    assessment_status: ReviewStatus = ReviewStatus.Draft


class QualityRequirementUpdate(BaseModel):
    requirement_text: Optional[str] = None
    scenario: Optional[str] = None
    applicable_aspects: Optional[list[str]] = None
    architecture_element_id: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    evidence_status: Optional[EvidenceStatus] = None
    owner: Optional[str] = None
    assessment_status: Optional[ReviewStatus] = None


class QualityRequirementOut(BaseModel):
    id: str
    req_id: str
    requirement_text: str
    scenario: Optional[str] = None
    applicable_aspects: list[str]
    architecture_element_id: Optional[str] = None
    architecture_element_name: Optional[str] = None
    risk_level: RiskLevel
    evidence_status: EvidenceStatus
    owner: Optional[str] = None
    assessment_status: ReviewStatus
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Sub-Quality Requirements ─────────────────────────────────────────────────

class SubRequirementCreate(BaseModel):
    sub_req_id: str
    acceptance_criterion: Optional[str] = None
    verification_condition: Optional[str] = None
    input_condition: Optional[str] = None
    expected_output: Optional[str] = None
    measured_value: Optional[str] = None
    pass_fail_criterion: Optional[str] = None
    architecture_element_id: Optional[str] = None


class SubRequirementUpdate(BaseModel):
    acceptance_criterion: Optional[str] = None
    verification_condition: Optional[str] = None
    input_condition: Optional[str] = None
    expected_output: Optional[str] = None
    measured_value: Optional[str] = None
    pass_fail_criterion: Optional[str] = None
    architecture_element_id: Optional[str] = None


class SubRequirementOut(BaseModel):
    id: str
    sub_req_id: str
    acceptance_criterion: Optional[str] = None
    verification_condition: Optional[str] = None
    input_condition: Optional[str] = None
    expected_output: Optional[str] = None
    measured_value: Optional[str] = None
    pass_fail_criterion: Optional[str] = None
    architecture_element_id: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Test Cases ───────────────────────────────────────────────────────────────

class TestCaseCreate(BaseModel):
    tc_id: str
    description: str
    test_objective: Optional[str] = None
    test_method: Optional[str] = None
    input_data: Optional[str] = None
    precondition: Optional[str] = None
    expected_result: Optional[str] = None
    pass_fail_criterion: Optional[str] = None
    evidence_link: Optional[str] = None
    automated: bool = False
    sub_req_id: Optional[str] = None


class TestCaseUpdate(BaseModel):
    description: Optional[str] = None
    test_objective: Optional[str] = None
    test_method: Optional[str] = None
    input_data: Optional[str] = None
    precondition: Optional[str] = None
    expected_result: Optional[str] = None
    pass_fail_criterion: Optional[str] = None
    evidence_link: Optional[str] = None
    automated: Optional[bool] = None
    sub_req_id: Optional[str] = None


class TestCaseOut(BaseModel):
    id: str
    tc_id: str
    description: str
    test_objective: Optional[str] = None
    test_method: Optional[str] = None
    evidence_link: Optional[str] = None
    automated: bool
    sub_req_id: Optional[str] = None
    test_result: Optional["TestResultOut"] = None
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Test Results ─────────────────────────────────────────────────────────────

from datetime import datetime as _dt
from app.models.enums import TestResultValue


class TestResultUpdate(BaseModel):
    result: TestResultValue
    actual_result: Optional[str] = None
    measured_value: Optional[str] = None
    deviation: Optional[str] = None
    conclusion: Optional[str] = None
    evidence_file: Optional[str] = None
    evidence_link: Optional[str] = None
    executed_at: Optional[_dt] = None
    tester: Optional[str] = None
    notes: Optional[str] = None


class TestResultOut(BaseModel):
    id: str
    tc_id: str
    result: TestResultValue
    actual_result: Optional[str] = None
    measured_value: Optional[str] = None
    conclusion: Optional[str] = None
    evidence_link: Optional[str] = None
    executed_at: Optional[_dt] = None
    tester: Optional[str] = None
    model_config = {"from_attributes": True}


# Update forward reference
TestCaseOut.model_rebuild()
