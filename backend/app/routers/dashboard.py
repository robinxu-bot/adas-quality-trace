from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.schemas.dashboard import DashboardOut
from app.services.dashboard_service import compute_dashboard

router = APIRouter(prefix="/projects", tags=["dashboard"])


@router.get("/{project_id}/dashboard", response_model=DashboardOut)
async def get_dashboard(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    return await compute_dashboard(db, project_id)
