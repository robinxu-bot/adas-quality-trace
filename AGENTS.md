# AGENTS.md

This file gives Codex agents the working rules for this repository. Keep it focused on current project direction, domain language, and implementation guardrails. Do not turn it into a version history.

## What This Is

**PQRETS** (Product Quality Risk and Evidence Traceability System) is a browser-based tool for automotive/ADAS quality engineering.

It visualizes ISO/IEC 25010 product quality traceability and project quality risk for five automotive quality aspects:

- QM
- FuSA
- CS
- SOTIF
- AI Safety

The project is moving toward **V6.2**, a frontend-backend separated application. Treat V6.2 design documents and implementation as the active target.

Legacy note: `index_v5_9_1_persistent.html` is the old V5.9.1 prototype. It may be used as interaction reference, but its mock data generation and inline implementation are not domain logic to preserve.

---

## Current Architecture

| Layer | Technology |
|---|---|
| Frontend | Vanilla JS + ES Modules, Vite, D3 v7 + d3-sankey |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.x async, Alembic |
| Database | PostgreSQL 15+ |
| Reverse proxy | Nginx |
| Deployment | Docker Compose |

Target repository structure:

```text
adas-quality-trace/
├── frontend/src/
│   ├── main.js
│   ├── api.js
│   ├── state.js
│   ├── constants/aspects.js
│   ├── views/
│   └── components/
├── backend/app/
│   ├── routers/
│   ├── services/
│   ├── models/
│   └── schemas/
├── data/
├── nginx/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.dev
└── .env.example
```

---

## Development Commands

```bash
# Start PostgreSQL
docker compose -f docker-compose.dev.yml --env-file .env.dev up -d db

# Backend
cd backend
python -m venv .venv
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Production build
cd frontend
npm run build

# Full production stack
docker compose --env-file .env.prod up -d --build

# Seed demo data
curl -X POST http://localhost:8000/api/v1/admin/seed-demo
```

When validating frontend changes, run `npm run build`. When validating backend Python changes, run a compile check such as `python -m compileall backend/app` from the repo root or through the project environment.

---

## Key Implementation Decisions

- **Delayed project creation**: `POST /api/v1/projects` is only called when the user confirms Step 5 of the wizard. Wizard data stays in frontend memory until confirmation. Project creation should be a single atomic transaction.
- **Sankey data flow**: `GET /projects/:id/full` fetches the complete flat project data tree. `state.js` `normalize()` converts arrays to `Map<uuid, object>`. `sankey.js` `build()` consumes normalized Maps and produces `{nodes, links}`.
- **Common model from API**: Do not hardcode ISO model data in frontend JS. Fetch `GET /api/v1/common/model` once on page load and cache it in `S.commonModel`.
- **Frontend constants**: Keep only the `ASPECTS = ["QM","FuSA","CS","SOTIF","AI Safety"]` enum as a frontend constant. ISO/model/mapping/product data comes from the API.
- **V5 mock logic is not domain logic**: V5.9.1 helper functions such as demo requirement/status/risk generation are placeholders and should not be migrated as business rules.

---

## Assessment Dashboard Domain Rules

Use these rules when editing `22_Audit_Report_And_Lifecycle_Maturity_Design*.md`, `23_Audit_Report_Dashboard_Implementation_Tasks.md`, or the assessment dashboard implementation.

- The assessment dashboard is a risk and maturity display. It does not maintain management decisions, approval conclusions, or decision records.
- The dashboard shows one formal report result. Do not reintroduce separate AI draft score, human-reviewed score, pending human confirmation, or AI report data flow in this dashboard.
- "Review" in maturity scoring means the deliverable, evidence, or work product has been technically reviewed or accepted. It is not a review of an AI-generated report.
- Use **Quality Sub-Characteristic** for ISO/IEC 25010 subcharacteristics. Avoid "Quality Attribute" unless explicitly discussing deprecated terminology.
- Use **Lifecycle Activity Maturity**, not "Lifecycle & Process Maturity" or "Lifecycle & Product Maturity".
- The fixed assessment dashboard views are: Assessment Snapshot, Quality Gate Maturity, Project Risk Posture, Quality Sub-Characteristic Maturity, Lifecycle Activity Maturity, and Team Activity & Work Product Matrix.
- Quality Gate Maturity, Quality Sub-Characteristic Maturity, and Lifecycle Activity Maturity are different aggregations over the same formal `Activity x Gate` result base, not independent scoring systems.
- Quality Sub-Characteristic Maturity is grouped by `Characteristic -> Quality Sub-Characteristic -> Quality Aspect -> Activity x Gate`. Safety-related subcharacteristics such as Risk identification, Fail safe, and Hazard warning should be grouped under Safety.
- A Quality Sub-Characteristic can relate to QM, FuSA, CS, SOTIF, and/or AI Safety. The UI should show the related aspects and the technical rationale.
- Aspect rationale must come from the ADAS quality aspect mapping model, for example `07_ADAS_Quality_Aspect_Mapping.json` `mappingReason`. A project scope selection only means the aspect is assessed for that project; it is not a technical rationale.
- ISO 26262, ISO/SAE 21434, SOTIF / ISO 21448, and ISO/PAS 8800 should be displayed as separate lifecycle/activity families. SOTIF and AI Safety can be trace-linked but must not be merged.
- ISO/PAS 8800 lifecycle coverage must include AI/data lifecycle activities.
- Team Activity & Work Product Matrix uses activity rows and team columns. Default ADAS team columns are: PdM/PgM/PjM AD/ADAS, 360 deg Perception AD/ADAS Safety, Map (Vehicle) CA & AD/ADAS Non-Safety, LaneLevelLocalization AD/ADAS Non-Safety, MotionPlanner AD/ADAS Safety-Rule, MotionPlanner AD/ADAS Safety-ML (SWC: DDTP), InterCommBev (Application Framework), Controller AD/ADAS Safety, Product Integrity, and optional Product Delivery.
- Team roles should distinguish Accountable, Contributing, Reviewer / Approver, and Not applicable. Product Integrity may review or approve, but should not replace the accountable activity owner.

---

## Design Documents

Use these documents as the source of truth before changing implementation:

| File | Content |
|---|---|
| `01_System_Concept_and_Scope.md` | System purpose, architecture, quality aspects, product lines |
| `02_User_Scenario_Derived_Requirements.md` | User roles and derived requirements |
| `03_System_Requirements_Specification.md` | Formal system requirements |
| `04_Data_Model_Design.md` | Logical data model, trace relationships, dashboard calculations |
| `08_Project_Workspace_UI_Design.md` | UI layout spec |
| `09_Create_Project_Workflow.md` | Create Project wizard |
| `10_Project_Overview_Dashboard_Design.md` | Project overview dashboard |
| `15_V62_Technical_Architecture.md` | V6.2 architecture and repo structure |
| `16_REST_API_Specification.md` | REST endpoints and schemas |
| `17_Database_Schema_Design.md` | PostgreSQL schema, indexes, seed strategy |
| `18_Frontend_Engineering_Plan.md` | Frontend module structure and migration plan |
| `20_Gate_Assessment_Design.md` | QG0-QG5 assessment model |
| `21_AI_Agent_Integration_Spec.md` | AI agent integration outside the formal assessment dashboard result |
| `22_Audit_Report_And_Lifecycle_Maturity_Design.md` | Assessment dashboard views and maturity model |
| `22_Audit_Report_And_Lifecycle_Maturity_Design.zh.md` | Chinese assessment dashboard design document for stakeholder review |
| `23_Audit_Report_Dashboard_Implementation_Tasks.md` | Assessment dashboard implementation slices |
| `UBIQUITOUS_LANGUAGE.md` | Canonical domain glossary |

---

## Reference Data

Reference JSON files are design-time and seed sources:

- `05_ISO25010_Common_Model.json`
- `06_Product_Line_Recommendation_Rules.json`
- `07_ADAS_Quality_Aspect_Mapping.json`
- `13_Sample_Project_Data_ADAS.json`

The runtime app should load common/model data through the backend API, not by importing these JSON files directly in frontend code.
