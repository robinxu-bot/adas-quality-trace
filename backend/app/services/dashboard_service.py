"""Dashboard metric computation for a project."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project import (
    ProjectScopeDecision, RiskItem, EvidenceItem,
    AssessmentFinding, ActionItem, TestResult, TestCase,
    SoftwareModule, ArchitectureElement, QualityGoal, QualityRequirement,
    SubQualityRequirement,
)
from app.models.enums import (
    ApplicabilityValue, RiskItemStatus, RiskLevel,
    FindingStatus, ActionStatus, TestResultValue, EvidenceStatus, ReviewStatus,
)
from app.schemas.dashboard import (
    DashboardOut,
    AspectStats,
    AuditReportDashboardOut,
    AuditSnapshotOut,
    GateReadinessOut,
    RiskConfidenceOut,
)
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


async def compute_audit_report_dashboard(
    session: AsyncSession,
    project: Project,
    snapshot_at: datetime | None = None,
    current_gate: str | None = None,
) -> AuditReportDashboardOut:
    """Build the first Audit Report Dashboard snapshot shell.

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
    draft_score = max(official_score, min(100, official_score + 10))
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

    return AuditReportDashboardOut(
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
            draft_integrated_score=draft_score,
            pending_human_confirmation_count=0,
            open_risk_count=dash.open_risk_count,
            evidence_gap_count=dash.evidence_gap_count,
        ),
        quality_gate_maturity=quality_gate_maturity,
        project_risk_posture=risk_posture,
        lifecycle_process_maturity=lifecycle_maturity,
    )


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
        draft_score = _lifecycle_draft_score(
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
        pending = sum(1 for activity in activities if activity["official_maturity"] == 0)

        frameworks.append({
            "framework": definition["framework"],
            "standard_context": definition["standard_context"],
            "aspect": aspect,
            "gate": current_gate,
            "official_score": official_score,
            "draft_score": draft_score,
            "official_coverage": official_coverage,
            "evidence_coverage": evidence_coverage,
            "maturity_band": _score_band(official_score),
            "draft_band": _score_band(draft_score),
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
            "pending_human_confirmation_count": pending,
            "activities": activities,
        })

    return frameworks


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


def _lifecycle_draft_score(evidence_coverage: int, blocking_risk_count: int) -> int:
    score = evidence_coverage
    if blocking_risk_count > 0:
        score = min(score, 50)
    return score


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
        reason = "No human-confirmed Activity x Gate result"
    elif blocking_risk_count > 0 and activity["blocking_level"] == "P0":
        official_maturity = min(2, _state_from_score(evidence_coverage))
        judgement = "Fail"
        reason = "P0 activity is blocked by open High/Critical risk"
    else:
        official_maturity = _state_from_score(min(official_coverage, evidence_coverage))
        judgement = "Pass" if official_maturity >= 3 else "Fail"
        reason = "Human-reviewed result available"

    draft_maturity = _state_from_score(_lifecycle_draft_score(evidence_coverage, blocking_risk_count))

    return {
        "lifecycle_phase": activity["phase"],
        "activity_name": activity["name"],
        "gate": gate,
        "expected_maturity": activity["expected_maturity"],
        "blocking_level": activity["blocking_level"],
        "required_evidence": activity["evidence"],
        "official_maturity": official_maturity,
        "draft_maturity": draft_maturity,
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
        return "No human-confirmed Activity x Gate result"
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
                _activity("Concept", "Project scope and quality plan", "Quality plan, scope definition", "P0"),
                _activity("Development", "Requirements baseline", "Requirement review record", "P0"),
                _activity("Development", "Architecture baseline", "Architecture review record", "P0"),
                _activity("Validation", "Integration and qualification test", "Test report, issue list", "P1"),
                _activity("Release", "Release readiness", "Release review record", "P0"),
            ],
        },
        {
            "framework": "FuSA Lifecycle / ISO 26262",
            "standard_context": "ISO 26262",
            "aspect": "FuSA",
            "activities": [
                _activity("Concept", "Safety management planning", "Safety plan, confirmation measure plan", "P0"),
                _activity("Concept", "Item definition", "Item definition document", "P0"),
                _activity("Concept", "HARA", "HARA report, safety goal list, ASIL rationale", "P0"),
                _activity("Development", "Functional safety concept", "FSC document", "P0"),
                _activity("Development", "Technical safety concept", "TSC document", "P0"),
                _activity("Validation", "Verification and validation", "Safety verification and validation report", "P0"),
                _activity("Release", "Safety case", "Safety argument and evidence package", "P0"),
            ],
        },
        {
            "framework": "CS Lifecycle / ISO/SAE 21434",
            "standard_context": "ISO/SAE 21434",
            "aspect": "CS",
            "activities": [
                _activity("Concept", "Cybersecurity management planning", "CS plan, role assignment", "P0"),
                _activity("Concept", "Cybersecurity item definition", "CS item definition", "P0"),
                _activity("Concept", "TARA", "TARA report, treatment rationale", "P0"),
                _activity("Development", "Cybersecurity requirements", "CS requirement baseline", "P0"),
                _activity("Validation", "Cybersecurity verification and validation", "Pen test and vulnerability test report", "P0"),
                _activity("Operation", "Operations and monitoring", "Monitoring and vulnerability management records", "P1"),
            ],
        },
        {
            "framework": "SOTIF Lifecycle / ISO 21448",
            "standard_context": "ISO 21448",
            "aspect": "SOTIF",
            "activities": [
                _activity("Concept", "Intended functionality definition", "Intended function and ODD description", "P0"),
                _activity("Concept", "SOTIF hazard identification", "Hazard and triggering condition analysis", "P0"),
                _activity("Development", "Scenario identification and coverage", "Scenario catalogue and coverage rationale", "P0"),
                _activity("Development", "Known unsafe scenario mitigation", "Mitigation strategy and verification evidence", "P0"),
                _activity("Validation", "Validation of SOTIF measures", "Validation report and residual risk evaluation", "P0"),
                _activity("Operation", "Field monitoring and update feedback", "Monitoring plan and field feedback evidence", "P1"),
            ],
        },
        {
            "framework": "AI Safety Lifecycle / ISO/PAS 8800",
            "standard_context": "ISO/PAS 8800",
            "aspect": "AI Safety",
            "activities": [
                _activity("Planning", "AI safety lifecycle planning", "AI safety plan and responsibility matrix", "P0"),
                _activity("Data", "Data lifecycle and data quality", "Dataset lineage, quality, coverage, and governance records", "P0"),
                _activity("Development", "Model development controls", "Model training and development evidence", "P0"),
                _activity("Evaluation", "Model evaluation and validation", "Model evaluation, robustness, and scenario validation report", "P0"),
                _activity("Assurance", "AI safety argument", "AI safety argument package", "P0"),
                _activity("Assurance", "Evaluation of safety argument", "Safety argument evaluation record", "P0"),
                _activity("Operation", "Operation and monitoring", "Runtime monitoring and assurance maintenance records", "P1"),
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
        return "No human-reviewed scope result for this aspect"
    if evidence_coverage < 70:
        return "Evidence coverage below gate threshold"
    if official_coverage < 80:
        return "Human-reviewed scope coverage below threshold"
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
