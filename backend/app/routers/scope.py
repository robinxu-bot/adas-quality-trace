from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project, ProjectScopeDecision
from app.models.common import CommonSubcharacteristic
from app.schemas.project import ScopeDecisionOut, ScopeDecisionIn
from app.services import scope_service

router = APIRouter(prefix="/projects", tags=["scope"])


async def _get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _get_decision_or_404(project_id: str, subchar_id: str, db: AsyncSession) -> ProjectScopeDecision:
    result = await db.execute(
        select(ProjectScopeDecision)
        .where(
            ProjectScopeDecision.project_id == project_id,
            ProjectScopeDecision.subchar_id == subchar_id,
        )
    )
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail=f"Scope decision for '{subchar_id}' not found")
    return decision


async def _enrich_decision(decision: ProjectScopeDecision, db: AsyncSession) -> ScopeDecisionOut:
    sc = await db.get(CommonSubcharacteristic, decision.subchar_id)
    return ScopeDecisionOut(
        id=decision.id,
        subchar_id=decision.subchar_id,
        subchar_name=sc.name if sc else None,
        characteristic_id=sc.characteristic_id if sc else None,
        applicability=decision.applicability,
        rationale=decision.rationale,
        recommended_applicability=decision.recommended_applicability,
        recommendation_reason=decision.recommendation_reason,
        selected_quality_aspects=decision.selected_quality_aspects or [],
        manual_override=decision.manual_override,
        decision_owner=decision.decision_owner,
        decision_date=decision.decision_date,
        review_status=decision.review_status,
        updated_at=decision.updated_at,
    )


@router.get("/{project_id}/scope", response_model=list[ScopeDecisionOut])
async def get_scope(project_id: str, db: AsyncSession = Depends(get_db)):
    await _get_project_or_404(project_id, db)
    result = await db.execute(
        select(ProjectScopeDecision).where(ProjectScopeDecision.project_id == project_id)
    )
    decisions = result.scalars().all()
    return [await _enrich_decision(d, db) for d in decisions]


@router.patch("/{project_id}/scope/{subchar_id}", response_model=ScopeDecisionOut)
async def update_scope_decision(
    project_id: str,
    subchar_id: str,
    body: ScopeDecisionIn,
    db: AsyncSession = Depends(get_db),
):
    await _get_project_or_404(project_id, db)
    decision = await _get_decision_or_404(project_id, subchar_id, db)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(decision, field, value)

    await db.commit()
    await db.refresh(decision)
    return await _enrich_decision(decision, db)


@router.put("/{project_id}/scope", response_model=list[ScopeDecisionOut])
async def batch_update_scope(
    project_id: str,
    body: list[ScopeDecisionIn],
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(project_id, db)

    # Load existing decisions indexed by subchar_id
    result = await db.execute(
        select(ProjectScopeDecision).where(ProjectScopeDecision.project_id == project_id)
    )
    existing = {d.subchar_id: d for d in result.scalars().all()}

    for item in body:
        if item.subchar_id in existing:
            d = existing[item.subchar_id]
            for field, value in item.model_dump(exclude_unset=True).items():
                setattr(d, field, value)
        # Unknown subchar_ids are silently skipped (no new decisions created here)

    await db.commit()

    result = await db.execute(
        select(ProjectScopeDecision).where(ProjectScopeDecision.project_id == project_id)
    )
    decisions = result.scalars().all()
    return [await _enrich_decision(d, db) for d in decisions]


@router.post("/{project_id}/scope/reset", response_model=list[ScopeDecisionOut])
async def reset_scope(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await _get_project_or_404(project_id, db)

    # Delete all existing scope decisions
    result = await db.execute(
        select(ProjectScopeDecision).where(ProjectScopeDecision.project_id == project_id)
    )
    for d in result.scalars().all():
        await db.delete(d)
    await db.flush()

    # Generate fresh default scope
    decisions = await scope_service.generate_default_scope(db, project)
    for d in decisions:
        db.add(d)

    await db.commit()

    result = await db.execute(
        select(ProjectScopeDecision).where(ProjectScopeDecision.project_id == project_id)
    )
    decisions = result.scalars().all()
    return [await _enrich_decision(d, db) for d in decisions]
