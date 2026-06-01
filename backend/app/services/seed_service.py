"""Seed the database from data/ JSON reference files.

Idempotent: skips tables that already have rows.
Called at startup and via POST /api/v1/admin/seed-demo.
"""
import json
import uuid
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common import (
    CommonCharacteristic,
    CommonSubcharacteristic,
    CommonAspectMapping,
    ProductLineRecommendation,
    ProductLineRecommendationAspect,
)
from app.models.project import (
    Project, ProjectScopeDecision,
    ArchitectureElement, SoftwareModule,
    QualityGoal, QualityRequirement, SubQualityRequirement,
    TestCase, TestResult, RiskItem,
)
from app.models.enums import (
    ApplicabilityValue, ProductLine, ProjectPhase, QualityAspect,
)

# In Docker the data/ directory is mounted at /data via compose volumes.
# In local dev it sits four levels above this file (adas-quality-trace/data/).
_DOCKER_DATA = Path("/data")
_DEV_DATA = Path(__file__).parent.parent.parent.parent / "data"
DATA_DIR = _DOCKER_DATA if _DOCKER_DATA.exists() else _DEV_DATA

# Aspect ID normalisation — JSON uses "AI Safety" and "AISafety" interchangeably
_ASPECT_ALIASES = {
    "AISafety": "AI Safety",
    "AI Safety": "AI Safety",
    "QM": "QM",
    "FuSA": "FuSA",
    "CS": "CS",
    "SOTIF": "SOTIF",
}


def _norm_aspect(raw: str) -> str:
    return _ASPECT_ALIASES.get(raw, raw)


async def _table_empty(session: AsyncSession, model) -> bool:
    result = await session.execute(select(func.count()).select_from(model))
    return result.scalar_one() == 0


async def seed_common_model(session: AsyncSession) -> bool:
    """Seed common characteristics and subcharacteristics. Returns True if seeded."""
    if not await _table_empty(session, CommonCharacteristic):
        return False

    iso_path = DATA_DIR / "05_ISO25010_Common_Model.json"
    with open(iso_path, encoding="utf-8") as f:
        iso = json.load(f)

    aspect_path = DATA_DIR / "07_ADAS_Quality_Aspect_Mapping.json"
    with open(aspect_path, encoding="utf-8") as f:
        aspect_data = json.load(f)

    # Build subchar_id → [aspects] map from ADAS mapping file
    aspect_map: dict[str, list[str]] = {}
    for mapping in aspect_data.get("mappings", []):
        scid = mapping["qualitySubcharacteristicId"]
        aspects = [_norm_aspect(a) for a in mapping.get("qualityAspects", [])]
        aspect_map[scid] = aspects

    for order, char in enumerate(iso.get("characteristics", [])):
        session.add(CommonCharacteristic(
            id=char["id"],
            name=char["name"],
            description=char.get("description"),
            display_order=order,
        ))
        for sub_order, sub in enumerate(char.get("subcharacteristics", [])):
            session.add(CommonSubcharacteristic(
                id=sub["id"],
                characteristic_id=char["id"],
                name=sub["name"],
                description=sub.get("description"),
                display_order=sub_order,
            ))
            for aspect_str in aspect_map.get(sub["id"], []):
                norm = _norm_aspect(aspect_str)
                if norm:
                    session.add(CommonAspectMapping(subchar_id=sub["id"], aspect=norm))

    await session.commit()
    return True


async def seed_product_line_recommendations(session: AsyncSession) -> bool:
    """Seed product line recommendation rules. Returns True if seeded."""
    if not await _table_empty(session, ProductLineRecommendation):
        return False

    rules_path = DATA_DIR / "06_Product_Line_Recommendation_Rules.json"
    with open(rules_path, encoding="utf-8") as f:
        rules_data = json.load(f)

    for pl_data in rules_data.get("productLines", []):
        product_line_str = pl_data["productLineId"]
        # Validate against known product lines
        if product_line_str not in [pl.value for pl in ProductLine]:
            continue

        for rule in pl_data.get("rules", []):
            rec_id = str(uuid.uuid4())
            rec_app = rule.get("recommendedApplicability", "Applicable")

            rec = ProductLineRecommendation(
                id=rec_id,
                product_line=product_line_str,
                subchar_id=rule["qualitySubcharacteristicId"],
                recommended_applicability=rec_app,
                default_rationale=rule.get("recommendationReason"),
            )
            session.add(rec)

            for aspect_str in rule.get("defaultQualityAspects", []):
                norm = _norm_aspect(aspect_str)
                if norm:
                    session.add(ProductLineRecommendationAspect(
                        recommendation_id=rec_id, aspect=norm
                    ))

    await session.commit()
    return True


async def seed_demo_projects(session: AsyncSession) -> dict:
    """Seed two sample ADAS projects with full trace chain data."""
    demo_projects = [
        {
            "project_id": "PRJ_ADAS_L2_001",
            "name": "ADAS L2 Highway Assist Quality Assessment",
            "product_type": "ADAS ECU",
            "product_line": ProductLine.ADAS,
            "phase": ProjectPhase.Development,
            "system_boundary": "Perception, fusion, AEB warning, LKA warning, HMI warning and degraded operation",
            "assessment_target": "ISO 26262 ASIL-B, SOTIF ISO 21448",
            "selected_aspects": ["QM", "FuSA", "SOTIF"],
        },
        {
            "project_id": "PRJ_ADAS_L3_002",
            "name": "ADAS L3 Traffic Jam Pilot Quality Assessment",
            "product_type": "ADAS ECU",
            "product_line": ProductLine.ADAS,
            "phase": ProjectPhase.Concept,
            "system_boundary": "Traffic jam pilot perception, planning, handover request and degraded operation",
            "assessment_target": "ISO 26262 ASIL-C, SOTIF ISO 21448, ISO PAS 8800",
            "selected_aspects": ["QM", "FuSA", "SOTIF", "AI Safety"],
        },
    ]

    seeded = []
    skipped = []

    for data in demo_projects:
        existing = await session.execute(
            select(Project).where(Project.project_id == data["project_id"])
        )
        if existing.scalar_one_or_none():
            skipped.append(data["project_id"])
            continue

        project_data = {
            **data,
            "product_line": data["product_line"].value,
            "phase": data["phase"].value,
        }
        project = Project(id=str(uuid.uuid4()), **project_data)
        session.add(project)
        await session.flush()

        # Generate scope decisions from ADAS recommendations
        recs_result = await session.execute(
            select(ProductLineRecommendation)
            .where(ProductLineRecommendation.product_line == ProductLine.ADAS.value)
        )
        recs = recs_result.scalars().all()

        scope_map: dict[str, str] = {}  # subchar_id → scope_decision.id
        for rec in recs:
            aspect_rows = await session.execute(
                select(ProductLineRecommendationAspect)
                .where(ProductLineRecommendationAspect.recommendation_id == rec.id)
            )
            aspects = [r.aspect for r in aspect_rows.scalars().all()]
            scope_id = str(uuid.uuid4())
            scope_map[rec.subchar_id] = scope_id
            session.add(ProjectScopeDecision(
                id=scope_id,
                project_id=project.id,
                subchar_id=rec.subchar_id,
                applicability=rec.recommended_applicability,
                rationale=rec.default_rationale,
                recommended_applicability=rec.recommended_applicability,
                recommendation_reason=rec.default_rationale,
                selected_quality_aspects=aspects,
                manual_override=False,
            ))

        await session.flush()

        # ── Architecture Elements & Software Modules ──────────────────────
        ae_data = [
            ("AE-001", "Perception Module",      "Camera and radar sensor fusion pipeline"),
            ("AE-002", "Planning Module",        "Path planning and decision logic"),
            ("AE-003", "HMI Module",             "Driver warning and status display"),
            ("AE-004", "Diagnostic Module",      "Fault detection and degradation control"),
            ("AE-005", "Safety Monitor",         "Functional safety supervision and safe state control"),
        ]
        ae_ids: dict[str, str] = {}
        sm_ids: dict[str, str] = {}

        for element_id, name, desc in ae_data:
            ae_id = str(uuid.uuid4())
            ae_ids[element_id] = ae_id
            session.add(ArchitectureElement(
                id=ae_id, project_id=project.id,
                element_id=element_id, name=name, description=desc,
            ))

        sm_data = [
            ("SM-001", "AE-001", "cam_fusion.cpp",      "Camera-radar object fusion"),
            ("SM-002", "AE-001", "object_tracker.cpp",  "Multi-object tracking"),
            ("SM-003", "AE-002", "aeb_controller.cpp",  "Automatic emergency braking logic"),
            ("SM-004", "AE-002", "lka_controller.cpp",  "Lane keeping assist logic"),
            ("SM-005", "AE-003", "warning_display.cpp", "HMI warning rendering"),
            ("SM-006", "AE-004", "fault_handler.cpp",   "Fault detection and DTC management"),
            ("SM-007", "AE-005", "safe_state.cpp",      "Safe state transition control"),
        ]
        for module_id, ae_key, name, desc in sm_data:
            sm_id = str(uuid.uuid4())
            sm_ids[module_id] = sm_id
            session.add(SoftwareModule(
                id=sm_id, architecture_element_id=ae_ids[ae_key],
                module_id=module_id, name=name, description=desc,
            ))

        await session.flush()

        # ── Trace chain: Goals → Requirements → Sub-Reqs → Test Cases ─────
        # Each entry: (subchar_id, goal_text, req_text, acceptance_criterion,
        #              ae_key, sm_key, tc_description, test_result, aspects)
        trace_data = [
            (
                "QSC_FunctionalSuitability_FunctionalCompleteness",
                "ADAS functions shall cover all required operating scenarios",
                "The system shall implement AEB, LKA, HMI warning and degraded operation as defined in project scope",
                "All four ADAS functions verified in integration test",
                "AE-001", "SM-003",
                "Verify all ADAS functions activate correctly in normal operating conditions",
                "Pass", ["QM", "FuSA", "SOTIF"],
            ),
            (
                "QSC_FunctionalSuitability_FunctionalCorrectness",
                "Perception output shall be correct under defined test conditions",
                "The system shall detect and classify objects with false positive rate below 0.1% in HIL test",
                "False positive rate < 0.1% across 10,000 test scenarios",
                "AE-001", "SM-001",
                "HIL test: measure object detection false positive rate across standard scenario set",
                "Pass", ["QM", "FuSA", "SOTIF", "AI Safety"],
            ),
            (
                "QSC_PerformanceEfficiency_TimeBehaviour",
                "Perception pipeline latency shall not exceed 50ms",
                "The system shall update fused object result within 50ms after valid camera and radar input",
                "P99 latency <= 50ms under maximum object count load",
                "AE-001", "SM-001",
                "Timing test: measure end-to-end perception latency at maximum object count",
                "Pass", ["QM", "FuSA", "SOTIF"],
            ),
            (
                "QSC_Reliability_FaultTolerance",
                "ADAS shall tolerate defined sensor faults without unsafe behaviour",
                "The system shall maintain safe operation when one sensor input is degraded or unavailable",
                "System transitions to degraded mode within 200ms of sensor fault detection",
                "AE-005", "SM-007",
                "Fault injection test: degrade camera input and verify safe state transition timing",
                "Pass", ["QM", "FuSA"],
            ),
            (
                "QSC_Safety_FailSafe",
                "System shall transition to safe state on confirmed hazardous inconsistency",
                "The system shall transition to safe state when confirmed hazardous inconsistency persists beyond fault reaction time",
                "Safe state transition completes within fault reaction time defined in HARA",
                "AE-005", "SM-007",
                "HIL test: inject hazardous sensor inconsistency and measure safe state transition time",
                "Fail", ["FuSA"],
            ),
            (
                "QSC_Safety_RiskIdentification",
                "All hazardous scenarios shall be identified and assessed",
                "The system shall identify all hazardous situations relevant to ADAS operation per ISO 26262 HARA",
                "HARA document covers all operating scenarios defined in ODD",
                "AE-005", "SM-007",
                "Review HARA document coverage against defined ODD scenarios",
                "Not run", ["FuSA", "SOTIF", "AI Safety"],
            ),
            (
                "QSC_Safety_HazardWarning",
                "Driver shall receive timely warning of hazardous conditions",
                "The system shall issue driver warning within 500ms of detecting a hazardous condition",
                "Warning latency < 500ms in 99% of test cases",
                "AE-003", "SM-005",
                "Measure time from hazard detection to HMI warning display",
                "Pass", ["FuSA", "SOTIF"],
            ),
            (
                "QSC_Maintainability_Testability",
                "All safety requirements shall be verifiable through defined test methods",
                "Each safety requirement shall have at least one linked test case with defined pass/fail criterion",
                "100% of safety requirements have linked test cases",
                "AE-004", "SM-006",
                "Verify traceability matrix: all safety requirements linked to test cases",
                "Not run", ["QM", "FuSA", "SOTIF"],
            ),
            (
                "QSC_InteractionCapability_UserErrorProtection",
                "System shall prevent activation in unsupported conditions",
                "The system shall not activate ADAS functions outside the defined ODD",
                "No false activation events in ODD boundary test scenarios",
                "AE-002", "SM-003",
                "ODD boundary test: verify ADAS does not activate outside speed, road type and weather constraints",
                "Pass", ["QM", "FuSA", "SOTIF"],
            ),
            (
                "QSC_Security_Integrity",
                "Safety-critical data shall be protected from unauthorised modification",
                "The system shall detect and reject corrupted or replayed sensor data",
                "Data integrity check detects 100% of injected corruption in test",
                "AE-001", "SM-002",
                "Security test: inject corrupted CAN messages and verify rejection",
                "Not run", ["CS", "FuSA"],
            ),
        ]

        for (subchar_id, goal_text, req_text, criterion,
             ae_key, sm_key, tc_desc, tc_result, aspects) in trace_data:

            scope_id = scope_map.get(subchar_id)
            if not scope_id:
                continue

            # Quality Goal
            goal_id = str(uuid.uuid4())
            goal_num = f"QG-{len(trace_data)}"
            session.add(QualityGoal(
                id=goal_id, scope_decision_id=scope_id,
                goal_id=goal_num, goal_text=goal_text,
            ))

            # Quality Requirement
            req_id = str(uuid.uuid4())
            req_num = f"QR-{trace_data.index((subchar_id, goal_text, req_text, criterion, ae_key, sm_key, tc_desc, tc_result, aspects)) + 1:03d}"
            session.add(QualityRequirement(
                id=req_id, goal_id=goal_id,
                req_id=req_num,
                requirement_text=req_text,
                applicable_aspects=aspects,
                architecture_element_id=ae_ids.get(ae_key),
                risk_level="High" if tc_result == "Fail" else "Medium" if tc_result == "Not run" else "Low",
                evidence_status="Failed" if tc_result == "Fail" else "Missing" if tc_result == "Not run" else "Complete",
            ))

            # Sub-Quality Requirement
            sqr_id = str(uuid.uuid4())
            session.add(SubQualityRequirement(
                id=sqr_id, req_id=req_id,
                sub_req_id=f"SQR-{req_num[3:]}",
                acceptance_criterion=criterion,
                architecture_element_id=ae_ids.get(ae_key),
            ))

            # Test Case
            tc_id = str(uuid.uuid4())
            session.add(TestCase(
                id=tc_id,
                software_module_id=sm_ids.get(sm_key, list(sm_ids.values())[0]),
                sub_req_id=sqr_id,
                tc_id=f"TC-{req_num[3:]}",
                description=tc_desc,
                automated=tc_result == "Pass",
            ))

            # Test Result
            session.add(TestResult(
                id=str(uuid.uuid4()),
                tc_id=tc_id,
                result=tc_result,
                conclusion=f"Result: {tc_result}",
            ))

        await session.flush()

        # ── Risk Items ────────────────────────────────────────────────────
        risks = [
            ("RISK-001", "Fail safe transition time exceeds HARA requirement",
             "Safe state transition test shows timing violation in worst-case scenario",
             "High", "High", "FuSA",
             "Optimise safe state software path and re-test"),
            ("RISK-002", "Security integrity test not yet executed",
             "CAN message integrity verification test has not been run",
             "Medium", "Medium", "CS",
             "Schedule security test in next integration cycle"),
            ("RISK-003", "HARA coverage review pending",
             "Risk identification review against ODD not completed",
             "Medium", "Low", "FuSA",
             "Complete HARA review before system validation gate"),
        ]
        for risk_id, title, desc, sev, lik, aspect, mitigation in risks:
            rl = "High" if sev == "High" and lik == "High" else "Medium"
            session.add(RiskItem(
                id=str(uuid.uuid4()),
                project_id=project.id,
                risk_id=risk_id,
                title=title,
                description=desc,
                quality_aspects=[aspect],
                severity=sev,
                likelihood=lik,
                risk_level=rl,
                status="Open",
                mitigation_action=mitigation,
            ))

        seeded.append(data["project_id"])

    await session.commit()
    return {"seeded": len(seeded), "skipped": len(skipped), "projects": seeded}


async def run_all_seeds(session: AsyncSession) -> None:
    """Run all seed operations at startup. Safe to call multiple times."""
    await seed_common_model(session)
    await seed_product_line_recommendations(session)
