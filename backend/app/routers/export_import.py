"""
Export and Import endpoints.

Export: GET /projects/:id/export
  Returns the complete project data as a JSON document (same shape as /full,
  plus project metadata), suitable for import into another instance.

Import: POST /projects/import
  Restores a project from an export document. Fails if project_id already exists.
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import (
    Project, ProjectScopeDecision,
    ArchitectureElement, SoftwareModule,
    QualityGoal, QualityRequirement, SubQualityRequirement,
    TestCase, TestResult, RiskItem, EvidenceItem,
    AssessmentFinding, ActionItem,
)
from app.models.common import CommonSubcharacteristic
from app.routers.full import get_project_full

router = APIRouter(prefix="/projects", tags=["export/import"])

EXPORT_VERSION = "1.0"


# ─── Export ───────────────────────────────────────────────────────────────────

@router.get("/{project_id}/export")
async def export_project(project_id: str, db: AsyncSession = Depends(get_db)):
    full = await get_project_full(project_id, db)

    # Fetch extra project fields not in FullProjectMeta
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    export_doc = {
        "export_version": EXPORT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "id": project.id,
            "project_id": project.project_id,
            "name": project.name,
            "product_type": project.product_type,
            "product_line": project.product_line,
            "phase": project.phase,
            "system_boundary": project.system_boundary,
            "assessment_target": project.assessment_target,
            "customer": project.customer,
            "selected_aspects": project.selected_aspects or [],
        },
        "scope": [d.model_dump() for d in full.scope],
        "goals": [g.model_dump() for g in full.goals],
        "requirements": [r.model_dump() for r in full.requirements],
        "sub_requirements": [s.model_dump() for s in full.sub_requirements],
        "architecture_elements": [ae.model_dump() for ae in full.architecture_elements],
        "software_modules": [m.model_dump() for m in full.software_modules],
        "test_cases": [tc.model_dump() for tc in full.test_cases],
        "test_results": [tr.model_dump() for tr in full.test_results],
        "risks": [r.model_dump() for r in full.risks],
    }

    filename = f"{project.project_id}.json"
    return JSONResponse(
        content=export_doc,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── Import ───────────────────────────────────────────────────────────────────

@router.post("/import", status_code=201)
async def import_project(body: dict, db: AsyncSession = Depends(get_db)):
    if body.get("export_version") != EXPORT_VERSION:
        raise HTTPException(422, f"Unsupported export version '{body.get('export_version')}'. Expected '{EXPORT_VERSION}'.")

    project_data = body.get("project")
    if not project_data:
        raise HTTPException(422, "Missing 'project' key in import document.")

    # Check duplicate
    existing = await db.execute(
        select(Project).where(Project.project_id == project_data["project_id"])
    )
    if existing.scalar_one_or_none():
        raise HTTPException(422, f"project_id '{project_data['project_id']}' already exists.")

    # Build ID remapping — preserve original UUIDs where possible,
    # but generate new ones if they collide (safe for fresh instances)
    new_project_id = project_data.get("id") or str(uuid.uuid4())

    # Create project
    from app.models.enums import ProductLine, ProjectPhase
    project = Project(
        id=new_project_id,
        project_id=project_data["project_id"],
        name=project_data["name"],
        product_type=project_data.get("product_type", "ADAS ECU"),
        product_line=ProductLine(project_data["product_line"]),
        phase=ProjectPhase(project_data["phase"]),
        system_boundary=project_data["system_boundary"],
        assessment_target=project_data.get("assessment_target"),
        customer=project_data.get("customer"),
        selected_aspects=project_data.get("selected_aspects", []),
    )
    db.add(project)
    await db.flush()

    # Scope decisions
    scope_id_map: dict[str, str] = {}
    for d in body.get("scope", []):
        # Verify subchar exists in our common model
        sc = await db.get(CommonSubcharacteristic, d["subchar_id"])
        if not sc:
            continue  # skip unknown subcharacteristics gracefully
        new_id = str(uuid.uuid4())
        scope_id_map[d["id"]] = new_id
        from app.models.enums import ApplicabilityValue, ReviewStatus
        db.add(ProjectScopeDecision(
            id=new_id,
            project_id=new_project_id,
            subchar_id=d["subchar_id"],
            applicability=ApplicabilityValue(d["applicability"]),
            rationale=d.get("rationale"),
            recommended_applicability=ApplicabilityValue(d["recommended_applicability"]) if d.get("recommended_applicability") else None,
            recommendation_reason=d.get("recommendation_reason"),
            selected_quality_aspects=d.get("selected_quality_aspects", []),
            manual_override=d.get("manual_override", False),
            decision_owner=d.get("decision_owner"),
            review_status=ReviewStatus(d.get("review_status", "Draft")),
        ))

    await db.flush()

    # Architecture elements
    ae_id_map: dict[str, str] = {}
    for ae in body.get("architecture_elements", []):
        new_id = str(uuid.uuid4())
        ae_id_map[ae["id"]] = new_id
        db.add(ArchitectureElement(
            id=new_id, project_id=new_project_id,
            element_id=ae["element_id"], name=ae["name"],
            description=ae.get("description"),
        ))

    await db.flush()

    # Software modules
    sm_id_map: dict[str, str] = {}
    for m in body.get("software_modules", []):
        ae_id = ae_id_map.get(m["architecture_element_id"])
        if not ae_id:
            continue
        new_id = str(uuid.uuid4())
        sm_id_map[m["id"]] = new_id
        db.add(SoftwareModule(
            id=new_id, architecture_element_id=ae_id,
            module_id=m["module_id"], name=m["name"],
            description=m.get("description"),
        ))

    await db.flush()

    # Goals
    goal_id_map: dict[str, str] = {}
    for g in body.get("goals", []):
        scope_id = scope_id_map.get(g["scope_decision_id"])
        if not scope_id:
            continue
        new_id = str(uuid.uuid4())
        goal_id_map[g["id"]] = new_id
        db.add(QualityGoal(
            id=new_id, scope_decision_id=scope_id,
            goal_id=g["goal_id"], goal_text=g["goal_text"],
            description=g.get("description"),
        ))

    await db.flush()

    # Requirements
    req_id_map: dict[str, str] = {}
    for r in body.get("requirements", []):
        goal_id = goal_id_map.get(r["goal_id"])
        if not goal_id:
            continue
        new_id = str(uuid.uuid4())
        req_id_map[r["id"]] = new_id
        ae_id = ae_id_map.get(r.get("architecture_element_id", "")) if r.get("architecture_element_id") else None
        from app.models.enums import RiskLevel, EvidenceStatus, ReviewStatus
        db.add(QualityRequirement(
            id=new_id, goal_id=goal_id,
            req_id=r["req_id"], requirement_text=r["requirement_text"],
            scenario=r.get("scenario"),
            applicable_aspects=r.get("applicable_aspects", []),
            architecture_element_id=ae_id,
            risk_level=RiskLevel(r.get("risk_level", "Low")),
            evidence_status=EvidenceStatus(r.get("evidence_status", "Missing")),
            owner=r.get("owner"),
            assessment_status=ReviewStatus(r.get("assessment_status", "Draft")),
        ))

    await db.flush()

    # Sub-requirements
    subreq_id_map: dict[str, str] = {}
    for s in body.get("sub_requirements", []):
        req_id = req_id_map.get(s["req_id"])
        if not req_id:
            continue
        new_id = str(uuid.uuid4())
        subreq_id_map[s["id"]] = new_id
        ae_id = ae_id_map.get(s.get("architecture_element_id", "")) if s.get("architecture_element_id") else None
        db.add(SubQualityRequirement(
            id=new_id, req_id=req_id,
            sub_req_id=s["sub_req_id"],
            acceptance_criterion=s.get("acceptance_criterion"),
            verification_condition=s.get("verification_condition"),
            architecture_element_id=ae_id,
        ))

    await db.flush()

    # Test cases
    tc_id_map: dict[str, str] = {}
    for tc in body.get("test_cases", []):
        sm_id = sm_id_map.get(tc["software_module_id"])
        if not sm_id:
            continue
        new_id = str(uuid.uuid4())
        tc_id_map[tc["id"]] = new_id
        sub_req_id = subreq_id_map.get(tc.get("sub_req_id", "")) if tc.get("sub_req_id") else None
        db.add(TestCase(
            id=new_id, software_module_id=sm_id,
            tc_id=tc["tc_id"], description=tc["description"],
            sub_req_id=sub_req_id,
            evidence_link=tc.get("evidence_link"),
            automated=tc.get("automated", False),
        ))

    await db.flush()

    # Test results
    from app.models.enums import TestResultValue
    for tr in body.get("test_results", []):
        tc_id = tc_id_map.get(tr.get("tc_id", ""))
        if not tc_id:
            continue
        db.add(TestResult(
            id=str(uuid.uuid4()), tc_id=tc_id,
            result=TestResultValue(tr.get("result", "Not run")),
            evidence_link=tr.get("evidence_link"),
        ))

    # Risks
    from app.models.enums import RiskLevel, RiskItemStatus
    for r in body.get("risks", []):
        req_id = req_id_map.get(r.get("related_req_id", "")) if r.get("related_req_id") else None
        db.add(RiskItem(
            id=str(uuid.uuid4()), project_id=new_project_id,
            risk_id=r["risk_id"], title=r["title"],
            description=r["description"],
            quality_aspects=r.get("quality_aspects", []),
            severity=RiskLevel(r.get("severity", "Low")),
            likelihood=RiskLevel(r.get("likelihood", "Low")),
            risk_level=RiskLevel(r.get("risk_level", "Low")),
            status=RiskItemStatus(r.get("status", "Open")),
            mitigation_action=r.get("mitigation_action"),
            owner=r.get("owner"),
            related_req_id=req_id,
        ))

    await db.commit()

    # Return full project detail
    from app.routers.projects import get_project
    return await get_project(new_project_id, db)
