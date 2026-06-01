# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

**PQRETS** (Product Quality Risk and Evidence Traceability System) — a browser-based tool for automotive/ADAS quality engineering. It visualizes ISO IEC 25010 product quality traceability as interactive Sankey diagrams, tailored to five automotive quality aspects: QM, FuSA, CS, SOTIF, AI Safety.

The current running prototype is **V5.9.1** (`index_v5_9_1_persistent.html`). The system is being redesigned as **V6.2** — a frontend-backend separated application. All V6.2 design documents are in this directory.

---

## V5.9.1 Prototype (Current Running Version)

### How to Run

No build step, no install. Open `index_v5_9_1_persistent.html` directly in a browser. Internet access required for CDN dependencies (D3 v7, d3-sankey).

### Stack

- Vanilla JavaScript (no framework, no bundler), everything inline in the single HTML file
- D3 v7 + d3-sankey 0.12.3 (CDN)
- Browser `localStorage` for persistence (key: `pqrets_v591_projects`)

### Key Functions (all in the `<script>` block)

| Function | Purpose |
|---|---|
| `build(project, common)` | Generates Sankey `{nodes, links}` from scope data + mock trace data |
| `makeScope(productLine)` | Creates default Project Quality Scope from product line profile |
| `sankey(el, data, opts)` | Renders D3 Sankey SVG with click-to-highlight |
| `branch(nodeId, data)` | Computes highlighted trace chain for a selected node |
| `filter(data, filters)` | Filters graph by characteristic/aspect/risk/evidence/search |
| `rows(data)` | Extracts structured trace rows for chain table and detail panel |
| `persist()` / `restore()` | Serialise/deserialise `S.projects` to/from localStorage |
| `renderCommon()` | Renders the Common tab |
| `renderProjectDetail()` | Renders dashboard + project-scoped Sankey |
| `saveProject()` | Creates or edits a project via the 5-step modal wizard |

> **Note:** `build()` in V5.9.1 generates mock text and status values (`reqs()`, `eStatus()`, `rLevel()`). These are demo placeholders — not domain logic to preserve in V6.2.

---

## V6.2 Target Architecture (In Design)

### Development Commands

```bash
# Start PostgreSQL (Docker)
docker compose -f docker-compose.dev.yml --env-file .env.dev up -d db

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                    # → http://localhost:5173, /api proxied to :8000

# Production build
cd frontend && npm run build   # output → nginx/static/

# Full production stack
docker compose --env-file .env.prod up -d --build

# Seed demo data (first time only)
curl -X POST http://localhost:8000/api/v1/admin/seed-demo
```

### Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla JS + ES Modules, Vite 5.x, D3 v7 + d3-sankey (npm) |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.x (async), Alembic |
| Database | PostgreSQL 15+ |
| Reverse proxy | Nginx 1.25+ |
| Deployment | Docker Compose |

### Repository Structure (Target)

```
adas-quality-trace/
├── frontend/src/
│   ├── main.js              # Entry point
│   ├── api.js               # All fetch calls
│   ├── state.js             # S object + normalize()
│   ├── constants/aspects.js # ASPECTS enum only
│   ├── views/               # CommonView, ProjectView, Modal
│   └── components/          # sankey.js, dashboard.js, table.js
├── backend/app/
│   ├── routers/             # FastAPI route handlers
│   ├── services/            # Business logic (scope, dashboard, seed)
│   ├── models/              # SQLAlchemy ORM models
│   └── schemas/             # Pydantic request/response schemas
├── data/                    # Read-only reference JSON (seed source)
├── nginx/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.dev                 # Committed — weak dev passwords
└── .env.example             # Template — commit this, not .env.prod
```

### Key Design Decisions

- **Delayed project creation**: `POST /api/v1/projects` is only called when the user confirms Step 5 of the wizard. All wizard data lives in `S.formScope` (frontend memory) until confirmation. Single atomic transaction.
- **Sankey data flow**: `GET /projects/:id/full` fetches the complete flat data tree once. `state.js` `normalize()` converts arrays to `Map<uuid, object>`. `build()` in `sankey.js` consumes the normalized Maps and produces `{nodes, links}`. Node IDs are database UUIDs. All filtering is client-side.
- **Common model**: No JS constants for ISO data. `GET /api/v1/common/model` is called once on page load and cached in `S.commonModel`.
- **`ASPECTS` constant only**: `ISO`, `MAP`, `ARCH`, `PRODUCT` constants are deleted — data comes from the API. Only `ASPECTS = ["QM","FuSA","CS","SOTIF","AI Safety"]` remains as a frontend constant.

---

## Design Documents

| File | Content |
|---|---|
| `01_System_Concept_and_Scope.md` | System purpose, 4-layer architecture, quality aspects, product lines |
| `02_User_Scenario_Derived_Requirements.md` | Three user roles (Product Assessor, Assessment Manager, Project Manager) and derived requirements |
| `03_System_Requirements_Specification.md` | Formal SYSREQ requirements including V6.2 client-server requirements (SYSREQ V62 001–012) |
| `04_Data_Model_Design.md` | Logical data model: 20 named objects, trace relationships, dashboard calculation rules |
| `08_Project_Workspace_UI_Design.md` | UI layout spec for all views |
| `09_Create_Project_Workflow.md` | 5-step Create Project wizard spec |
| `10_Project_Overview_Dashboard_Design.md` | Dashboard cards and metrics design |
| `11_Implementation_Plan.md` | Version roadmap + V6.2 vertical slice plan (7 slices) |
| `14_V5_9_Persistence_Enhancement_Notes.md` | V5.9 localStorage design notes |
| `15_V62_Technical_Architecture.md` | V6.2 overall architecture, tech stack, repo structure |
| `16_REST_API_Specification.md` | All REST endpoints, request/response schemas, enum values |
| `17_Database_Schema_Design.md` | PostgreSQL DDL, enum types, indexes, triggers, seed strategy |
| `18_Frontend_Engineering_Plan.md` | Frontend module structure, `normalize()`, `build()` contract, migration steps |
| `19_Deployment_Guide.md` | Docker Compose setup, env vars, nginx config, backup/restore |
| `UBIQUITOUS_LANGUAGE.md` | Canonical domain glossary — use these terms consistently |

## Reference JSON Files (Design-Time Only)

`05_ISO25010_Common_Model.json`, `06_Product_Line_Recommendation_Rules.json`, `07_ADAS_Quality_Aspect_Mapping.json`, `13_Sample_Project_Data_ADAS.json` — seed sources for the database. Not loaded by the app at runtime.
