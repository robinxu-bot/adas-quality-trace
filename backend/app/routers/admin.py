from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.seed_service import seed_demo_projects

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed-demo")
async def seed_demo(db: AsyncSession = Depends(get_db)):
    """Populate two sample ADAS projects. Idempotent — skips existing projects."""
    return await seed_demo_projects(db)
