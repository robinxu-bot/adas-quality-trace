import uuid
from datetime import datetime, date
import sqlalchemy as sa
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, Date, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.enums import (
    QualityAspect, ProductLine, ProjectPhase, ApplicabilityValue,
    RiskLevel, RiskItemStatus, TestResultValue, EvidenceStatus,
    ReviewStatus, FindingStatus, ActionStatus,
)


def _uuid() -> str:
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    product_type: Mapped[str] = mapped_column(String(128), nullable=False)
    product_line: Mapped[ProductLine] = mapped_column(sa.String(64), nullable=False)
    phase: Mapped[ProjectPhase] = mapped_column(sa.String(64), nullable=False)
    system_boundary: Mapped[str] = mapped_column(Text, nullable=False)
    assessment_target: Mapped[str | None] = mapped_column(Text)
    customer: Mapped[str | None] = mapped_column(String(256))
    selected_aspects: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    scope_decisions: Mapped[list["ProjectScopeDecision"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    architecture_elements: Mapped[list["ArchitectureElement"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    risk_items: Mapped[list["RiskItem"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    assessment_findings: Mapped[list["AssessmentFinding"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    action_items: Mapped[list["ActionItem"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectScopeDecision(Base):
    __tablename__ = "project_scope_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    subchar_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("common_subcharacteristics.id"), nullable=False
    )
    applicability: Mapped[ApplicabilityValue] = mapped_column(
        sa.String(64), nullable=False
    )
    rationale: Mapped[str | None] = mapped_column(Text)
    recommended_applicability: Mapped[ApplicabilityValue | None] = mapped_column(
        sa.String(64)
    )
    recommendation_reason: Mapped[str | None] = mapped_column(Text)
    selected_quality_aspects: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    manual_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    decision_owner: Mapped[str | None] = mapped_column(String(128))
    decision_date: Mapped[date | None] = mapped_column(Date)
    review_status: Mapped[ReviewStatus] = mapped_column(
        sa.String(64), nullable=False, default=ReviewStatus.Draft
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="scope_decisions")
    quality_goals: Mapped[list["QualityGoal"]] = relationship(
        back_populates="scope_decision", cascade="all, delete-orphan"
    )


class ArchitectureElement(Base):
    __tablename__ = "architecture_elements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    element_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="architecture_elements")
    software_modules: Mapped[list["SoftwareModule"]] = relationship(
        back_populates="architecture_element", cascade="all, delete-orphan"
    )


class SoftwareModule(Base):
    __tablename__ = "software_modules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    architecture_element_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("architecture_elements.id", ondelete="CASCADE"), nullable=False
    )
    module_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    architecture_element: Mapped[ArchitectureElement] = relationship(
        back_populates="software_modules"
    )
    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="software_module", cascade="all, delete-orphan"
    )


class QualityGoal(Base):
    __tablename__ = "quality_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scope_decision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("project_scope_decisions.id", ondelete="CASCADE"), nullable=False
    )
    goal_id: Mapped[str] = mapped_column(String(64), nullable=False)
    goal_text: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    scope_decision: Mapped[ProjectScopeDecision] = relationship(back_populates="quality_goals")
    quality_requirements: Mapped[list["QualityRequirement"]] = relationship(
        back_populates="goal", cascade="all, delete-orphan"
    )


class QualityRequirement(Base):
    __tablename__ = "quality_requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    goal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("quality_goals.id", ondelete="CASCADE"), nullable=False
    )
    req_id: Mapped[str] = mapped_column(String(64), nullable=False)
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    scenario: Mapped[str | None] = mapped_column(Text)
    applicable_aspects: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    architecture_element_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("architecture_elements.id")
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        sa.String(64), nullable=False, default=RiskLevel.Low
    )
    evidence_status: Mapped[EvidenceStatus] = mapped_column(
        sa.String(64), nullable=False, default=EvidenceStatus.Missing
    )
    owner: Mapped[str | None] = mapped_column(String(128))
    assessment_status: Mapped[ReviewStatus] = mapped_column(
        sa.String(64), nullable=False, default=ReviewStatus.Draft
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    goal: Mapped[QualityGoal] = relationship(back_populates="quality_requirements")
    sub_requirements: Mapped[list["SubQualityRequirement"]] = relationship(
        back_populates="requirement", cascade="all, delete-orphan"
    )


class SubQualityRequirement(Base):
    __tablename__ = "sub_quality_requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    req_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("quality_requirements.id", ondelete="CASCADE"), nullable=False
    )
    sub_req_id: Mapped[str] = mapped_column(String(64), nullable=False)
    acceptance_criterion: Mapped[str | None] = mapped_column(Text)
    verification_condition: Mapped[str | None] = mapped_column(Text)
    input_condition: Mapped[str | None] = mapped_column(Text)
    expected_output: Mapped[str | None] = mapped_column(Text)
    measured_value: Mapped[str | None] = mapped_column(String(256))
    pass_fail_criterion: Mapped[str | None] = mapped_column(Text)
    architecture_element_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("architecture_elements.id")
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    requirement: Mapped[QualityRequirement] = relationship(back_populates="sub_requirements")
    test_cases: Mapped[list["TestCase"]] = relationship(back_populates="sub_requirement")


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    software_module_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("software_modules.id", ondelete="CASCADE"), nullable=False
    )
    sub_req_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sub_quality_requirements.id")
    )
    tc_id: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    test_objective: Mapped[str | None] = mapped_column(Text)
    test_method: Mapped[str | None] = mapped_column(String(128))
    input_data: Mapped[str | None] = mapped_column(Text)
    precondition: Mapped[str | None] = mapped_column(Text)
    expected_result: Mapped[str | None] = mapped_column(Text)
    pass_fail_criterion: Mapped[str | None] = mapped_column(Text)
    evidence_link: Mapped[str | None] = mapped_column(Text)
    automated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    software_module: Mapped[SoftwareModule] = relationship(back_populates="test_cases")
    sub_requirement: Mapped[SubQualityRequirement | None] = relationship(
        back_populates="test_cases"
    )
    test_result: Mapped["TestResult | None"] = relationship(
        back_populates="test_case", cascade="all, delete-orphan"
    )


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tc_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    result: Mapped[TestResultValue] = mapped_column(
        sa.String(64), nullable=False, default=TestResultValue.NotRun
    )
    actual_result: Mapped[str | None] = mapped_column(Text)
    measured_value: Mapped[str | None] = mapped_column(String(256))
    deviation: Mapped[str | None] = mapped_column(Text)
    conclusion: Mapped[str | None] = mapped_column(Text)
    evidence_file: Mapped[str | None] = mapped_column(Text)
    evidence_link: Mapped[str | None] = mapped_column(Text)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tester: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    test_case: Mapped[TestCase] = relationship(back_populates="test_result")


class RiskItem(Base):
    __tablename__ = "risk_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    risk_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quality_aspects: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    severity: Mapped[RiskLevel] = mapped_column(sa.String(64), nullable=False)
    likelihood: Mapped[RiskLevel] = mapped_column(sa.String(64), nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(sa.String(64), nullable=False)
    status: Mapped[RiskItemStatus] = mapped_column(
        sa.String(64), nullable=False, default=RiskItemStatus.Open
    )
    risk_reason: Mapped[str | None] = mapped_column(Text)
    impact: Mapped[str | None] = mapped_column(Text)
    mitigation_action: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(128))
    due_date: Mapped[date | None] = mapped_column(Date)
    target_milestone: Mapped[str | None] = mapped_column(String(128))
    related_subchar_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("common_subcharacteristics.id")
    )
    related_req_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("quality_requirements.id")
    )
    related_test_result_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("test_results.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="risk_items")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    evidence_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    evidence_type: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[EvidenceStatus] = mapped_column(
        sa.String(64), nullable=False, default=EvidenceStatus.Missing
    )
    source_link: Mapped[str | None] = mapped_column(Text)
    related_req_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("quality_requirements.id")
    )
    related_test_result_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("test_results.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="evidence_items")


class AssessmentFinding(Base):
    __tablename__ = "assessment_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    finding_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    finding_type: Mapped[str | None] = mapped_column(String(128))
    severity: Mapped[RiskLevel] = mapped_column(
        sa.String(64), nullable=False, default=RiskLevel.Low
    )
    status: Mapped[FindingStatus] = mapped_column(
        sa.String(64), nullable=False, default=FindingStatus.Open
    )
    related_subchar_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("common_subcharacteristics.id")
    )
    related_req_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("quality_requirements.id")
    )
    owner: Mapped[str | None] = mapped_column(String(128))
    due_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="assessment_findings")


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    action_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ActionStatus] = mapped_column(
        sa.String(64), nullable=False, default=ActionStatus.Open
    )
    priority: Mapped[RiskLevel] = mapped_column(
        sa.String(64), nullable=False, default=RiskLevel.Medium
    )
    owner: Mapped[str | None] = mapped_column(String(128))
    due_date: Mapped[date | None] = mapped_column(Date)
    target_milestone: Mapped[str | None] = mapped_column(String(128))
    related_finding_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("assessment_findings.id")
    )
    related_risk_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("risk_items.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship(back_populates="action_items")
