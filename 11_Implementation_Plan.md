# 11 Implementation Plan

# Updated Implementation Plan for V5.8.4

## 1. Purpose

This document defines implementation updates based on the refined UI and system requirements.

## 2. Current Prototype Deliverable

The current prototype deliverable shall be a single browser openable file:

```text
index.html
```

## 3. V5.8.4 Implementation Scope

V5.8.4 shall implement:

- Top level Common tab
- Top level Project tab
- Common full ISO IEC 25010 quality model
- Common Sankey Trace Tree
- Project card overview
- Plus button for project creation
- Create Project modal or intermediate workflow
- Quality Scope Tailoring inside Create Project
- Quality Scope Tailoring for editing existing project
- Project detail dashboard
- Project specific Sankey Trace View
- Project Sankey based on tailored project scope
- Risk Status after Test Result
- QM, FuSA, CS, SOTIF and AI Safety tags

## 4. Implementation Rules

### Rule 1

Common model data shall remain complete.

### Rule 2

Project View shall use Project Quality Scope.

### Rule 3

Create Project shall not be a top level page.

### Rule 4

Quality Scope Tailoring shall not be a top level page.

### Rule 5

Project Sankey shall only show tailored project scope by default.

### Rule 6

Excluded items shall remain reviewable in Quality Scope Tailoring.

### Rule 7

The Sankey graph shall use precise structured trace row highlighting.

## 5. File Structure

For the current prototype:

```text
index.html
```

Later versions may separate:

```text
index.html
data/
  iso25010-common-model.json
  product-line-recommendation-rules.json
  adas-quality-aspect-mapping.json
  projects.json
```

## 6. Next Versions

### V5.8.5

Improve project creation interaction and project card detail.

### V5.9

Add localStorage persistence.

### V6.0

Separate data files.

### V6.1

Add import and export.

### V6.2

Transform PQRETS into a deployable client-server application. Full specification in documents 15–19.

**Scope:**
- Backend: Python + FastAPI, PostgreSQL persistence, Alembic migrations
- Frontend: Vite-based ES Module project refactored from V5.9.1 single HTML file; UI/UX unchanged
- Deployment: Docker Compose (Nginx + FastAPI + PostgreSQL) on internal private server
- Data: localStorage replaced by REST API (`/api/v1/*`); Sankey rendering stays client-side
- Auth: out of scope for V6.2 (no user login)

**Deliverables:**
- `backend/` — FastAPI application with full CRUD for projects, scope, trace chain, risks, evidence, findings, actions
- `frontend/` — Vite project producing deployable static bundle
- `docker-compose.yml` + `docker-compose.dev.yml` — production and development deployment
- `nginx/nginx.conf` — reverse proxy configuration
- `.env.dev` / `.env.example` — environment variable templates

**Reference documents:**
- `15_V62_Technical_Architecture.md` — overall architecture and technology stack
- `16_REST_API_Specification.md` — all API endpoints, request/response schemas
- `17_Database_Schema_Design.md` — PostgreSQL table definitions, indexes, seed strategy
- `18_Frontend_Engineering_Plan.md` — frontend module structure, migration steps from V5.9.1
- `19_Deployment_Guide.md` — Docker Compose setup, Nginx config, backup/restore

**Development approach:** Vertical slices — each slice delivers a complete, working feature end-to-end (backend API + frontend UI). Backend is implemented and verified first within each slice; frontend connects to the real API (no mocks).

---

#### V6.2 Vertical Slice Plan

##### Slice 1 — Project List + Create Project

Backend:
- Database: initial Alembic migration (all tables), seed migration (common model from `data/` JSON files)
- `GET /api/v1/projects` — list all projects with summary counts
- `POST /api/v1/projects` — create project with optional scope payload; backend generates default scope from product line recommendations if scope omitted; atomic transaction
- `GET /api/v1/common/product-lines/:pl/recommendations` — used by wizard Step 4
- `GET /api/v1/health`

Frontend:
- Vite project scaffolding, `src/styles/main.css` extracted from V5.9.1
- `src/api.js`, `src/state.js` (with `normalize()`), `src/constants/aspects.js`
- `src/views/ProjectView.js` — project card list
- `src/views/Modal.js` — 5-step Create Project wizard; scope decisions held in `S.formScope` until Step 5; single `POST /projects` on confirm
- `GET /common/model` cached in `S.commonModel` on page load

Acceptance: User can create a project through the 5-step wizard; project appears in the list; data persists after page refresh.

---

##### Slice 2 — Common View + Common Sankey

Backend:
- `GET /api/v1/common/model` — full ISO IEC 25010 model with subcharacteristics and aspect mappings

Frontend:
- `src/views/CommonView.js` — characteristic selector, subcharacteristic grid
- `src/components/sankey.js` — `build()`, `filter()`, `branch()`, `rows()`, `renderSankey()` extracted and adapted from V5.9.1; `build()` accepts normalized Maps; node IDs are database UUIDs
- Common Sankey Trace Tree rendered from `GET /common/model` data (no JS constants)

Acceptance: Common View shows full ISO model; Common Sankey renders all 11 layers; node click highlights trace chain.

---

##### Slice 3 — Project Detail Dashboard + Scope Editing

Backend:
- `GET /api/v1/projects/:id` — project detail with scope decisions
- `PUT /api/v1/projects/:id` — update project metadata
- `DELETE /api/v1/projects/:id`
- `GET /api/v1/projects/:id/scope`
- `PATCH /api/v1/projects/:id/scope/:subchar_id` — update single scope decision
- `PUT /api/v1/projects/:id/scope` — batch update (used when saving full tailoring table)
- `POST /api/v1/projects/:id/scope/reset`
- `GET /api/v1/projects/:id/dashboard` — pre-computed metrics

Frontend:
- `src/views/ProjectView.js` — project detail panel, dashboard cards, aspect distribution table, risk/evidence summary
- `src/components/dashboard.js` — dashboard card rendering
- Edit Quality Scope flow: opens Modal in edit mode; changes held in memory; saved via `PUT /projects/:id/scope`

Acceptance: Project detail shows dashboard; scope decisions can be edited and saved; dashboard metrics update after scope change.

---

##### Slice 4 — Trace Chain Data (Architecture, Requirements, Test Cases)

Backend:
- `GET/POST/PUT/DELETE /api/v1/projects/:id/architecture-elements`
- `GET/POST/PUT/DELETE /api/v1/projects/:id/architecture-elements/:ae_id/software-modules`
- `GET/POST/PUT/DELETE /api/v1/projects/:id/scope/:subchar_id/goals`
- `GET/POST/PUT/DELETE /api/v1/projects/:id/scope/:subchar_id/goals/:goal_id/requirements`
- `GET/POST/PUT/DELETE /api/v1/projects/:id/requirements/:req_id/sub-requirements`
- `GET/POST/PUT/DELETE /api/v1/projects/:id/software-modules/:sm_id/test-cases`
- `GET/PUT /api/v1/projects/:id/test-cases/:tc_id/result`

Frontend:
- Trace chain editing UI in project detail (forms for requirements, test cases, results)
- `src/components/table.js` — structured trace chain table

Acceptance: Quality Goals, Requirements, Sub-Requirements, Architecture Elements, Software Modules, Test Cases, and Test Results can be created, edited, and deleted through the UI.

---

##### Slice 5 — Project Sankey Trace View

Backend:
- `GET /api/v1/projects/:id/full` — flat structure with all trace chain entities; used as Sankey data source

Frontend:
- Project Sankey Trace View: calls `getProjectFull()` once on open → `normalize()` → `S.projectFull` → `build()` → `renderSankey()`
- Sankey filters (characteristic, aspect, risk, evidence, search text) — all client-side, operate on in-memory `S.projectFull`
- Node click → `branch()` → highlight exact trace chain → `detail()` panel

Acceptance: Project Sankey renders using real database data; filters work without additional API calls; node selection highlights exact trace chain.

---

##### Slice 6 — Risks, Evidence, Findings, Actions

Backend:
- `GET/POST/PUT/DELETE /api/v1/projects/:id/risks`
- `GET/POST/PUT/DELETE /api/v1/projects/:id/evidence`
- `GET/POST/PUT/DELETE /api/v1/projects/:id/findings`
- `GET/POST/PUT/DELETE /api/v1/projects/:id/actions`

Frontend:
- Risk list and risk edit forms in project detail
- Evidence, finding, and action management panels
- Dashboard risk/evidence counts update from live data

Acceptance: Risks, Evidence Items, Assessment Findings, and Action Items can be fully managed; Risk Level is computed by backend; dashboard counts reflect current data.

---

##### Slice 7 — Export, Import, Demo Seed, Deployment

Backend:
- `GET /api/v1/projects/:id/export`
- `POST /api/v1/projects/import`
- `POST /api/v1/admin/seed-demo`

Frontend:
- Export button in project detail (triggers file download)
- Import button in Project View (file picker → `POST /projects/import`)

Deployment:
- `docker-compose.yml` production config
- `docker-compose.dev.yml` development config
- `nginx/nginx.conf`
- `.env.dev`, `.env.example`
- `frontend/npm run build` → `nginx/static/`

Acceptance: Export produces a valid JSON file; import restores a project from that file; `docker compose up` on a clean machine starts the full system; demo seed populates two ADAS projects.

---

**V6.2 Acceptance Criteria:**
1. All V5.9.1 UI/UX is visually identical in V6.2 frontend.
2. Project CRUD operations persist to PostgreSQL (survive server restart).
3. `GET /api/v1/health` returns `{"status": "ok"}`.
4. `docker compose up` on a clean machine starts the full system without manual steps beyond `.env` configuration.
5. The frontend build (`npm run build`) produces a complete static bundle served by Nginx.
6. Project Sankey renders correctly using data fetched from the API.
7. All Sankey filters operate client-side without additional API calls after initial `/full` load.
8. Export → Import round-trip produces an identical project.

## 7. Acceptance Criteria

V5.8.4 is accepted if:

1. It is delivered as index.html.
2. It opens directly in browser.
3. Top level navigation only shows Common and Project.
4. Common shows full ISO IEC 25010 and Common Sankey Trace Tree.
5. Project shows cards and plus button.
6. Plus opens Create Project.
7. Create Project includes Quality Scope Tailoring.
8. Project detail shows dashboard first.
9. Project detail opens Project Sankey Trace View.
10. Project Sankey uses tailored project scope.
