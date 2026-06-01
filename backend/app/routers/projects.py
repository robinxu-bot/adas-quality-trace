import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.project import Project, ProjectScopeDecision
from app.models.common import CommonSubcharacteristic
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectSummary, ProjectDetail, ScopeDecisionOut,
)
from app.services import scope_service

router = APIRouter(prefix="/projects", tags=["projects"])


def _scope_out(decision: ProjectScopeDecision, subchar: CommonSubcharacteristic | None) -> ScopeDecisionOut:
    return ScopeDecisionOut(
        id=decision.id,
        subchar_id=decision.subchar_id,
        subchar_name=subchar.name if subchar else None,
        characteristic_id=subchar.characteristic_id if subchar else None,
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


async def _enrich_summary(session: AsyncSession, project: Project) -> ProjectSummary:
    stats = await scope_service.get_project_summary_stats(session, project.id)
    return ProjectSummary(
        id=project.id,
        project_id=project.project_id,
        name=project.name,
        product_type=project.product_type,
        product_line=project.product_line,
        phase=project.phase,
        system_boundary=project.system_boundary,
        assessment_target=project.assessment_target,
        customer=project.customer,
        selected_aspects=project.selected_aspects or [],
        created_at=project.created_at,
        updated_at=project.updated_at,
        **stats,
    )


@router.get("", response_model=list[ProjectSummary])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return [await _enrich_summary(db, p) for p in projects]


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.scope_decisions))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Load subchar names for scope decoration
    subchar_ids = [d.subchar_id for d in project.scope_decisions]
    subchar_map: dict[str, CommonSubcharacteristic] = {}
    if subchar_ids:
        sc_result = await db.execute(
            select(CommonSubcharacteristic)
            .where(CommonSubcharacteristic.id.in_(subchar_ids))
        )
        subchar_map = {s.id: s for s in sc_result.scalars().all()}

    stats = await scope_service.get_project_summary_stats(db, project.id)
    scope_out = [_scope_out(d, subchar_map.get(d.subchar_id)) for d in project.scope_decisions]

    return ProjectDetail(
        id=project.id,
        project_id=project.project_id,
        name=project.name,
        product_type=project.product_type,
        product_line=project.product_line,
        phase=project.phase,
        system_boundary=project.system_boundary,
        assessment_target=project.assessment_target,
        customer=project.customer,
        selected_aspects=project.selected_aspects or [],
        created_at=project.created_at,
        updated_at=project.updated_at,
        scope=scope_out,
        **stats,
    )


@router.post("", response_model=ProjectDetail, status_code=201)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    # Check duplicate project_id
    existing = await db.execute(
        select(Project).where(Project.project_id == body.project_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=422, detail=f"project_id '{body.project_id}' already exists")

    project = Project(
        id=str(uuid.uuid4()),
        project_id=body.project_id,
        name=body.name,
        product_type=body.product_type,
        product_line=body.product_line,
        phase=body.phase,
        system_boundary=body.system_boundary,
        assessment_target=body.assessment_target,
        customer=body.customer,
        selected_aspects=body.selected_aspects,
    )
    db.add(project)
    await db.flush()  # get project.id

    # Generate or apply scope
    if body.scope:
        decisions = await scope_service.apply_scope_payload(db, project, body.scope)
    else:
        decisions = await scope_service.generate_default_scope(db, project)

    for d in decisions:
        db.add(d)

    await db.commit()
    await db.refresh(project)

    return await get_project(project.id, db)


@router.put("/{project_id}", response_model=ProjectSummary)
async def update_project(project_id: str, body: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return await _enrich_summary(db, project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
