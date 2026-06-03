"""ORM models for Gate Assessment."""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class AssessmentGateDefinition(Base):
    __tablename__ = "assessment_gate_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    gate_id: Mapped[str] = mapped_column(String(8), nullable=False)
    gate_name: Mapped[str] = mapped_column(String(128), nullable=False)
    lifecycle_phase: Mapped[str] = mapped_column(String(128), nullable=False)
    expected_maturity: Mapped[str] = mapped_column(String(128), nullable=False)
    characteristic: Mapped[str] = mapped_column(String(128), nullable=False)
    subcharacteristic: Mapped[str] = mapped_column(String(128), nullable=False)
    subchar_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("common_subcharacteristics.id"), nullable=True
    )
    what_to_check: Mapped[str] = mapped_column(Text, nullable=False)
    pass_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    required_evidence: Mapped[str | None] = mapped_column(Text)
    review_method: Mapped[str | None] = mapped_column(String(256))
    blocking_level: Mapped[str] = mapped_column(String(4), nullable=False)
    responsible_role: Mapped[str | None] = mapped_column(String(128))
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    check_results: Mapped[list["AssessmentCheckResult"]] = relationship(
        back_populates="definition"
    )


class AssessmentRun(Base):
    __tablename__ = "assessment_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    gate_id: Mapped[str] = mapped_column(String(8), nullable=False)
    gate_name: Mapped[str] = mapped_column(String(128), nullable=False)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="In Progress")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    ai_agent_version: Mapped[str | None] = mapped_column(String(64))
    overall_result: Mapped[str | None] = mapped_column(String(32))
    p0_fail_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    p1_fail_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    p2_fail_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    executed_by: Mapped[str | None] = mapped_column(String(128))
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    check_results: Mapped[list["AssessmentCheckResult"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class AssessmentCheckResult(Base):
    __tablename__ = "assessment_check_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_runs.id", ondelete="CASCADE"), nullable=False
    )
    definition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_gate_definitions.id"), nullable=False
    )
    result: Mapped[str] = mapped_column(String(32), nullable=False, default="Open")
    findings: Mapped[str | None] = mapped_column(Text)
    evidence_ref: Mapped[str | None] = mapped_column(Text)
    ai_confidence: Mapped[float | None] = mapped_column(Float)
    ai_rationale: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[str | None] = mapped_column(String(128))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    run: Mapped[AssessmentRun] = relationship(back_populates="check_results")
    definition: Mapped[AssessmentGateDefinition] = relationship(
        back_populates="check_results"
    )
