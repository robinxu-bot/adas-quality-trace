from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.services.seed_service import run_all_seeds
from app.services.gate_seed_service import seed_gate_definitions
from app.routers import projects, common, admin, scope, dashboard, trace, full, risks, export_import, assessment


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run seed at startup (idempotent)
    async with AsyncSessionLocal() as session:
        await run_all_seeds(session)
        await seed_gate_definitions(session)
    yield


settings = get_settings()

app = FastAPI(
    title="PQRETS API",
    description="Product Quality Risk and Evidence Traceability System",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(scope.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(trace.router, prefix=API_PREFIX)
app.include_router(full.router, prefix=API_PREFIX)
app.include_router(risks.router, prefix=API_PREFIX)
app.include_router(export_import.router, prefix=API_PREFIX)
app.include_router(assessment.router, prefix=API_PREFIX)
app.include_router(common.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)


@app.get(f"{API_PREFIX}/health", tags=["health"])
async def health():
    return {"status": "ok", "version": settings.app_version, "db": "connected"}
