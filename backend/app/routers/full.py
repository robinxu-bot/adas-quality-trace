"""GET /projects/:id/full — returns the complete flat project data tree for Sankey rendering."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import (
    Project, ProjectScopeDecision,
    ArchitectureElement, SoftwareModule,
    QualityGoal, QualityRequirement, SubQualityRequirement,
    TestCase, TestResult, RiskItem,
)
from app.models.common import CommonSubcharacteristic
from app.schemas.full import ProjectFullOut, FullScopeDecision

router = APIRouter(prefix="/projects", tags=["full"])


@router.get("/{project_id}/full", response_model=ProjectFullOut)
async def get_project_full(project_id: str, db: AsyncSession = Depends(get_db)):
    # Project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    # Scope decisions + subchar names
    scope_result = await db.execute(
        select(ProjectScopeDecision).where(ProjectScopeDecision.project_id == project_id)
    )
    scope_decisions = scope_result.scalars().all()

    subchar_ids = [d.subchar_id for d in scope_decisions]
    subchar_map: dict[str, CommonSubcharacteristic] = {}
    if subchar_ids:
        sc_result = await db.execute(
            select(CommonSubcharacteristic)
            .where(CommonSubcharacteristic.id.in_(subchar_ids))
        )
        subchar_map = {s.id: s for s in sc_result.scalars().all()}

    # Build scope output with enriched names
    scope_out = []
    for d in scope_decisions:
        sc = subchar_map.get(d.subchar_id)
        scope_out.append(FullScopeDecision(
            id=d.id,
            subchar_id=d.subchar_id,
            subchar_name=sc.name if sc else None,
            characteristic_id=sc.characteristic_id if sc else None,
            applicability=d.applicability,
            selected_quality_aspects=d.selected_quality_aspects or [],
        ))

    # Fetch characteristic names for the unique characteristic_ids
    char_ids = {d.characteristic_id for d in scope_out if d.characteristic_id}
    char_map: dict[str, str] = {}
    if char_ids:
        from app.models.common import CommonCharacteristic
        char_result = await db.execute(
            select(CommonCharacteristic).where(CommonCharacteristic.id.in_(char_ids))
        )
        char_map = {c.id: c.name for c in char_result.scalars().all()}

    for d in scope_out:
        if d.characteristic_id:
            d.characteristic_name = char_map.get(d.characteristic_id)

    # Quality Goals
    scope_ids = [d.id for d in scope_decisions]
    goals_result = await db.execute(
        select(QualityGoal).where(QualityGoal.scope_decision_id.in_(scope_ids))
    ) if scope_ids else None
    goals = goals_result.scalars().all() if goals_result else []

    # Quality Requirements
    goal_ids = [g.id for g in goals]
    reqs_result = await db.execute(
        select(QualityRequirement).where(QualityRequirement.goal_id.in_(goal_ids))
    ) if goal_ids else None
    reqs = reqs_result.scalars().all() if reqs_result else []

    # Sub-Quality Requirements
    req_ids = [r.id for r in reqs]
    sub_reqs_result = await db.execute(
        select(SubQualityRequirement).where(SubQualityRequirement.req_id.in_(req_ids))
    ) if req_ids else None
    sub_reqs = sub_reqs_result.scalars().all() if sub_reqs_result else []

    # Architecture Elements
    ae_result = await db.execute(
        select(ArchitectureElement).where(ArchitectureElement.project_id == project_id)
    )
    arch_elements = ae_result.scalars().all()

    # Software Modules
    ae_ids = [ae.id for ae in arch_elements]
    modules_result = await db.execute(
        select(SoftwareModule).where(SoftwareModule.architecture_element_id.in_(ae_ids))
    ) if ae_ids else None
    modules = modules_result.scalars().all() if modules_result else []

    # Test Cases
    sm_ids = [m.id for m in modules]
    tc_result = await db.execute(
        select(TestCase).where(TestCase.software_module_id.in_(sm_ids))
    ) if sm_ids else None
    test_cases = tc_result.scalars().all() if tc_result else []

    # Test Results
    tc_ids = [tc.id for tc in test_cases]
    tr_result = await db.execute(
        select(TestResult).where(TestResult.tc_id.in_(tc_ids))
    ) if tc_ids else None
    test_results = tr_result.scalars().all() if tr_result else []

    # Risk Items
    risk_result = await db.execute(
        select(RiskItem).where(RiskItem.project_id == project_id)
    )
    risks = risk_result.scalars().all()

    return ProjectFullOut(
        project=project,
        scope=scope_out,
        goals=goals,
        requirements=reqs,
        sub_requirements=sub_reqs,
        architecture_elements=arch_elements,
        software_modules=modules,
        test_cases=test_cases,
        test_results=test_results,
        risks=risks,
    )
