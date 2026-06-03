"""Business logic for Gate Assessment."""
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment import (
    AssessmentGateDefinition, AssessmentRun, AssessmentCheckResult,
)
from app.models.project import Project

GATE_ORDER = ["QG0", "QG1", "QG2", "QG3", "QG4", "QG5"]

GATE_NAMES = {
    "QG0": "Project Scope and Plan",
    "QG1": "Requirement Feasibility",
    "QG2": "Implementation Completed",
    "QG3": "Software Integrated",
    "QG4": "Ready for Release",
    "QG5": "Project Close",
}


def compute_overall_result(p0_fail: int, p1_fail: int, p2_fail: int) -> str:
    if p0_fail > 0:
        return "Fail"
    if p1_fail > 0:
        return "Conditional"
    return "Pass"


def compute_readiness(overall_result: str | None) -> str:
    if overall_result is None:
        return "Not ready"
    if overall_result == "Fail":
        return "Not ready"
    if overall_result == "Conditional":
        return "Conditionally ready"
    return "Ready"


async def get_next_run_number(session: AsyncSession, project_id: str, gate_id: str) -> int:
    result = await session.execute(
        select(func.max(AssessmentRun.run_number))
        .where(
            AssessmentRun.project_id == project_id,
            AssessmentRun.gate_id == gate_id,
        )
    )
    max_num = result.scalar_one_or_none()
    return (max_num or 0) + 1


async def recompute_run_counts(session: AsyncSession, run: AssessmentRun) -> None:
    """Recompute p0/p1/p2 fail counts and overall_result from check results."""
    results = await session.execute(
        select(AssessmentCheckResult)
        .options(selectinload(AssessmentCheckResult.definition))
        .where(AssessmentCheckResult.run_id == run.id)
    )
    check_results = results.scalars().all()

    p0 = p1 = p2 = 0
    for cr in check_results:
        if cr.result == "Fail":
            bl = cr.definition.blocking_level if cr.definition else "P2"
            if bl == "P0":
                p0 += 1
            elif bl == "P1":
                p1 += 1
            else:
                p2 += 1

    run.p0_fail_count = p0
    run.p1_fail_count = p1
    run.p2_fail_count = p2
    run.overall_result = compute_overall_result(p0, p1, p2)


async def update_project_readiness(session: AsyncSession, project_id: str) -> str:
    """Find latest completed run for project's current gate and update readiness."""
    project = await session.get(Project, project_id)
    if not project:
        return "Not ready"

    current_gate = getattr(project, "current_gate", "QG0") or "QG0"

    result = await session.execute(
        select(AssessmentRun)
        .where(
            AssessmentRun.project_id == project_id,
            AssessmentRun.gate_id == current_gate,
            AssessmentRun.status == "Completed",
        )
        .order_by(AssessmentRun.run_number.desc())
        .limit(1)
    )
    latest_run = result.scalar_one_or_none()
    readiness = compute_readiness(latest_run.overall_result if latest_run else None)
    return readiness


async def get_assessment_dashboard(session: AsyncSession, project_id: str) -> dict:
    """Build gate assessment dashboard data for all QG0-QG5."""
    project = await session.get(Project, project_id)
    current_gate = getattr(project, "current_gate", "QG0") or "QG0"

    gates_out = []
    for gate_id in GATE_ORDER:
        result = await session.execute(
            select(AssessmentRun)
            .where(
                AssessmentRun.project_id == project_id,
                AssessmentRun.gate_id == gate_id,
                AssessmentRun.status == "Completed",
            )
            .order_by(AssessmentRun.run_number.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        gates_out.append({
            "gate_id": gate_id,
            "gate_name": GATE_NAMES.get(gate_id, gate_id),
            "latest_run_number": latest.run_number if latest else None,
            "overall_result": latest.overall_result if latest else None,
            "p0_fail_count": latest.p0_fail_count if latest else None,
            "p1_fail_count": latest.p1_fail_count if latest else None,
            "p2_fail_count": latest.p2_fail_count if latest else None,
            "executed_at": latest.executed_at.isoformat() if latest and latest.executed_at else None,
        })

    readiness = await update_project_readiness(session, project_id)

    return {
        "current_gate": current_gate,
        "assessment_readiness": readiness,
        "gates": gates_out,
    }
