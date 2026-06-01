"""Dashboard metric computation for a project."""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import (
    ProjectScopeDecision, RiskItem, EvidenceItem,
    AssessmentFinding, ActionItem, TestResult, TestCase,
    SoftwareModule, ArchitectureElement,
)
from app.models.enums import (
    ApplicabilityValue, RiskItemStatus, RiskLevel,
    FindingStatus, ActionStatus, TestResultValue,
)
from app.schemas.dashboard import DashboardOut, AspectStats
from app.constants import ASPECTS, INCLUDED_APPLICABILITY, EXCLUDED_APPLICABILITY


async def compute_dashboard(session: AsyncSession, project_id: str) -> DashboardOut:
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

    return DashboardOut(
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


def _compute_readiness(open_high_plus: int, evidence_gaps: int) -> str:
    if open_high_plus == 0 and evidence_gaps == 0:
        return "Ready"
    if open_high_plus <= 2 or evidence_gaps <= 3:
        return "Conditionally ready"
    return "Not ready"
