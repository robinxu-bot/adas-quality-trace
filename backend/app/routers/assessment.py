"""Gate Assessment API routes."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.assessment import (
    AssessmentGateDefinition, AssessmentRun, AssessmentCheckResult,
)
from app.models.project import Project
from app.services.assessment_service import (
    get_next_run_number, recompute_run_counts,
    update_project_readiness, get_assessment_dashboard,
    GATE_NAMES,
)

router = APIRouter(tags=["assessment"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class CheckResultIn(BaseModel):
    definition_id: str
    result: str
    findings: Optional[str] = None
    evidence_ref: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_rationale: Optional[str] = None


class CheckResultPatch(BaseModel):
    result: Optional[str] = None
    findings: Optional[str] = None
    evidence_ref: Optional[str] = None
    reviewed_by: Optional[str] = None


class RunImport(BaseModel):
    gate_id: str
    source: str = "ai_agent"
    ai_agent_version: Optional[str] = None
    executed_by: Optional[str] = None
    notes: Optional[str] = None
    results: list[CheckResultIn]


class RunCreate(BaseModel):
    gate_id: str
    executed_by: Optional[str] = None
    notes: Optional[str] = None


# ─── Gate definitions ──────────────────────────────────────────────────────────

@router.get("/assessment/gates/{gate_id}/definitions")
async def get_gate_definitions(gate_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AssessmentGateDefinition)
        .where(AssessmentGateDefinition.gate_id == gate_id)
        .order_by(AssessmentGateDefinition.display_order)
    )
    defs = result.scalars().all()
    if not defs:
        raise HTTPException(404, f"No definitions found for gate '{gate_id}'")
    return [_def_out(d) for d in defs]


def _def_out(d: AssessmentGateDefinition) -> dict:
    return {
        "id": d.id,
        "gate_id": d.gate_id,
        "gate_name": d.gate_name,
        "lifecycle_phase": d.lifecycle_phase,
        "characteristic": d.characteristic,
        "subcharacteristic": d.subcharacteristic,
        "subchar_id": d.subchar_id,
        "what_to_check": d.what_to_check,
        "pass_criteria": d.pass_criteria,
        "required_evidence": d.required_evidence,
        "review_method": d.review_method,
        "blocking_level": d.blocking_level,
        "responsible_role": d.responsible_role,
    }


# ─── Assessment runs ──────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/assessment/runs")
async def list_runs(
    project_id: str,
    gate_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    await _project_or_404(project_id, db)
    stmt = select(AssessmentRun).where(AssessmentRun.project_id == project_id)
    if gate_id:
        stmt = stmt.where(AssessmentRun.gate_id == gate_id)
    stmt = stmt.order_by(AssessmentRun.executed_at.desc())
    result = await db.execute(stmt)
    return [_run_summary(r) for r in result.scalars().all()]


@router.get("/projects/{project_id}/assessment/runs/{run_id}")
async def get_run(project_id: str, run_id: str, db: AsyncSession = Depends(get_db)):
    run = await _run_or_404(run_id, project_id, db)
    results = await db.execute(
        select(AssessmentCheckResult)
        .options(selectinload(AssessmentCheckResult.definition))
        .where(AssessmentCheckResult.run_id == run_id)
    )
    check_results = results.scalars().all()
    return {
        **_run_summary(run),
        "ai_agent_version": run.ai_agent_version,
        "notes": run.notes,
        "results": [_result_out(cr) for cr in check_results],
    }


@router.post("/projects/{project_id}/assessment/runs", status_code=201)
async def create_manual_run(
    project_id: str, body: RunCreate, db: AsyncSession = Depends(get_db)
):
    await _project_or_404(project_id, db)
    gate_name = GATE_NAMES.get(body.gate_id, body.gate_id)
    run_number = await get_next_run_number(db, project_id, body.gate_id)

    run = AssessmentRun(
        id=str(uuid.uuid4()),
        project_id=project_id,
        gate_id=body.gate_id,
        gate_name=gate_name,
        run_number=run_number,
        status="In Progress",
        source="manual",
        executed_by=body.executed_by,
        notes=body.notes,
    )
    db.add(run)
    await db.flush()

    # Pre-populate Open results for all definitions in this gate
    defs_result = await db.execute(
        select(AssessmentGateDefinition)
        .where(AssessmentGateDefinition.gate_id == body.gate_id)
    )
    for d in defs_result.scalars().all():
        db.add(AssessmentCheckResult(
            id=str(uuid.uuid4()),
            run_id=run.id,
            definition_id=d.id,
            result="Open",
        ))

    await db.commit()
    await db.refresh(run)
    return _run_summary(run)


@router.post("/projects/{project_id}/assessment/runs/import", status_code=201)
async def import_ai_run(
    project_id: str, body: RunImport, db: AsyncSession = Depends(get_db)
):
    await _project_or_404(project_id, db)
    gate_name = GATE_NAMES.get(body.gate_id, body.gate_id)
    run_number = await get_next_run_number(db, project_id, body.gate_id)

    run = AssessmentRun(
        id=str(uuid.uuid4()),
        project_id=project_id,
        gate_id=body.gate_id,
        gate_name=gate_name,
        run_number=run_number,
        status="Completed",
        source=body.source,
        ai_agent_version=body.ai_agent_version,
        executed_by=body.executed_by or "AI Agent",
        notes=body.notes,
        executed_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()

    for item in body.results:
        db.add(AssessmentCheckResult(
            id=str(uuid.uuid4()),
            run_id=run.id,
            definition_id=item.definition_id,
            result=item.result,
            findings=item.findings,
            evidence_ref=item.evidence_ref,
            ai_confidence=item.ai_confidence,
            ai_rationale=item.ai_rationale,
        ))

    await db.flush()
    await recompute_run_counts(db, run)
    readiness = await update_project_readiness(db, project_id)
    await db.commit()

    return {
        **_run_summary(run),
        "assessment_readiness": readiness,
    }


@router.post("/projects/{project_id}/assessment/runs/{run_id}/complete")
async def complete_run(project_id: str, run_id: str, db: AsyncSession = Depends(get_db)):
    run = await _run_or_404(run_id, project_id, db)
    run.status = "Completed"
    await recompute_run_counts(db, run)
    readiness = await update_project_readiness(db, project_id)
    await db.commit()
    return {
        **_run_summary(run),
        "assessment_readiness": readiness,
    }


@router.patch("/projects/{project_id}/assessment/runs/{run_id}/results/{result_id}")
async def update_check_result(
    project_id: str, run_id: str, result_id: str,
    body: CheckResultPatch, db: AsyncSession = Depends(get_db),
):
    cr = await db.get(AssessmentCheckResult, result_id)
    if not cr or cr.run_id != run_id:
        raise HTTPException(404, "Check result not found")
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(cr, f, v)
    if body.reviewed_by:
        cr.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(cr)
    return _result_out(cr)


@router.get("/projects/{project_id}/assessment/dashboard")
async def get_dashboard(project_id: str, db: AsyncSession = Depends(get_db)):
    await _project_or_404(project_id, db)
    return await get_assessment_dashboard(db, project_id)


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _project_or_404(project_id: str, db: AsyncSession) -> Project:
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    return p


async def _run_or_404(run_id: str, project_id: str, db: AsyncSession) -> AssessmentRun:
    run = await db.get(AssessmentRun, run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(404, "Assessment run not found")
    return run


def _run_summary(r: AssessmentRun) -> dict:
    return {
        "run_id": r.id,
        "project_id": r.project_id,
        "gate_id": r.gate_id,
        "gate_name": r.gate_name,
        "run_number": r.run_number,
        "status": r.status,
        "source": r.source,
        "overall_result": r.overall_result,
        "p0_fail_count": r.p0_fail_count,
        "p1_fail_count": r.p1_fail_count,
        "p2_fail_count": r.p2_fail_count,
        "executed_by": r.executed_by,
        "executed_at": r.executed_at.isoformat() if r.executed_at else None,
    }


def _result_out(cr: AssessmentCheckResult) -> dict:
    d = cr.definition
    return {
        "id": cr.id,
        "definition_id": cr.definition_id,
        "characteristic": d.characteristic if d else None,
        "subcharacteristic": d.subcharacteristic if d else None,
        "blocking_level": d.blocking_level if d else None,
        "what_to_check": d.what_to_check if d else None,
        "pass_criteria": d.pass_criteria if d else None,
        "result": cr.result,
        "findings": cr.findings,
        "evidence_ref": cr.evidence_ref,
        "ai_confidence": cr.ai_confidence,
        "ai_rationale": cr.ai_rationale,
        "reviewed_by": cr.reviewed_by,
        "reviewed_at": cr.reviewed_at.isoformat() if cr.reviewed_at else None,
    }
