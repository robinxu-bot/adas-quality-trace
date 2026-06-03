from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.models.project import Project
from app.schemas.dashboard import DashboardOut, AuditReportDashboardOut
from app.services.dashboard_service import compute_dashboard, compute_audit_report_dashboard

router = APIRouter(prefix="/projects", tags=["dashboard"])


@router.get("/{project_id}/dashboard", response_model=DashboardOut)
async def get_dashboard(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    return await compute_dashboard(db, project_id)


@router.get("/{project_id}/audit-report/dashboard", response_model=AuditReportDashboardOut)
async def get_audit_report_dashboard(
    project_id: str,
    snapshot_at: datetime | None = None,
    current_gate: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await compute_audit_report_dashboard(
        db,
        project,
        snapshot_at=snapshot_at,
        current_gate=current_gate,
    )
