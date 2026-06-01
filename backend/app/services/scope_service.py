"""Business logic for Project Quality Scope generation and management."""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectScopeDecision
from app.models.common import (
    ProductLineRecommendation, ProductLineRecommendationAspect,
    CommonSubcharacteristic,
)
from app.models.enums import ProductLine, ApplicabilityValue
from app.schemas.project import ScopeDecisionIn


async def generate_default_scope(
    session: AsyncSession, project: Project
) -> list[ProjectScopeDecision]:
    """Generate default scope decisions from product line recommendations."""
    recs_result = await session.execute(
        select(ProductLineRecommendation)
        .where(ProductLineRecommendation.product_line == project.product_line)
    )
    recs = recs_result.scalars().all()

    decisions = []
    for rec in recs:
        aspect_result = await session.execute(
            select(ProductLineRecommendationAspect)
            .where(ProductLineRecommendationAspect.recommendation_id == rec.id)
        )
        aspects = [r.aspect for r in aspect_result.scalars().all()]

        decisions.append(ProjectScopeDecision(
            id=str(uuid.uuid4()),
            project_id=project.id,
            subchar_id=rec.subchar_id,
            applicability=rec.recommended_applicability,
            rationale=rec.default_rationale,
            recommended_applicability=rec.recommended_applicability,
            recommendation_reason=rec.default_rationale,
            selected_quality_aspects=aspects,
            manual_override=False,
        ))

    return decisions


async def apply_scope_payload(
    session: AsyncSession,
    project: Project,
    scope_in: list[ScopeDecisionIn],
) -> list[ProjectScopeDecision]:
    """Create scope decisions from wizard payload (Step 5 confirm)."""
    # Look up recommended values for each subchar so we can record them
    subchar_ids = [s.subchar_id for s in scope_in]
    recs_result = await session.execute(
        select(ProductLineRecommendation)
        .where(
            ProductLineRecommendation.product_line == project.product_line,
            ProductLineRecommendation.subchar_id.in_(subchar_ids),
        )
    )
    rec_map = {r.subchar_id: r for r in recs_result.scalars().all()}

    decisions = []
    for item in scope_in:
        rec = rec_map.get(item.subchar_id)
        decisions.append(ProjectScopeDecision(
            id=str(uuid.uuid4()),
            project_id=project.id,
            subchar_id=item.subchar_id,
            applicability=item.applicability,
            rationale=item.rationale,
            recommended_applicability=rec.recommended_applicability if rec else None,
            recommendation_reason=rec.default_rationale if rec else None,
            selected_quality_aspects=item.selected_quality_aspects,
            manual_override=item.manual_override,
            decision_owner=item.decision_owner,
            decision_date=item.decision_date,
            review_status=item.review_status,
        ))

    return decisions


def compute_risk_level(severity: str, likelihood: str) -> str:
    """Compute risk level from severity × likelihood matrix."""
    if severity == "Critical" or likelihood == "Critical":
        return "Critical"
    levels = {"High": 3, "Medium": 2, "Low": 1}
    score = levels.get(severity, 1) * levels.get(likelihood, 1)
    if score >= 9:
        return "High"
    if score <= 1:
        return "Low"
    return "Medium"


async def get_project_summary_stats(
    session: AsyncSession, project_id: str
) -> dict:
    """Compute summary stats for project card display."""
    from sqlalchemy import func
    from app.models.project import RiskItem
    from app.models.enums import RiskItemStatus
    from app.constants import INCLUDED_APPLICABILITY

    scope_result = await session.execute(
        select(ProjectScopeDecision)
        .where(ProjectScopeDecision.project_id == project_id)
    )
    scope = scope_result.scalars().all()

    selected_count = sum(1 for s in scope if s.applicability in INCLUDED_APPLICABILITY)

    risk_result = await session.execute(
        select(func.count())
        .select_from(RiskItem)
        .where(
            RiskItem.project_id == project_id,
            RiskItem.status == RiskItemStatus.Open,
        )
    )
    open_risk_count = risk_result.scalar_one()

    return {
        "selected_subchar_count": selected_count,
        "open_risk_count": open_risk_count,
        "evidence_gap_count": 0,  # populated in Slice 4+ when test data exists
        "assessment_readiness": _compute_readiness(open_risk_count, 0),
    }


def _compute_readiness(open_high_risks: int, evidence_gaps: int) -> str:
    if open_high_risks == 0 and evidence_gaps == 0:
        return "Ready"
    if open_high_risks <= 2 or evidence_gaps <= 3:
        return "Conditionally ready"
    return "Not ready"
