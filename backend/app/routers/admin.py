from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.seed_service import seed_demo_projects
from app.services.gate_seed_service import seed_gate_definitions

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed-demo")
async def seed_demo(db: AsyncSession = Depends(get_db)):
    """Populate two sample ADAS projects. Idempotent — skips existing projects."""
    demo_result = await seed_demo_projects(db)
    gate_definitions_seeded = await seed_gate_definitions(db)
    return {
        **demo_result,
        "gate_definitions_seeded": gate_definitions_seeded,
    }


@router.post("/seed-gate-definitions")
async def seed_gate_definition_data(db: AsyncSession = Depends(get_db)):
    """Populate assessment gate definitions from the checklist Excel file."""
    return {
        "gate_definitions_seeded": await seed_gate_definitions(db),
    }
