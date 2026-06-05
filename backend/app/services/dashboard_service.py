"""Dashboard metric computation for a project."""
import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project import (
    ProjectScopeDecision, RiskItem, EvidenceItem,
    AssessmentFinding, ActionItem, TestResult, TestCase,
    SoftwareModule, ArchitectureElement, QualityGoal, QualityRequirement,
    SubQualityRequirement,
)
from app.models.assessment import (
    AssessmentGateDefinition, AssessmentRun, AssessmentCheckResult,
)
from app.models.common import CommonSubcharacteristic, CommonCharacteristic
from app.models.enums import (
    ApplicabilityValue, RiskItemStatus, RiskLevel,
    FindingStatus, ActionStatus, TestResultValue, EvidenceStatus, ReviewStatus,
)
from app.schemas.dashboard import (
    DashboardOut,
    AspectStats,
    AssessmentDashboardOut,
    AuditSnapshotOut,
    GateReadinessOut,
    RiskConfidenceOut,
)
from app.services.gate_seed_service import seed_gate_definitions
from app.constants import ASPECTS, INCLUDED_APPLICABILITY, EXCLUDED_APPLICABILITY


async def compute_dashboard(session: AsyncSession, project_id: str) -> DashboardOut:
    project_result = await session.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()

    # --- Scope counts ---
    scope_result = await session.execute(
        select(ProjectScopeDecision)
        .where(ProjectScopeDecision.project_id == project_id)
    )
    scope = scope_result.scalars().all()

    included = [d for d in scope if d.applicability in INCLUDED_APPLICABILITY]
    excluded = [d for d in scope if d.applicability in EXCLUDED_APPLICABILITY]

    # Distinct characteristics in included scope — look up via common_subcharacteristics
    from app.models.common import CommonSubcharacteristic
    if included:
        subchar_ids = [d.subchar_id for d in included]
        sc_result = await session.execute(
            select(CommonSubcharacteristic.characteristic_id)
            .where(CommonSubcharacteristic.id.in_(subchar_ids))
            .distinct()
        )
        char_ids = set(sc_result.scalars().all())
    else:
        char_ids = set()

    # Aspect distribution
    aspect_dist: dict[str, AspectStats] = {a: AspectStats() for a in ASPECTS}
    for d in scope:
        for aspect in (d.selected_quality_aspects or []):
            if aspect not in aspect_dist:
                continue
            if d.applicability == ApplicabilityValue.Applicable:
                aspect_dist[aspect].applicable += 1
            elif d.applicability == ApplicabilityValue.PartiallyApplicable:
                aspect_dist[aspect].partial += 1
            else:
                aspect_dist[aspect].not_applicable += 1

    # --- Risk counts ---
    open_risks_result = await session.execute(
        select(func.count())
        .select_from(RiskItem)
        .where(RiskItem.project_id == project_id, RiskItem.status == RiskItemStatus.Open)
    )
    open_risk_count = open_risks_result.scalar_one()

    high_risks_result = await session.execute(
        select(func.count())
        .select_from(RiskItem)
        .where(
            RiskItem.project_id == project_id,
            RiskItem.status == RiskItemStatus.Open,
            RiskItem.risk_level == RiskLevel.High,
        )
    )
    high_risk_count = high_risks_result.scalar_one()

    critical_risks_result = await session.execute(
        select(func.count())
        .select_from(RiskItem)
        .where(
            RiskItem.project_id == project_id,
            RiskItem.status == RiskItemStatus.Open,
            RiskItem.risk_level == RiskLevel.Critical,
        )
    )
    critical_risk_count = critical_risks_result.scalar_one()

    # --- Evidence gap counts (test cases with non-passing results) ---
    gap_result = await session.execute(
        select(func.count())
        .select_from(TestResult)
        .join(TestCase, TestResult.tc_id == TestCase.id)
        .join(SoftwareModule, TestCase.software_module_id == SoftwareModule.id)
        .join(ArchitectureElement, SoftwareModule.architecture_element_id == ArchitectureElement.id)
        .where(
            ArchitectureElement.project_id == project_id,
            TestResult.result.in_([
                TestResultValue.Fail, TestResultValue.Blocked, TestResultValue.NotRun,
            ]),
        )
    )
    evidence_gap_count = gap_result.scalar_one()

    missing_result = await session.execute(
        select(func.count())
        .select_from(TestResult)
        .join(TestCase, TestResult.tc_id == TestCase.id)
        .join(SoftwareModule, TestCase.software_module_id == SoftwareModule.id)
        .join(ArchitectureElement, SoftwareModule.architecture_element_id == ArchitectureElement.id)
        .where(
            ArchitectureElement.project_id == project_id,
            TestResult.result == TestResultValue.NotRun,
        )
    )
    missing_evidence_count = missing_result.scalar_one()

    failed_result = await session.execute(
        select(func.count())
        .select_from(TestResult)
        .join(TestCase, TestResult.tc_id == TestCase.id)
        .join(SoftwareModule, TestCase.software_module_id == SoftwareModule.id)
        .join(ArchitectureElement, SoftwareModule.architecture_element_id == ArchitectureElement.id)
        .where(
            ArchitectureElement.project_id == project_id,
            TestResult.result == TestResultValue.Fail,
        )
    )
    failed_evidence_count = failed_result.scalar_one()

    # --- Findings and actions ---
    finding_result = await session.execute(
        select(func.count())
        .select_from(AssessmentFinding)
        .where(
            AssessmentFinding.project_id == project_id,
            AssessmentFinding.status == FindingStatus.Open,
        )
    )
    open_finding_count = finding_result.scalar_one()

    action_result = await session.execute(
        select(func.count())
        .select_from(ActionItem)
        .where(
            ActionItem.project_id == project_id,
            ActionItem.status == ActionStatus.Open,
        )
    )
    open_action_count = action_result.scalar_one()

    # --- Assessment readiness ---
    readiness = _compute_readiness(critical_risk_count + high_risk_count, evidence_gap_count)

    # --- Risk confidence inputs ---
    evidence_total_result = await session.execute(
        select(func.count())
        .select_from(EvidenceItem)
        .where(EvidenceItem.project_id == project_id)
    )
    evidence_total = evidence_total_result.scalar_one()

    usable_evidence_result = await session.execute(
        select(func.count())
        .select_from(EvidenceItem)
        .where(
            EvidenceItem.project_id == project_id,
            EvidenceItem.status.in_([EvidenceStatus.Complete, EvidenceStatus.Partial]),
        )
    )
    usable_evidence_count = usable_evidence_result.scalar_one()

    total_subreq_result = await session.execute(
        select(func.count())
        .select_from(SubQualityRequirement)
        .join(QualityRequirement, SubQualityRequirement.req_id == QualityRequirement.id)
        .join(QualityGoal, QualityRequirement.goal_id == QualityGoal.id)
        .join(ProjectScopeDecision, QualityGoal.scope_decision_id == ProjectScopeDecision.id)
        .where(ProjectScopeDecision.project_id == project_id)
    )
    trace_total = total_subreq_result.scalar_one()

    traced_subreq_result = await session.execute(
        select(func.count(func.distinct(TestCase.sub_req_id)))
        .select_from(TestCase)
        .join(SubQualityRequirement, TestCase.sub_req_id == SubQualityRequirement.id)
        .join(QualityRequirement, SubQualityRequirement.req_id == QualityRequirement.id)
        .join(QualityGoal, QualityRequirement.goal_id == QualityGoal.id)
        .join(ProjectScopeDecision, QualityGoal.scope_decision_id == ProjectScopeDecision.id)
        .where(ProjectScopeDecision.project_id == project_id)
    )
    trace_linked_count = traced_subreq_result.scalar_one()

    dashboard = DashboardOut(
        project_id=project_id,
        selected_characteristics_count=len(char_ids),
        selected_subchar_count=len(included),
        excluded_count=len(excluded),
        open_risk_count=open_risk_count,
        high_risk_count=high_risk_count,
        critical_risk_count=critical_risk_count,
        evidence_gap_count=evidence_gap_count,
        missing_evidence_count=missing_evidence_count,
        failed_evidence_count=failed_evidence_count,
        open_finding_count=open_finding_count,
        open_action_count=open_action_count,
        assessment_readiness=readiness,
        aspect_distribution=aspect_dist,
    )

    risk_confidence = _compute_initial_risk_confidence(
        dashboard,
        evidence_total=evidence_total,
        usable_evidence_count=usable_evidence_count,
        trace_total=trace_total,
        trace_linked_count=trace_linked_count,
        official_reviewed_count=_reviewed_count(included),
        official_total=len(included),
        fresh_review_count=_fresh_review_count(included),
        review_total=len(included),
    )
    product_risk = _compute_initial_product_risk(dashboard)
    gate_signal = _compute_initial_gate_signal(dashboard, risk_confidence.level)
    process_risk = "Unknown"

    dashboard.recommended_attention_level = _compute_initial_attention(
        product_risk=product_risk,
        process_risk=process_risk,
        gate_signal=gate_signal,
        risk_confidence=risk_confidence.level,
        critical_risk_count=critical_risk_count,
    )
    dashboard.product_risk = product_risk
    dashboard.process_maturity_risk = process_risk
    dashboard.gate_progression_signal = gate_signal
    dashboard.risk_confidence = risk_confidence
    dashboard.current_gate = _infer_current_gate(_enum_value(project.phase)) if project else "Unknown"
    dashboard.current_gate_official_maturity = _initial_official_score(dashboard)
    dashboard.current_gate_p0_status = "Unknown"

    return dashboard


def _compute_readiness(open_high_plus: int, evidence_gaps: int) -> str:
    if open_high_plus == 0 and evidence_gaps == 0:
        return "Ready"
    if open_high_plus <= 2 or evidence_gaps <= 3:
        return "Conditionally ready"
    return "Not ready"


async def compute_assessment_dashboard(
    session: AsyncSession,
    project: Project,
    snapshot_at: datetime | None = None,
    current_gate: str | None = None,
) -> AssessmentDashboardOut:
    """Build the first Assessment Dashboard snapshot shell.

    Slice 1 intentionally derives safe executive signals from existing project
    dashboard metrics. Later slices replace these placeholders with Activity x
    Gate lifecycle maturity calculations.
    """
    dash = await compute_dashboard(session, project.id)
    snapshot_time = snapshot_at or datetime.now(timezone.utc)
    gate = current_gate or _infer_current_gate(_enum_value(project.phase))

    quality_gate_maturity = await _compute_quality_gate_maturity(
        session=session,
        project_id=project.id,
        current_gate=gate,
    )
    process_risk = _compute_process_maturity_risk(quality_gate_maturity)
    risk_confidence = dash.risk_confidence or _compute_initial_risk_confidence(dash)
    product_risk = _compute_initial_product_risk(dash)
    gate_signal = _compute_initial_gate_signal(dash, risk_confidence.level)
    attention = _compute_initial_attention(
        product_risk=product_risk,
        process_risk=process_risk,
        gate_signal=gate_signal,
        risk_confidence=risk_confidence.level,
        critical_risk_count=dash.critical_risk_count,
    )

    official_score = _initial_official_score(dash)
    risk_posture = await _compute_project_risk_posture(
        session=session,
        project_id=project.id,
        current_gate=gate,
        dashboard=dash,
    )
    lifecycle_maturity = await _compute_lifecycle_process_maturity(
        session=session,
        project_id=project.id,
        current_gate=gate,
        quality_gate_maturity=quality_gate_maturity,
    )
    quality_subcharacteristic_maturity = await _compute_quality_subcharacteristic_maturity(
        session=session,
        project_id=project.id,
        current_gate=gate,
        quality_gate_maturity=quality_gate_maturity,
    )
    team_activity_work_product_matrix = _compute_team_activity_work_product_matrix(lifecycle_maturity)

    return AssessmentDashboardOut(
        project_id=project.id,
        snapshot_at=snapshot_time.isoformat(),
        current_gate=gate,
        audit_snapshot=AuditSnapshotOut(
            recommended_attention_level=attention,
            product_risk=product_risk,
            process_maturity_risk=process_risk,
            gate_readiness=GateReadinessOut(
                official_maturity=official_score,
                p0_status="Unknown",
                blocking_gap_count=dash.critical_risk_count + dash.evidence_gap_count,
                gate_progression_signal=gate_signal,
            ),
            risk_confidence=risk_confidence,
            official_integrated_score=official_score,
            open_risk_count=dash.open_risk_count,
            evidence_gap_count=dash.evidence_gap_count,
        ),
        quality_gate_maturity=quality_gate_maturity,
        project_risk_posture=risk_posture,
        quality_subcharacteristic_maturity=quality_subcharacteristic_maturity,
        lifecycle_process_maturity=lifecycle_maturity,
        team_activity_work_product_matrix=team_activity_work_product_matrix,
    )


compute_audit_report_dashboard = compute_assessment_dashboard


async def _compute_quality_gate_maturity(
    session: AsyncSession,
    project_id: str,
    current_gate: str,
) -> list[dict]:
    scope_result = await session.execute(
        select(ProjectScopeDecision)
        .where(ProjectScopeDecision.project_id == project_id)
    )
    scope = scope_result.scalars().all()
    included = [d for d in scope if d.applicability in INCLUDED_APPLICABILITY]

    req_result = await session.execute(
        select(QualityRequirement, ProjectScopeDecision)
        .join(QualityGoal, QualityRequirement.goal_id == QualityGoal.id)
        .join(ProjectScopeDecision, QualityGoal.scope_decision_id == ProjectScopeDecision.id)
        .where(ProjectScopeDecision.project_id == project_id)
    )
    req_scope_pairs = req_result.all()

    risk_result = await session.execute(
        select(RiskItem)
        .where(RiskItem.project_id == project_id, RiskItem.status == RiskItemStatus.Open)
    )
    open_risks = risk_result.scalars().all()

    rows = []
    for aspect in ASPECTS:
        aspect_scope = [
            d for d in included
            if aspect in (d.selected_quality_aspects or [])
        ]
        if not aspect_scope:
            rows.append({
                "aspect": aspect,
                "gate": current_gate,
                "scope_count": 0,
                "official_maturity": None,
                "reviewed_count": 0,
                "official_coverage": 0,
                "evidence_coverage": 0,
                "open_risk_count": 0,
                "high_or_critical_risk_count": 0,
                "blocking_gap_count": 0,
                "gate_progression_signal": "Unknown",
                "process_maturity_risk": "Unknown",
                "primary_reason": "No scoped quality characteristic for this aspect",
            })
            continue

        aspect_scope_ids = {d.id for d in aspect_scope}
        aspect_reqs = [
            req for req, decision in req_scope_pairs
            if decision.id in aspect_scope_ids
            and (not req.applicable_aspects or aspect in req.applicable_aspects)
        ]
        reviewed_count = _reviewed_count(aspect_scope)
        official_coverage = _percentage(reviewed_count, len(aspect_scope))
        evidence_coverage = _requirement_evidence_coverage(aspect_reqs)
        aspect_risks = [
            risk for risk in open_risks
            if aspect in (risk.quality_aspects or [])
        ]
        high_or_critical_risks = [
            risk for risk in aspect_risks
            if _enum_value(risk.risk_level) in {"Critical", "High"}
        ]
        blocking_gap_count = len(high_or_critical_risks)
        maturity = round((official_coverage * 0.6) + (evidence_coverage * 0.4))
        signal = _aspect_gate_signal(maturity, blocking_gap_count, official_coverage)
        risk_level = _aspect_process_risk(signal, maturity, blocking_gap_count)

        rows.append({
            "aspect": aspect,
            "gate": current_gate,
            "scope_count": len(aspect_scope),
            "official_maturity": maturity,
            "reviewed_count": reviewed_count,
            "official_coverage": official_coverage,
            "evidence_coverage": evidence_coverage,
            "open_risk_count": len(aspect_risks),
            "high_or_critical_risk_count": len(high_or_critical_risks),
            "blocking_gap_count": blocking_gap_count,
            "gate_progression_signal": signal,
            "process_maturity_risk": risk_level,
            "primary_reason": _quality_gate_reason(
                maturity=maturity,
                blocking_gap_count=blocking_gap_count,
                official_coverage=official_coverage,
                evidence_coverage=evidence_coverage,
            ),
        })

    return rows


async def _compute_project_risk_posture(
    session: AsyncSession,
    project_id: str,
    current_gate: str,
    dashboard: DashboardOut,
) -> dict:
    risk_result = await session.execute(
        select(RiskItem)
        .where(RiskItem.project_id == project_id, RiskItem.status == RiskItemStatus.Open)
        .order_by(
            RiskItem.risk_level,
            RiskItem.due_date.is_(None),
            RiskItem.due_date,
            RiskItem.risk_id,
        )
    )
    open_risks = risk_result.scalars().all()

    evidence_result = await session.execute(
        select(EvidenceItem)
        .where(EvidenceItem.project_id == project_id)
    )
    evidence_items = evidence_result.scalars().all()

    severity_distribution = {level.value: 0 for level in RiskLevel}
    aspect_distribution = {aspect: 0 for aspect in ASPECTS}
    for risk in open_risks:
        level = _enum_value(risk.risk_level)
        severity_distribution[level] = severity_distribution.get(level, 0) + 1
        for aspect in risk.quality_aspects or ["Unassigned"]:
            aspect_distribution[aspect] = aspect_distribution.get(aspect, 0) + 1

    evidence_status = {status.value: 0 for status in EvidenceStatus}
    for evidence in evidence_items:
        status = _enum_value(evidence.status)
        evidence_status[status] = evidence_status.get(status, 0) + 1

    gate_risks = [
        risk for risk in open_risks
        if _risk_impacts_current_gate(risk, current_gate)
    ]
    critical_or_high = [
        risk for risk in open_risks
        if _enum_value(risk.risk_level) in {"Critical", "High"}
    ]

    return {
        "open_risk_count": len(open_risks),
        "severity_distribution": severity_distribution,
        "aspect_distribution": aspect_distribution,
        "evidence_gap_summary": {
            "missing_evidence_count": dashboard.missing_evidence_count + evidence_status.get("Missing", 0),
            "failed_evidence_count": dashboard.failed_evidence_count + evidence_status.get("Failed", 0),
            "evidence_gap_count": dashboard.evidence_gap_count,
            "evidence_item_status": evidence_status,
        },
        "current_gate_impact": {
            "gate": current_gate,
            "risk_count": len(gate_risks),
            "blocking_gap_count": dashboard.critical_risk_count + dashboard.evidence_gap_count,
            "risks": [_risk_summary(risk) for risk in gate_risks[:6]],
        },
        "top_open_risks": [_risk_summary(risk) for risk in critical_or_high[:8]],
    }


async def _compute_quality_subcharacteristic_maturity(
    session: AsyncSession,
    project_id: str,
    current_gate: str,
    quality_gate_maturity: list[dict],
) -> list[dict]:
    scope_result = await session.execute(
        select(ProjectScopeDecision, CommonSubcharacteristic, CommonCharacteristic)
        .join(CommonSubcharacteristic, ProjectScopeDecision.subchar_id == CommonSubcharacteristic.id)
        .join(CommonCharacteristic, CommonSubcharacteristic.characteristic_id == CommonCharacteristic.id)
        .where(ProjectScopeDecision.project_id == project_id)
        .order_by(CommonCharacteristic.display_order, CommonSubcharacteristic.display_order)
    )
    scope_rows = scope_result.all()
    included_rows = [
        (decision, subchar, characteristic)
        for decision, subchar, characteristic in scope_rows
        if decision.applicability in INCLUDED_APPLICABILITY
    ]

    req_result = await session.execute(
        select(QualityRequirement, ProjectScopeDecision)
        .join(QualityGoal, QualityRequirement.goal_id == QualityGoal.id)
        .join(ProjectScopeDecision, QualityGoal.scope_decision_id == ProjectScopeDecision.id)
        .where(ProjectScopeDecision.project_id == project_id)
    )
    req_scope_pairs = req_result.all()

    risk_result = await session.execute(
        select(RiskItem)
        .where(RiskItem.project_id == project_id, RiskItem.status == RiskItemStatus.Open)
    )
    open_risks = risk_result.scalars().all()
    qg_by_aspect = {row["aspect"]: row for row in quality_gate_maturity}
    mapping_reasons = _quality_aspect_mapping_reasons()

    rows: list[dict] = []
    for decision, subchar, characteristic in included_rows:
        mapped_aspects = [
            aspect for aspect in (decision.selected_quality_aspects or [])
            if aspect in qg_by_aspect
        ]
        aspect_breakdown = []
        aspect_mapping_reasons = {
            aspect: mapping_reasons.get((subchar.id, aspect), _scope_only_mapping_reason(aspect))
            for aspect in mapped_aspects
        }

        for aspect in mapped_aspects:
            aspect_reqs = [
                req for req, req_decision in req_scope_pairs
                if req_decision.id == decision.id
                and (not req.applicable_aspects or aspect in req.applicable_aspects)
            ]
            aspect_risks = [
                risk for risk in open_risks
                if aspect in (risk.quality_aspects or [])
            ]
            blocking_risks = [
                risk for risk in aspect_risks
                if _enum_value(risk.risk_level) in {"Critical", "High"}
            ]
            gate_row = qg_by_aspect.get(aspect, {})
            activity_maturity = gate_row.get("official_maturity")
            evidence_coverage = _requirement_evidence_coverage(aspect_reqs)
            score = _attribute_aspect_score(
                activity_maturity=activity_maturity,
                evidence_coverage=evidence_coverage,
                blocking_gap_count=len(blocking_risks),
            )
            aspect_breakdown.append({
                "aspect": aspect,
                "score": score,
                "activity_maturity": activity_maturity,
                "evidence_coverage": evidence_coverage,
                "open_risk_count": len(aspect_risks),
                "blocking_gap_count": len(blocking_risks),
                "mapping_reason": aspect_mapping_reasons.get(aspect),
                "reason": _attribute_aspect_reason(
                    score=score,
                    evidence_coverage=evidence_coverage,
                    blocking_gap_count=len(blocking_risks),
                    activity_maturity=activity_maturity,
                ),
            })

        if aspect_breakdown:
            score = round(sum(item["score"] for item in aspect_breakdown) / len(aspect_breakdown))
            weakest = min(aspect_breakdown, key=lambda item: item["score"])
            evidence_coverage = round(
                sum(item["evidence_coverage"] for item in aspect_breakdown) / len(aspect_breakdown)
            )
            blocking_gap_count = sum(item["blocking_gap_count"] for item in aspect_breakdown)
            main_weakness = f'{weakest["aspect"]}: {weakest["reason"]}'
        else:
            score = 0
            weakest = None
            evidence_coverage = 0
            blocking_gap_count = 0
            main_weakness = "No mapped quality aspect in current scope"

        rows.append({
            "quality_characteristic": characteristic.name,
            "quality_subcharacteristic": subchar.name,
            "gate": current_gate,
            "overall_maturity": score,
            "maturity_band": _score_band(score),
            "mapped_aspects": mapped_aspects,
            "aspect_mapping_reasons": aspect_mapping_reasons,
            "weakest_aspect": weakest["aspect"] if weakest else "Unknown",
            "evidence_coverage": evidence_coverage,
            "blocking_gap_count": blocking_gap_count,
            "main_weakness": main_weakness,
            "aspect_breakdown": aspect_breakdown,
        })

    return sorted(rows, key=lambda row: (
        row["quality_characteristic"],
        row["quality_subcharacteristic"],
    ))


@lru_cache(maxsize=1)
def _quality_aspect_mapping_reasons() -> dict[tuple[str, str], str]:
    data_path = _data_dir() / "07_ADAS_Quality_Aspect_Mapping.json"
    if not data_path.exists():
        return {}

    with data_path.open(encoding="utf-8") as f:
        data = json.load(f)

    reasons: dict[tuple[str, str], str] = {}
    for mapping in data.get("mappings", []):
        subchar_id = mapping.get("qualitySubcharacteristicId")
        reason = mapping.get("mappingReason") or "Mapped by ADAS quality aspect model."
        for aspect in mapping.get("qualityAspects", []):
            normalized = _normalise_aspect_name(aspect)
            if subchar_id and normalized:
                reasons[(subchar_id, normalized)] = reason
    return reasons


def _scope_only_mapping_reason(aspect: str) -> str:
    return (
        f"Project-specific {aspect} mapping selected in the quality scope; "
        "the common ADAS quality aspect mapping model does not yet define the technical rationale."
    )


def _data_dir() -> Path:
    docker_data = Path("/data")
    if docker_data.exists():
        return docker_data
    return Path(__file__).resolve().parents[3] / "data"


def _normalise_aspect_name(aspect: str) -> str:
    return "AI Safety" if aspect == "AISafety" else aspect


async def _compute_lifecycle_process_maturity(
    session: AsyncSession,
    project_id: str,
    current_gate: str,
    quality_gate_maturity: list[dict],
) -> list[dict]:
    risk_result = await session.execute(
        select(RiskItem)
        .where(RiskItem.project_id == project_id, RiskItem.status == RiskItemStatus.Open)
    )
    open_risks = risk_result.scalars().all()
    qg_by_aspect = {row["aspect"]: row for row in quality_gate_maturity}

    frameworks = []
    for definition in _lifecycle_activity_library():
        aspect = definition["aspect"]
        qg = qg_by_aspect.get(aspect, {})
        framework_risks = [
            risk for risk in open_risks
            if aspect in (risk.quality_aspects or [])
        ]
        blocking_risk_count = sum(
            1 for risk in framework_risks
            if _enum_value(risk.risk_level) in {"Critical", "High"}
        )
        official_coverage = qg.get("official_coverage", 0) or 0
        evidence_coverage = qg.get("evidence_coverage", 0) or 0
        official_score = _lifecycle_official_score(
            official_coverage=official_coverage,
            evidence_coverage=evidence_coverage,
            blocking_risk_count=blocking_risk_count,
        )
        activities = [
            _activity_gate_summary(
                activity=activity,
                gate=current_gate,
                official_coverage=official_coverage,
                evidence_coverage=evidence_coverage,
                blocking_risk_count=blocking_risk_count,
            )
            for activity in definition["activities"]
        ]
        blockers = [activity for activity in activities if activity["judgement"] == "Fail"]

        frameworks.append({
            "framework": definition["framework"],
            "standard_context": definition["standard_context"],
            "aspect": aspect,
            "gate": current_gate,
            "official_score": official_score,
            "official_coverage": official_coverage,
            "evidence_coverage": evidence_coverage,
            "maturity_band": _score_band(official_score),
            "process_maturity_risk": _framework_process_risk(
                official_score=official_score,
                blocking_risk_count=blocking_risk_count,
                official_coverage=official_coverage,
            ),
            "main_blocker": _framework_main_blocker(
                official_coverage=official_coverage,
                evidence_coverage=evidence_coverage,
                blocking_risk_count=blocking_risk_count,
                blockers=blockers,
            ),
            "open_risk_count": len(framework_risks),
            "blocking_risk_count": blocking_risk_count,
            "activities": activities,
        })

    return frameworks


def _compute_team_activity_work_product_matrix(lifecycle_maturity: list[dict]) -> list[dict]:
    rows = []
    for framework in lifecycle_maturity:
        for activity in framework.get("activities", []):
            cells = [
                _default_team_activity_cell(
                    team=team["name"],
                    aspect=framework["aspect"],
                    activity_name=activity["activity_name"],
                    maturity_state=activity["official_maturity"],
                    judgement=activity["judgement"],
                    required_work_product=activity["required_evidence"],
                    blocking_risk_count=framework["blocking_risk_count"],
                    main_weakness=activity["primary_reason"],
                )
                for team in _default_adas_team_columns()
            ]
            accountable_teams = [
                cell["team"]
                for cell in cells
                if cell["role"] == "A"
            ]
            rows.append({
                "framework": framework["framework"],
                "aspect": framework["aspect"],
                "lifecycle_phase": activity["lifecycle_phase"],
                "activity_name": activity["activity_name"],
                "check_detail": "Team responsibility and work product maturity for this lifecycle activity",
                "gate": activity["gate"],
                "expected_maturity": activity["expected_maturity"],
                "required_work_product": activity["required_evidence"],
                "responsible_role": ", ".join(accountable_teams),
                "mapped_team": ", ".join(accountable_teams),
                "team_assignment_status": "Mapped",
                "maturity_state": activity["official_maturity"],
                "judgement": activity["judgement"],
                "blocking_level": activity["blocking_level"],
                "blocking_risk_count": framework["blocking_risk_count"],
                "main_weakness": activity["primary_reason"],
                "source": "lifecycle_activity_team_model",
                "cells": cells,
            })
    return rows


def _default_adas_team_columns() -> list[dict]:
    return [
        {"name": "PdM/PgM/PjM AD/ADAS"},
        {"name": "360 deg Perception AD/ADAS Safety"},
        {"name": "Map (Vehicle) CA & AD/ADAS Non-Safety"},
        {"name": "LaneLevelLocalization AD/ADAS Non-Safety"},
        {"name": "MotionPlanner AD/ADAS Safety-Rule"},
        {"name": "MotionPlanner AD/ADAS Safety-ML (SWC: DDTP)"},
        {"name": "InterCommBev (Application Framework)"},
        {"name": "Controller AD/ADAS Safety"},
        {"name": "Product Integrity"},
        {"name": "Product Delivery (Optional)"},
    ]


def _configured_team_matrix_cell(
    team: str,
    mapped_team: str | None,
    result_status: str,
    required_work_product: str | None,
    findings: str | None,
    evidence_ref: str | None,
) -> dict:
    if team != mapped_team:
        return {
            "team": team,
            "role": "-",
            "maturity_state": None,
            "work_product_status": "Not applicable",
            "evidence_status": "Not applicable",
            "blocking_risk_count": 0,
            "main_weakness": "",
        }

    maturity_state = _maturity_from_result(result_status)
    return {
        "team": team,
        "role": "A",
        "maturity_state": maturity_state,
        "work_product_status": _work_product_status(maturity_state, result_status),
        "evidence_status": _evidence_status(maturity_state),
        "blocking_risk_count": 1 if result_status == "Fail" else 0,
        "main_weakness": findings or "",
        "required_work_product": required_work_product,
        "evidence_ref": evidence_ref,
    }


def _default_team_activity_cell(
    team: str,
    aspect: str,
    activity_name: str,
    maturity_state: int,
    judgement: str,
    required_work_product: str,
    blocking_risk_count: int,
    main_weakness: str,
) -> dict:
    role = _default_team_role_for_activity(team, aspect, activity_name)
    if role == "N/A":
        return {
            "team": team,
            "role": "N/A",
            "maturity_state": None,
            "work_product_status": "Not applicable",
            "evidence_status": "Not applicable",
            "blocking_risk_count": 0,
            "main_weakness": "",
            "required_work_product": required_work_product,
        }

    return {
        "team": team,
        "role": role,
        "maturity_state": maturity_state,
        "work_product_status": _work_product_status(maturity_state, judgement),
        "evidence_status": _evidence_status(maturity_state),
        "blocking_risk_count": blocking_risk_count if role == "A" and judgement == "Fail" else 0,
        "main_weakness": main_weakness if judgement == "Fail" and role in {"A", "R"} else "",
        "required_work_product": required_work_product,
    }


def _default_team_role_for_activity(team: str, aspect: str, activity_name: str) -> str:
    name = activity_name.lower()
    is_pdm = team == "PdM/PgM/PjM AD/ADAS"
    is_perception = team == "360 deg Perception AD/ADAS Safety"
    is_map = team == "Map (Vehicle) CA & AD/ADAS Non-Safety"
    is_localization = team == "LaneLevelLocalization AD/ADAS Non-Safety"
    is_planner_rule = team == "MotionPlanner AD/ADAS Safety-Rule"
    is_planner_ml = team == "MotionPlanner AD/ADAS Safety-ML (SWC: DDTP)"
    is_intercomm = team == "InterCommBev (Application Framework)"
    is_controller = team == "Controller AD/ADAS Safety"
    is_integrity = team == "Product Integrity"
    is_delivery = team == "Product Delivery (Optional)"
    domain_teams = {
        "360 deg Perception AD/ADAS Safety",
        "Map (Vehicle) CA & AD/ADAS Non-Safety",
        "LaneLevelLocalization AD/ADAS Non-Safety",
        "MotionPlanner AD/ADAS Safety-Rule",
        "MotionPlanner AD/ADAS Safety-ML (SWC: DDTP)",
        "InterCommBev (Application Framework)",
        "Controller AD/ADAS Safety",
    }

    if is_integrity:
        return "R"

    if aspect == "QM":
        if is_pdm and any(key in name for key in ["planning", "tailoring", "defect", "release"]):
            return "A"
        if is_delivery and any(key in name for key in ["defect", "release"]):
            return "C"
        if is_intercomm and "architecture" in name:
            return "A"
        if team in domain_teams and any(key in name for key in ["requirements", "architecture", "verification"]):
            return "A" if not is_intercomm or "architecture" not in name else "A"
        if is_pdm or team in domain_teams:
            return "C"
        return "N/A"

    if aspect == "FuSA":
        if is_planner_rule and any(key in name for key in ["item", "hara", "safety goal", "functional", "allocation", "analysis"]):
            return "A"
        if is_controller and any(key in name for key in ["technical", "verification"]):
            return "A"
        if is_perception or is_planner_ml or is_localization:
            return "C"
        if is_pdm:
            return "C"
        return "N/A"

    if aspect == "CS":
        if is_intercomm and any(key in name for key in ["vulnerability", "verification", "incident"]):
            return "A"
        if is_map and any(key in name for key in ["item", "tara", "goals", "concept", "requirements"]):
            return "A"
        if is_controller or is_planner_rule or is_planner_ml or is_perception or is_localization:
            return "C"
        if is_pdm or is_delivery:
            return "C" if "incident" in name else "N/A"
        return "N/A"

    if aspect == "SOTIF":
        if is_planner_rule and any(key in name for key in ["functionality", "hazard", "scenario", "mitigation", "exploration", "verification"]):
            return "A"
        if is_map and any(key in name for key in ["triggering", "scenario"]):
            return "A"
        if is_delivery and "field monitoring" in name:
            return "C"
        if is_perception or is_localization or is_controller or is_planner_ml:
            return "C"
        if is_pdm:
            return "C"
        return "N/A"

    if aspect == "AI Safety":
        if is_planner_ml and any(key in name for key in ["ai system", "ai risk", "training", "model", "robustness", "runtime", "human-machine", "change"]):
            return "A"
        if is_localization and any(key in name for key in ["data lifecycle", "data collection", "annotation", "dataset"]):
            return "A"
        if is_delivery and any(key in name for key in ["change", "post-deployment"]):
            return "C"
        if is_perception or is_map or is_controller or is_planner_rule:
            return "C"
        if is_pdm:
            return "C"
        return "N/A"

    return "N/A"


def _maturity_from_result(result_status: str) -> int:
    if result_status == "Pass":
        return 4
    if result_status == "Conditional":
        return 3
    if result_status == "Fail":
        return 2
    if result_status == "Open":
        return 1
    return 0


def _work_product_status(maturity_state: int, judgement: str) -> str:
    if maturity_state >= 4 and judgement == "Pass":
        return "Accepted"
    if maturity_state >= 3:
        return "Evidence available"
    if maturity_state >= 2:
        return "In progress"
    if maturity_state >= 1:
        return "Planned"
    return "Not assessed"


def _evidence_status(maturity_state: int) -> str:
    if maturity_state >= 3:
        return "Available"
    if maturity_state >= 2:
        return "Partial"
    return "Missing"


def _map_responsible_role_to_team(responsible_role: str | None) -> str | None:
    if not responsible_role:
        return None
    role = responsible_role.lower()
    for team in _default_adas_team_columns():
        name = team["name"]
        normalized = name.lower()
        if normalized in role or role in normalized:
            return name
    return None


def _gate_definition_activity_label(definition: AssessmentGateDefinition) -> str:
    subcharacteristic = definition.subcharacteristic or "Unspecified sub-characteristic"
    phase = definition.lifecycle_phase or "Unspecified phase"
    return f"{subcharacteristic} / {phase}"


def _framework_from_gate_definition(definition: AssessmentGateDefinition) -> str:
    aspect = _aspect_from_gate_definition(definition)
    return {
        "FuSA": "FuSA Lifecycle / ISO 26262",
        "CS": "CS Lifecycle / ISO/SAE 21434",
        "SOTIF": "SOTIF Lifecycle / ISO 21448",
        "AI Safety": "AI Safety Lifecycle / ISO/PAS 8800",
        "QM": "QM Lifecycle",
    }.get(aspect, "Assessment Gate Definition")


def _aspect_from_gate_definition(definition: AssessmentGateDefinition) -> str:
    text = " ".join([
        definition.lifecycle_phase or "",
        definition.characteristic or "",
        definition.subcharacteristic or "",
        definition.what_to_check or "",
        definition.pass_criteria or "",
        definition.required_evidence or "",
        definition.responsible_role or "",
    ]).lower()
    if any(key in text for key in ["sotif", "iso 21448", "triggering condition", "intended functionality"]):
        return "SOTIF"
    if any(key in text for key in ["iso/pas 8800", "iso 8800", "ai safety", "dataset", "model", "data lifecycle"]):
        return "AI Safety"
    if any(key in text for key in ["tara", "cyber", "iso/sae 21434", "iso 21434"]):
        return "CS"
    if any(key in text for key in ["fusa", "iso 26262", "hara", "asil", "safety goal", "functional safety"]):
        return "FuSA"
    return "QM"


def _infer_current_gate(phase: str) -> str:
    phase_to_gate = {
        "Concept": "QG1",
        "Development": "QG2",
        "Validation": "QG4",
        "Production": "QG5",
    }
    return phase_to_gate.get(phase, "Unknown")


def _enum_value(value) -> str:
    return getattr(value, "value", value)


def _risk_impacts_current_gate(risk: RiskItem, current_gate: str) -> bool:
    if _enum_value(risk.risk_level) in {"Critical", "High"}:
        return True
    milestone = (risk.target_milestone or "").upper()
    return bool(current_gate and current_gate != "Unknown" and current_gate.upper() in milestone)


def _risk_summary(risk: RiskItem) -> dict:
    return {
        "risk_id": risk.risk_id,
        "title": risk.title,
        "risk_level": _enum_value(risk.risk_level),
        "status": _enum_value(risk.status),
        "quality_aspects": risk.quality_aspects or [],
        "owner": risk.owner or "-",
        "target_milestone": risk.target_milestone or "-",
        "due_date": risk.due_date.isoformat() if risk.due_date else "-",
        "reason": risk.risk_reason or risk.impact or "",
    }


def _lifecycle_official_score(
    official_coverage: int,
    evidence_coverage: int,
    blocking_risk_count: int,
) -> int:
    if official_coverage == 0:
        return 0
    score = round((official_coverage * 0.7) + (evidence_coverage * 0.3))
    if blocking_risk_count > 0:
        score = min(score, 50)
    return score


def _attribute_aspect_score(
    activity_maturity: int | None,
    evidence_coverage: int,
    blocking_gap_count: int,
) -> int:
    if activity_maturity is None:
        return 0
    score = round((activity_maturity * 0.7) + (evidence_coverage * 0.3))
    if blocking_gap_count > 0:
        score = min(score, 50)
    return score


def _attribute_aspect_reason(
    score: int,
    evidence_coverage: int,
    blocking_gap_count: int,
    activity_maturity: int | None,
) -> str:
    if activity_maturity is None:
        return "No Activity x Gate maturity mapped to this quality sub-characteristic"
    if blocking_gap_count > 0:
        return "Open High/Critical risk blocks sub-characteristic maturity"
    if evidence_coverage < 70:
        return "Evidence coverage below sub-characteristic threshold"
    if score < 70:
        return "Activity maturity below sub-characteristic ready threshold"
    return "Quality sub-characteristic is in ready range"


def _activity_gate_summary(
    activity: dict,
    gate: str,
    official_coverage: int,
    evidence_coverage: int,
    blocking_risk_count: int,
) -> dict:
    if official_coverage == 0:
        official_maturity = 0
        judgement = "Not Assessed"
        reason = "No formal Activity x Gate result"
    elif blocking_risk_count > 0 and activity["blocking_level"] == "P0":
        official_maturity = min(2, _state_from_score(evidence_coverage))
        judgement = "Fail"
        reason = "P0 activity is blocked by open High/Critical risk"
    else:
        official_maturity = _state_from_score(min(official_coverage, evidence_coverage))
        judgement = "Pass" if official_maturity >= 3 else "Fail"
        reason = "Formal Activity x Gate result available"

    return {
        "lifecycle_phase": activity["phase"],
        "activity_name": activity["name"],
        "gate": gate,
        "expected_maturity": activity["expected_maturity"],
        "blocking_level": activity["blocking_level"],
        "required_evidence": activity["evidence"],
        "official_maturity": official_maturity,
        "judgement": judgement,
        "primary_reason": reason,
    }


def _state_from_score(score: int) -> int:
    if score >= 90:
        return 4
    if score >= 70:
        return 3
    if score >= 50:
        return 2
    if score > 0:
        return 1
    return 0


def _score_band(score: int) -> str:
    if score >= 90:
        return "Deliverable accepted"
    if score >= 70:
        return "Evidence complete"
    if score >= 50:
        return "In progress"
    if score >= 25:
        return "Insufficient"
    return "Not assessed / no basis"


def _framework_process_risk(
    official_score: int,
    blocking_risk_count: int,
    official_coverage: int,
) -> str:
    if blocking_risk_count > 0:
        return "High"
    if official_coverage == 0:
        return "Unknown"
    if official_score < 50:
        return "High"
    if official_score < 70:
        return "Medium"
    return "Low"


def _framework_main_blocker(
    official_coverage: int,
    evidence_coverage: int,
    blocking_risk_count: int,
    blockers: list[dict],
) -> str:
    if blocking_risk_count > 0 and blockers:
        return blockers[0]["activity_name"]
    if blocking_risk_count > 0:
        return "Open High/Critical risk"
    if official_coverage == 0:
        return "No formal Activity x Gate result"
    if evidence_coverage < 70:
        return "Evidence coverage below lifecycle threshold"
    return "No major lifecycle blocker"


def _lifecycle_activity_library() -> list[dict]:
    return [
        {
            "framework": "QM Lifecycle",
            "standard_context": "QM",
            "aspect": "QM",
            "activities": [
                _activity("Planning", "Project quality planning", "Quality plan, scope definition, role and responsibility matrix", "P0"),
                _activity("Planning", "Quality sub-characteristic tailoring", "Quality sub-characteristic tailoring record and assessment scope decision", "P0"),
                _activity("Development", "Requirements completeness review", "Requirements coverage report and review record", "P0"),
                _activity("Development", "Architecture consistency review", "Architecture review record and interface consistency evidence", "P0"),
                _activity("Validation", "Verification strategy and coverage planning", "Verification strategy, validation plan, and coverage matrix", "P0"),
                _activity("Operation", "Defect and issue management", "Defect register, issue triage record, and closure evidence", "P1"),
                _activity("Release", "Release quality readiness", "Release readiness report and open risk review", "P0"),
            ],
        },
        {
            "framework": "FuSA Lifecycle / ISO 26262",
            "standard_context": "ISO 26262",
            "aspect": "FuSA",
            "activities": [
                _activity("Concept", "Item definition", "Item definition document", "P0"),
                _activity("Concept", "HARA", "HARA report, safety goal list, ASIL rationale", "P0"),
                _activity("Concept", "Safety goal definition", "Safety goal list and ASIL rationale", "P0"),
                _activity("Development", "Functional safety concept", "FSC document", "P0"),
                _activity("Development", "Technical safety concept", "TSC document", "P0"),
                _activity("Development", "Safety requirements allocation", "Allocated safety requirements and traceability matrix", "P0"),
                _activity("Development", "Safety analysis", "Safety analysis report and residual risk rationale", "P0"),
                _activity("Validation", "Safety verification and validation", "Safety verification and validation report", "P0"),
                _activity("Release", "Safety case / safety argument", "Safety case and evidence package", "P0"),
            ],
        },
        {
            "framework": "CS Lifecycle / ISO/SAE 21434",
            "standard_context": "ISO/SAE 21434",
            "aspect": "CS",
            "activities": [
                _activity("Concept", "Cybersecurity item definition", "CS item definition", "P0"),
                _activity("Concept", "TARA", "TARA report, treatment rationale", "P0"),
                _activity("Concept", "Cybersecurity goals", "Cybersecurity goal list and risk treatment rationale", "P0"),
                _activity("Development", "Cybersecurity concept", "Cybersecurity concept and control allocation", "P0"),
                _activity("Development", "Cybersecurity requirements", "CS requirement baseline", "P0"),
                _activity("Development", "Vulnerability analysis", "Vulnerability analysis report and mitigation tracking", "P0"),
                _activity("Validation", "Cybersecurity verification and validation", "Pen test and vulnerability test report", "P0"),
                _activity("Operation", "Incident and vulnerability response planning", "Incident response plan and vulnerability management records", "P1"),
            ],
        },
        {
            "framework": "SOTIF Lifecycle / ISO 21448",
            "standard_context": "ISO 21448",
            "aspect": "SOTIF",
            "activities": [
                _activity("Concept", "Intended functionality definition", "Intended function and ODD description", "P0"),
                _activity("Concept", "Hazard identification for intended functionality", "SOTIF hazard analysis for intended functionality", "P0"),
                _activity("Concept", "Triggering condition identification", "Triggering condition catalogue and rationale", "P0"),
                _activity("Development", "Scenario analysis", "Scenario catalogue and coverage rationale", "P0"),
                _activity("Development", "Known unsafe scenario mitigation", "Mitigation strategy and verification evidence", "P0"),
                _activity("Development", "Unknown unsafe scenario exploration", "Unknown unsafe scenario exploration evidence", "P0"),
                _activity("Validation", "SOTIF verification and validation", "Validation report and residual risk evaluation", "P0"),
                _activity("Operation", "Field monitoring and feedback", "Monitoring plan and field feedback evidence", "P1"),
            ],
        },
        {
            "framework": "AI Safety Lifecycle / ISO/PAS 8800",
            "standard_context": "ISO/PAS 8800",
            "aspect": "AI Safety",
            "activities": [
                _activity("Planning", "AI system definition", "AI system definition and intended use description", "P0"),
                _activity("Planning", "AI risk analysis", "AI risk analysis and risk treatment rationale", "P0"),
                _activity("Data", "Data lifecycle planning", "Data lifecycle plan and governance model", "P0"),
                _activity("Data", "Data collection and sourcing", "Data source inventory, lineage, and collection evidence", "P0"),
                _activity("Data", "Data annotation and labelling", "Annotation guideline, labelling quality report, and review record", "P0"),
                _activity("Data", "Dataset quality and representativeness assessment", "Dataset quality, bias, representativeness, and coverage assessment", "P0"),
                _activity("Development", "Training and model development", "Training record, model development evidence, and configuration baseline", "P0"),
                _activity("Evaluation", "Model verification and validation", "Model verification, validation, and scenario evaluation report", "P0"),
                _activity("Evaluation", "Robustness and edge case evaluation", "Robustness, edge case, and stress evaluation report", "P0"),
                _activity("Operation", "Runtime monitoring", "Runtime monitoring plan and operational safety evidence", "P1"),
                _activity("HMI", "Human-machine interaction safety", "HMI safety analysis and user interaction risk evidence", "P0"),
                _activity("Operation", "Change management and post-deployment monitoring", "Change impact analysis and post-deployment monitoring evidence", "P1"),
            ],
        },
    ]


def _activity(phase: str, name: str, evidence: str, blocking_level: str) -> dict:
    return {
        "phase": phase,
        "name": name,
        "evidence": evidence,
        "blocking_level": blocking_level,
        "expected_maturity": "3 Evidence complete",
    }


def _requirement_evidence_coverage(requirements: list[QualityRequirement]) -> int:
    if not requirements:
        return 0
    usable = sum(
        1 for requirement in requirements
        if requirement.evidence_status in {EvidenceStatus.Complete, EvidenceStatus.Partial}
    )
    return _percentage(usable, len(requirements))


def _aspect_gate_signal(maturity: int, blocking_gap_count: int, official_coverage: int) -> str:
    if blocking_gap_count > 0 or maturity < 50:
        return "Blocked"
    if official_coverage == 0:
        return "Unknown"
    if maturity >= 80:
        return "Ready"
    return "Conditional"


def _aspect_process_risk(signal: str, maturity: int, blocking_gap_count: int) -> str:
    if signal == "Unknown":
        return "Unknown"
    if blocking_gap_count > 0 or maturity < 50:
        return "High"
    if maturity < 70:
        return "Medium"
    return "Low"


def _quality_gate_reason(
    maturity: int,
    blocking_gap_count: int,
    official_coverage: int,
    evidence_coverage: int,
) -> str:
    if blocking_gap_count > 0:
        return "Open High/Critical risk blocks this gate"
    if official_coverage == 0:
        return "No formal scope assessment result for this aspect"
    if evidence_coverage < 70:
        return "Evidence coverage below gate threshold"
    if official_coverage < 80:
        return "Formal scope assessment coverage below threshold"
    if maturity < 80:
        return "Gate maturity is conditional"
    return "Gate maturity is ready"


def _compute_process_maturity_risk(quality_gate_maturity: list[dict]) -> str:
    scoped = [row for row in quality_gate_maturity if row.get("scope_count", 0) > 0]
    if not scoped:
        return "Unknown"
    if any(row.get("gate_progression_signal") == "Blocked" for row in scoped):
        return "High"
    if any(row.get("gate_progression_signal") == "Unknown" for row in scoped):
        return "High"
    if any(row.get("process_maturity_risk") == "Medium" for row in scoped):
        return "Medium"
    return "Low"


def _compute_initial_product_risk(dash: DashboardOut) -> str:
    if dash.critical_risk_count > 0:
        return "Critical"
    if dash.high_risk_count > 0 or dash.failed_evidence_count > 0:
        return "High"
    if dash.open_risk_count > 0 or dash.evidence_gap_count > 0:
        return "Medium"
    return "Low"


def _compute_initial_gate_signal(dash: DashboardOut, confidence: str) -> str:
    if confidence == "Unknown":
        return "Unknown"
    if dash.critical_risk_count > 0 or dash.failed_evidence_count > 0:
        return "Blocked"
    if dash.assessment_readiness == "Ready" and confidence in {"High", "Medium"}:
        return "Ready"
    return "Conditional"


def _compute_initial_risk_confidence(
    dash: DashboardOut,
    evidence_total: int | None = None,
    usable_evidence_count: int | None = None,
    trace_total: int | None = None,
    trace_linked_count: int | None = None,
    official_reviewed_count: int | None = None,
    official_total: int | None = None,
    fresh_review_count: int | None = None,
    review_total: int | None = None,
) -> RiskConfidenceOut:
    assessed_count = (
        dash.selected_subchar_count
        + dash.open_risk_count
        + dash.open_finding_count
        + dash.open_action_count
    )
    if assessed_count == 0:
        return RiskConfidenceOut(
            level="Unknown",
            primary_reason="No assessment basis available",
            evidence_coverage=0,
            trace_coverage=0,
            official_assessment_coverage=0,
            review_freshness=0,
            critical_unknown_count=1,
        )

    if evidence_total:
        evidence_coverage = _percentage(usable_evidence_count or 0, evidence_total)
    else:
        evidence_coverage = _percentage(
            max(dash.selected_subchar_count - dash.evidence_gap_count, 0),
            max(dash.selected_subchar_count, 1),
        )

    if trace_total:
        trace_coverage = _percentage(trace_linked_count or 0, trace_total)
    else:
        trace_coverage = 0 if dash.selected_subchar_count else 0

    if official_total:
        official_coverage = _percentage(official_reviewed_count or 0, official_total)
    else:
        official_coverage = 0 if dash.selected_subchar_count else 0

    if review_total:
        review_freshness = _percentage(fresh_review_count or 0, review_total)
    else:
        review_freshness = 0 if dash.selected_subchar_count else 0
    critical_unknown_count = dash.critical_risk_count

    if critical_unknown_count > 0:
        level = "Low"
        primary_reason = "Critical unknown or critical risk exists"
    elif evidence_coverage < 70:
        level = "Low"
        primary_reason = "Evidence coverage below threshold"
    elif trace_coverage < 70:
        level = "Low"
        primary_reason = "Trace coverage below threshold"
    elif official_coverage < 80:
        level = "Low"
        primary_reason = "Official assessment coverage below threshold"
    elif evidence_coverage >= 85 and trace_coverage >= 85 and official_coverage >= 90:
        level = "High"
        primary_reason = "Coverage thresholds are strongly met"
    else:
        level = "Medium"
        primary_reason = "Baseline coverage thresholds are met"

    return RiskConfidenceOut(
        level=level,
        primary_reason=primary_reason,
        evidence_coverage=evidence_coverage,
        trace_coverage=trace_coverage,
        official_assessment_coverage=official_coverage,
        review_freshness=review_freshness,
        critical_unknown_count=critical_unknown_count,
    )


def _compute_initial_attention(
    product_risk: str,
    process_risk: str,
    gate_signal: str,
    risk_confidence: str,
    critical_risk_count: int,
) -> str:
    if critical_risk_count > 0 or gate_signal == "Blocked":
        return "Critical"
    if process_risk == "Unknown" or gate_signal == "Unknown":
        return "At Risk"
    if risk_confidence in {"Low", "Unknown"}:
        return "At Risk"
    if product_risk == "High":
        return "At Risk"
    if product_risk == "Medium" or gate_signal == "Conditional":
        return "Watch"
    return "Normal"


def _initial_official_score(dash: DashboardOut) -> int:
    if dash.assessment_readiness == "Ready":
        return 75
    if dash.assessment_readiness == "Conditionally ready":
        return 55
    return 25


def _percentage(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 0
    return round((numerator / denominator) * 100)


def _reviewed_count(scope: list[ProjectScopeDecision]) -> int:
    return sum(1 for d in scope if d.review_status in {ReviewStatus.Reviewed, ReviewStatus.Approved})


def _fresh_review_count(scope: list[ProjectScopeDecision]) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    count = 0
    for decision in scope:
        updated_at = decision.updated_at
        if updated_at is None:
            continue
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        if updated_at >= cutoff:
            count += 1
    return count
