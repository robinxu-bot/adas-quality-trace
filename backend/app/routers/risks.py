"""CRUD routes for Risk Items, Evidence Items, Assessment Findings, and Action Items."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.project import Project, RiskItem, EvidenceItem, AssessmentFinding, ActionItem
from app.models.enums import RiskItemStatus, RiskLevel, FindingStatus, ActionStatus
from app.schemas.risks import (
    RiskItemCreate, RiskItemUpdate, RiskItemOut,
    EvidenceItemCreate, EvidenceItemUpdate, EvidenceItemOut,
    AssessmentFindingCreate, AssessmentFindingUpdate, AssessmentFindingOut,
    ActionItemCreate, ActionItemUpdate, ActionItemOut,
)

router = APIRouter(prefix="/projects", tags=["risks"])


def _uid() -> str:
    return str(uuid.uuid4())


async def _project_or_404(project_id: str, db: AsyncSession) -> Project:
    r = await db.execute(select(Project).where(Project.id == project_id))
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Project not found")
    return p


async def _get_or_404(model, pk: str, db: AsyncSession):
    obj = await db.get(model, pk)
    if not obj:
        raise HTTPException(404, f"{model.__name__} not found")
    return obj


# ─── Risk Items ───────────────────────────────────────────────────────────────

@router.get("/{project_id}/risks", response_model=list[RiskItemOut])
async def list_risks(
    project_id: str,
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    aspect: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _project_or_404(project_id, db)
    stmt = select(RiskItem).where(RiskItem.project_id == project_id)
    if status:
        try:
            stmt = stmt.where(RiskItem.status == RiskItemStatus(status))
        except ValueError:
            raise HTTPException(422, f"Invalid status '{status}'")
    if risk_level:
        try:
            stmt = stmt.where(RiskItem.risk_level == RiskLevel(risk_level))
        except ValueError:
            raise HTTPException(422, f"Invalid risk_level '{risk_level}'")
    if aspect:
        stmt = stmt.where(RiskItem.quality_aspects.contains([aspect]))
    result = await db.execute(stmt.order_by(RiskItem.created_at.desc()))
    return result.scalars().all()


@router.post("/{project_id}/risks", response_model=RiskItemOut, status_code=201)
async def create_risk(project_id: str, body: RiskItemCreate, db: AsyncSession = Depends(get_db)):
    await _project_or_404(project_id, db)
    risk = RiskItem(id=_uid(), project_id=project_id, **body.model_dump())
    db.add(risk)
    await db.commit()
    await db.refresh(risk)
    return risk


@router.put("/{project_id}/risks/{risk_id}", response_model=RiskItemOut)
async def update_risk(
    project_id: str, risk_id: str, body: RiskItemUpdate, db: AsyncSession = Depends(get_db)
):
    risk = await _get_or_404(RiskItem, risk_id, db)
    if risk.project_id != project_id:
        raise HTTPException(404, "Risk not found in this project")
    update = body.model_dump(exclude_none=True)
    # Recompute risk_level if severity or likelihood changed but risk_level not provided
    if ("severity" in update or "likelihood" in update) and "risk_level" not in update:
        from app.schemas.risks import _derive_risk_level
        sev = update.get("severity", risk.severity)
        lik = update.get("likelihood", risk.likelihood)
        update["risk_level"] = _derive_risk_level(sev, lik)
    for f, v in update.items():
        setattr(risk, f, v)
    await db.commit()
    await db.refresh(risk)
    return risk


@router.delete("/{project_id}/risks/{risk_id}", status_code=204)
async def delete_risk(project_id: str, risk_id: str, db: AsyncSession = Depends(get_db)):
    risk = await _get_or_404(RiskItem, risk_id, db)
    if risk.project_id != project_id:
        raise HTTPException(404, "Risk not found in this project")
    await db.delete(risk)
    await db.commit()


# ─── Evidence Items ───────────────────────────────────────────────────────────

@router.get("/{project_id}/evidence", response_model=list[EvidenceItemOut])
async def list_evidence(project_id: str, db: AsyncSession = Depends(get_db)):
    await _project_or_404(project_id, db)
    result = await db.execute(
        select(EvidenceItem)
        .where(EvidenceItem.project_id == project_id)
        .order_by(EvidenceItem.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{project_id}/evidence", response_model=EvidenceItemOut, status_code=201)
async def create_evidence(
    project_id: str, body: EvidenceItemCreate, db: AsyncSession = Depends(get_db)
):
    await _project_or_404(project_id, db)
    ev = EvidenceItem(id=_uid(), project_id=project_id, **body.model_dump())
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return ev


@router.put("/{project_id}/evidence/{evidence_id}", response_model=EvidenceItemOut)
async def update_evidence(
    project_id: str, evidence_id: str, body: EvidenceItemUpdate, db: AsyncSession = Depends(get_db)
):
    ev = await _get_or_404(EvidenceItem, evidence_id, db)
    if ev.project_id != project_id:
        raise HTTPException(404, "Evidence item not found in this project")
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(ev, f, v)
    await db.commit()
    await db.refresh(ev)
    return ev


@router.delete("/{project_id}/evidence/{evidence_id}", status_code=204)
async def delete_evidence(
    project_id: str, evidence_id: str, db: AsyncSession = Depends(get_db)
):
    ev = await _get_or_404(EvidenceItem, evidence_id, db)
    if ev.project_id != project_id:
        raise HTTPException(404, "Evidence item not found in this project")
    await db.delete(ev)
    await db.commit()


# ─── Assessment Findings ──────────────────────────────────────────────────────

@router.get("/{project_id}/findings", response_model=list[AssessmentFindingOut])
async def list_findings(project_id: str, db: AsyncSession = Depends(get_db)):
    await _project_or_404(project_id, db)
    result = await db.execute(
        select(AssessmentFinding)
        .where(AssessmentFinding.project_id == project_id)
        .order_by(AssessmentFinding.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{project_id}/findings", response_model=AssessmentFindingOut, status_code=201)
async def create_finding(
    project_id: str, body: AssessmentFindingCreate, db: AsyncSession = Depends(get_db)
):
    await _project_or_404(project_id, db)
    finding = AssessmentFinding(id=_uid(), project_id=project_id, **body.model_dump())
    db.add(finding)
    await db.commit()
    await db.refresh(finding)
    return finding


@router.put("/{project_id}/findings/{finding_id}", response_model=AssessmentFindingOut)
async def update_finding(
    project_id: str, finding_id: str, body: AssessmentFindingUpdate, db: AsyncSession = Depends(get_db)
):
    finding = await _get_or_404(AssessmentFinding, finding_id, db)
    if finding.project_id != project_id:
        raise HTTPException(404, "Finding not found in this project")
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(finding, f, v)
    await db.commit()
    await db.refresh(finding)
    return finding


@router.delete("/{project_id}/findings/{finding_id}", status_code=204)
async def delete_finding(
    project_id: str, finding_id: str, db: AsyncSession = Depends(get_db)
):
    finding = await _get_or_404(AssessmentFinding, finding_id, db)
    if finding.project_id != project_id:
        raise HTTPException(404, "Finding not found in this project")
    await db.delete(finding)
    await db.commit()


# ─── Action Items ─────────────────────────────────────────────────────────────

@router.get("/{project_id}/actions", response_model=list[ActionItemOut])
async def list_actions(project_id: str, db: AsyncSession = Depends(get_db)):
    await _project_or_404(project_id, db)
    result = await db.execute(
        select(ActionItem)
        .where(ActionItem.project_id == project_id)
        .order_by(ActionItem.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{project_id}/actions", response_model=ActionItemOut, status_code=201)
async def create_action(
    project_id: str, body: ActionItemCreate, db: AsyncSession = Depends(get_db)
):
    await _project_or_404(project_id, db)
    action = ActionItem(id=_uid(), project_id=project_id, **body.model_dump())
    db.add(action)
    await db.commit()
    await db.refresh(action)
    return action


@router.put("/{project_id}/actions/{action_id}", response_model=ActionItemOut)
async def update_action(
    project_id: str, action_id: str, body: ActionItemUpdate, db: AsyncSession = Depends(get_db)
):
    action = await _get_or_404(ActionItem, action_id, db)
    if action.project_id != project_id:
        raise HTTPException(404, "Action not found in this project")
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(action, f, v)
    await db.commit()
    await db.refresh(action)
    return action


@router.delete("/{project_id}/actions/{action_id}", status_code=204)
async def delete_action(
    project_id: str, action_id: str, db: AsyncSession = Depends(get_db)
):
    action = await _get_or_404(ActionItem, action_id, db)
    if action.project_id != project_id:
        raise HTTPException(404, "Action not found in this project")
    await db.delete(action)
    await db.commit()
