"""
Trace chain CRUD routes:
  Architecture Elements + Software Modules
  Quality Goals → Quality Requirements → Sub-Quality Requirements
  Test Cases + Test Results
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import (
    Project, ProjectScopeDecision,
    ArchitectureElement, SoftwareModule,
    QualityGoal, QualityRequirement, SubQualityRequirement,
    TestCase, TestResult,
)
from app.schemas.trace import (
    ArchElementCreate, ArchElementUpdate, ArchElementOut,
    SoftwareModuleCreate, SoftwareModuleUpdate, SoftwareModuleOut,
    QualityGoalCreate, QualityGoalUpdate, QualityGoalOut,
    QualityRequirementCreate, QualityRequirementUpdate, QualityRequirementOut,
    SubRequirementCreate, SubRequirementUpdate, SubRequirementOut,
    TestCaseCreate, TestCaseUpdate, TestCaseOut,
    TestResultUpdate, TestResultOut,
)

router = APIRouter(prefix="/projects", tags=["trace"])


# ─── helpers ──────────────────────────────────────────────────────────────────

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


def _uid() -> str:
    return str(uuid.uuid4())


# ─── Architecture Elements ────────────────────────────────────────────────────

@router.get("/{project_id}/architecture-elements", response_model=list[ArchElementOut])
async def list_arch_elements(project_id: str, db: AsyncSession = Depends(get_db)):
    await _project_or_404(project_id, db)
    r = await db.execute(
        select(ArchitectureElement)
        .options(selectinload(ArchitectureElement.software_modules))
        .where(ArchitectureElement.project_id == project_id)
        .order_by(ArchitectureElement.display_order)
    )
    return r.scalars().all()


@router.post("/{project_id}/architecture-elements", response_model=ArchElementOut, status_code=201)
async def create_arch_element(
    project_id: str, body: ArchElementCreate, db: AsyncSession = Depends(get_db)
):
    await _project_or_404(project_id, db)
    ae = ArchitectureElement(id=_uid(), project_id=project_id, **body.model_dump())
    db.add(ae)
    await db.commit()
    await db.refresh(ae)
    return ae


@router.put("/{project_id}/architecture-elements/{ae_id}", response_model=ArchElementOut)
async def update_arch_element(
    project_id: str, ae_id: str, body: ArchElementUpdate, db: AsyncSession = Depends(get_db)
):
    ae = await _get_or_404(ArchitectureElement, ae_id, db)
    if ae.project_id != project_id:
        raise HTTPException(404, "Architecture element not found in this project")
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(ae, f, v)
    await db.commit()
    await db.refresh(ae)
    return ae


@router.delete("/{project_id}/architecture-elements/{ae_id}", status_code=204)
async def delete_arch_element(
    project_id: str, ae_id: str, db: AsyncSession = Depends(get_db)
):
    ae = await _get_or_404(ArchitectureElement, ae_id, db)
    if ae.project_id != project_id:
        raise HTTPException(404, "Architecture element not found in this project")
    await db.delete(ae)
    await db.commit()


# ─── Software Modules ─────────────────────────────────────────────────────────

@router.get(
    "/{project_id}/architecture-elements/{ae_id}/software-modules",
    response_model=list[SoftwareModuleOut],
)
async def list_software_modules(
    project_id: str, ae_id: str, db: AsyncSession = Depends(get_db)
):
    ae = await _get_or_404(ArchitectureElement, ae_id, db)
    if ae.project_id != project_id:
        raise HTTPException(404, "Architecture element not found in this project")
    r = await db.execute(
        select(SoftwareModule)
        .where(SoftwareModule.architecture_element_id == ae_id)
        .order_by(SoftwareModule.display_order)
    )
    return r.scalars().all()


@router.post(
    "/{project_id}/architecture-elements/{ae_id}/software-modules",
    response_model=SoftwareModuleOut,
    status_code=201,
)
async def create_software_module(
    project_id: str, ae_id: str, body: SoftwareModuleCreate, db: AsyncSession = Depends(get_db)
):
    ae = await _get_or_404(ArchitectureElement, ae_id, db)
    if ae.project_id != project_id:
        raise HTTPException(404, "Architecture element not found in this project")
    sm = SoftwareModule(id=_uid(), architecture_element_id=ae_id, **body.model_dump())
    db.add(sm)
    await db.commit()
    await db.refresh(sm)
    return sm


@router.put(
    "/{project_id}/architecture-elements/{ae_id}/software-modules/{sm_id}",
    response_model=SoftwareModuleOut,
)
async def update_software_module(
    project_id: str, ae_id: str, sm_id: str,
    body: SoftwareModuleUpdate, db: AsyncSession = Depends(get_db)
):
    sm = await _get_or_404(SoftwareModule, sm_id, db)
    if sm.architecture_element_id != ae_id:
        raise HTTPException(404, "Software module not found in this architecture element")
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(sm, f, v)
    await db.commit()
    await db.refresh(sm)
    return sm


@router.delete(
    "/{project_id}/architecture-elements/{ae_id}/software-modules/{sm_id}",
    status_code=204,
)
async def delete_software_module(
    project_id: str, ae_id: str, sm_id: str, db: AsyncSession = Depends(get_db)
):
    sm = await _get_or_404(SoftwareModule, sm_id, db)
    if sm.architecture_element_id != ae_id:
        raise HTTPException(404, "Software module not found in this architecture element")
    await db.delete(sm)
    await db.commit()


# ─── Quality Goals ────────────────────────────────────────────────────────────

@router.get(
    "/{project_id}/scope/{subchar_id}/goals",
    response_model=list[QualityGoalOut],
)
async def list_goals(project_id: str, subchar_id: str, db: AsyncSession = Depends(get_db)):
    # Locate scope decision
    r = await db.execute(
        select(ProjectScopeDecision).where(
            ProjectScopeDecision.project_id == project_id,
            ProjectScopeDecision.subchar_id == subchar_id,
        )
    )
    decision = r.scalar_one_or_none()
    if not decision:
        raise HTTPException(404, "Scope decision not found")
    r = await db.execute(
        select(QualityGoal)
        .where(QualityGoal.scope_decision_id == decision.id)
        .order_by(QualityGoal.display_order)
    )
    return r.scalars().all()


@router.post(
    "/{project_id}/scope/{subchar_id}/goals",
    response_model=QualityGoalOut,
    status_code=201,
)
async def create_goal(
    project_id: str, subchar_id: str, body: QualityGoalCreate, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(
        select(ProjectScopeDecision).where(
            ProjectScopeDecision.project_id == project_id,
            ProjectScopeDecision.subchar_id == subchar_id,
        )
    )
    decision = r.scalar_one_or_none()
    if not decision:
        raise HTTPException(404, "Scope decision not found")
    goal = QualityGoal(id=_uid(), scope_decision_id=decision.id, **body.model_dump())
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


@router.put(
    "/{project_id}/scope/{subchar_id}/goals/{goal_id}",
    response_model=QualityGoalOut,
)
async def update_goal(
    project_id: str, subchar_id: str, goal_id: str,
    body: QualityGoalUpdate, db: AsyncSession = Depends(get_db)
):
    goal = await _get_or_404(QualityGoal, goal_id, db)
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(goal, f, v)
    await db.commit()
    await db.refresh(goal)
    return goal


@router.delete("/{project_id}/scope/{subchar_id}/goals/{goal_id}", status_code=204)
async def delete_goal(
    project_id: str, subchar_id: str, goal_id: str, db: AsyncSession = Depends(get_db)
):
    goal = await _get_or_404(QualityGoal, goal_id, db)
    await db.delete(goal)
    await db.commit()


# ─── Quality Requirements ─────────────────────────────────────────────────────

@router.get(
    "/{project_id}/scope/{subchar_id}/goals/{goal_id}/requirements",
    response_model=list[QualityRequirementOut],
)
async def list_requirements(
    project_id: str, subchar_id: str, goal_id: str, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(
        select(QualityRequirement)
        .where(QualityRequirement.goal_id == goal_id)
        .order_by(QualityRequirement.display_order)
    )
    reqs = r.scalars().all()
    return [await _enrich_req(req, db) for req in reqs]


@router.post(
    "/{project_id}/scope/{subchar_id}/goals/{goal_id}/requirements",
    response_model=QualityRequirementOut,
    status_code=201,
)
async def create_requirement(
    project_id: str, subchar_id: str, goal_id: str,
    body: QualityRequirementCreate, db: AsyncSession = Depends(get_db)
):
    await _get_or_404(QualityGoal, goal_id, db)
    req = QualityRequirement(id=_uid(), goal_id=goal_id, **body.model_dump())
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return await _enrich_req(req, db)


@router.put(
    "/{project_id}/scope/{subchar_id}/goals/{goal_id}/requirements/{req_id}",
    response_model=QualityRequirementOut,
)
async def update_requirement(
    project_id: str, subchar_id: str, goal_id: str, req_id: str,
    body: QualityRequirementUpdate, db: AsyncSession = Depends(get_db)
):
    req = await _get_or_404(QualityRequirement, req_id, db)
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(req, f, v)
    await db.commit()
    await db.refresh(req)
    return await _enrich_req(req, db)


@router.delete(
    "/{project_id}/scope/{subchar_id}/goals/{goal_id}/requirements/{req_id}",
    status_code=204,
)
async def delete_requirement(
    project_id: str, subchar_id: str, goal_id: str, req_id: str,
    db: AsyncSession = Depends(get_db)
):
    req = await _get_or_404(QualityRequirement, req_id, db)
    await db.delete(req)
    await db.commit()


async def _enrich_req(req: QualityRequirement, db: AsyncSession) -> QualityRequirementOut:
    ae_name = None
    if req.architecture_element_id:
        ae = await db.get(ArchitectureElement, req.architecture_element_id)
        ae_name = ae.name if ae else None
    return QualityRequirementOut(
        id=req.id,
        req_id=req.req_id,
        requirement_text=req.requirement_text,
        scenario=req.scenario,
        applicable_aspects=req.applicable_aspects or [],
        architecture_element_id=req.architecture_element_id,
        architecture_element_name=ae_name,
        risk_level=req.risk_level,
        evidence_status=req.evidence_status,
        owner=req.owner,
        assessment_status=req.assessment_status,
        created_at=req.created_at,
    )


# ─── Sub-Quality Requirements ─────────────────────────────────────────────────

@router.get(
    "/{project_id}/requirements/{req_id}/sub-requirements",
    response_model=list[SubRequirementOut],
)
async def list_sub_requirements(
    project_id: str, req_id: str, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(
        select(SubQualityRequirement)
        .where(SubQualityRequirement.req_id == req_id)
        .order_by(SubQualityRequirement.display_order)
    )
    return r.scalars().all()


@router.post(
    "/{project_id}/requirements/{req_id}/sub-requirements",
    response_model=SubRequirementOut,
    status_code=201,
)
async def create_sub_requirement(
    project_id: str, req_id: str, body: SubRequirementCreate, db: AsyncSession = Depends(get_db)
):
    await _get_or_404(QualityRequirement, req_id, db)
    sub = SubQualityRequirement(id=_uid(), req_id=req_id, **body.model_dump())
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.put(
    "/{project_id}/requirements/{req_id}/sub-requirements/{sub_id}",
    response_model=SubRequirementOut,
)
async def update_sub_requirement(
    project_id: str, req_id: str, sub_id: str,
    body: SubRequirementUpdate, db: AsyncSession = Depends(get_db)
):
    sub = await _get_or_404(SubQualityRequirement, sub_id, db)
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(sub, f, v)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.delete(
    "/{project_id}/requirements/{req_id}/sub-requirements/{sub_id}",
    status_code=204,
)
async def delete_sub_requirement(
    project_id: str, req_id: str, sub_id: str, db: AsyncSession = Depends(get_db)
):
    sub = await _get_or_404(SubQualityRequirement, sub_id, db)
    await db.delete(sub)
    await db.commit()


# ─── Test Cases ───────────────────────────────────────────────────────────────

@router.get(
    "/{project_id}/software-modules/{sm_id}/test-cases",
    response_model=list[TestCaseOut],
)
async def list_test_cases(
    project_id: str, sm_id: str, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(
        select(TestCase)
        .options(selectinload(TestCase.test_result))
        .where(TestCase.software_module_id == sm_id)
        .order_by(TestCase.display_order)
    )
    return r.scalars().all()


@router.post(
    "/{project_id}/software-modules/{sm_id}/test-cases",
    response_model=TestCaseOut,
    status_code=201,
)
async def create_test_case(
    project_id: str, sm_id: str, body: TestCaseCreate, db: AsyncSession = Depends(get_db)
):
    await _get_or_404(SoftwareModule, sm_id, db)
    tc = TestCase(id=_uid(), software_module_id=sm_id, **body.model_dump())
    db.add(tc)
    await db.commit()
    await db.refresh(tc)
    return tc


@router.put(
    "/{project_id}/software-modules/{sm_id}/test-cases/{tc_id}",
    response_model=TestCaseOut,
)
async def update_test_case(
    project_id: str, sm_id: str, tc_id: str,
    body: TestCaseUpdate, db: AsyncSession = Depends(get_db)
):
    tc = await _get_or_404(TestCase, tc_id, db)
    if tc.software_module_id != sm_id:
        raise HTTPException(404, "Test case not found in this software module")
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(tc, f, v)
    await db.commit()
    await db.refresh(tc)
    return tc


@router.delete(
    "/{project_id}/software-modules/{sm_id}/test-cases/{tc_id}",
    status_code=204,
)
async def delete_test_case(
    project_id: str, sm_id: str, tc_id: str, db: AsyncSession = Depends(get_db)
):
    tc = await _get_or_404(TestCase, tc_id, db)
    if tc.software_module_id != sm_id:
        raise HTTPException(404, "Test case not found in this software module")
    await db.delete(tc)
    await db.commit()


# ─── Test Results ─────────────────────────────────────────────────────────────

@router.get(
    "/{project_id}/test-cases/{tc_id}/result",
    response_model=TestResultOut,
)
async def get_test_result(
    project_id: str, tc_id: str, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(select(TestResult).where(TestResult.tc_id == tc_id))
    result = r.scalar_one_or_none()
    if not result:
        raise HTTPException(404, "No test result for this test case")
    return result


@router.put(
    "/{project_id}/test-cases/{tc_id}/result",
    response_model=TestResultOut,
)
async def upsert_test_result(
    project_id: str, tc_id: str, body: TestResultUpdate, db: AsyncSession = Depends(get_db)
):
    await _get_or_404(TestCase, tc_id, db)
    r = await db.execute(select(TestResult).where(TestResult.tc_id == tc_id))
    tr = r.scalar_one_or_none()

    if tr:
        for f, v in body.model_dump(exclude_none=True).items():
            setattr(tr, f, v)
    else:
        tr = TestResult(id=_uid(), tc_id=tc_id, **body.model_dump())
        db.add(tr)

    await db.commit()
    await db.refresh(tr)
    return tr
