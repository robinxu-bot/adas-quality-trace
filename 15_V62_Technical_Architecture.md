# 15 — V6.2 Technical Architecture

## 1. Overview

V6.2 transforms PQRETS from a single-file browser prototype into a deployable client-server application. The core UI/UX and domain logic remain unchanged; what changes is the persistence layer (localStorage → PostgreSQL), the delivery mechanism (single HTML → served SPA + REST API), and the operational model (browser-local → shared internal server).

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (Client)                     │
│                                                          │
│   ┌──────────────────────────────────────────────────┐  │
│   │           Frontend SPA (Vite + Vanilla JS)        │  │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│   │  │ Common   │ │ Project  │ │  Sankey / D3 v7  │  │  │
│   │  │  View    │ │  View    │ │  (d3-sankey)     │  │  │
│   │  └──────────┘ └──────────┘ └──────────────────┘  │  │
│   │              api.js (fetch wrapper)               │  │
│   └──────────────────────┬───────────────────────────┘  │
└──────────────────────────│──────────────────────────────┘
                           │ HTTP/REST (JSON)
┌──────────────────────────▼──────────────────────────────┐
│                  Backend (FastAPI / Python)               │
│                                                          │
│   ┌──────────────────────────────────────────────────┐  │
│   │                   API Layer                       │  │
│   │  /api/v1/projects  /api/v1/common  /api/v1/health  │
│   │  scope  goals  requirements  architecture-elements │
│   │  test-cases  risks  evidence  findings  actions    │  │
│   └──────────────────────┬───────────────────────────┘  │
│   ┌──────────────────────▼───────────────────────────┐  │
│   │                 Service Layer                     │  │
│   │  ProjectService  ScopeService  CommonModelService │  │
│   └──────────────────────┬───────────────────────────┘  │
│   ┌──────────────────────▼───────────────────────────┐  │
│   │           Repository / ORM Layer (SQLAlchemy)     │  │
│   └──────────────────────┬───────────────────────────┘  │
└──────────────────────────│──────────────────────────────┘
                           │ SQL
┌──────────────────────────▼──────────────────────────────┐
│                   PostgreSQL Database                    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| Frontend runtime | Vanilla JavaScript + ES Modules | ES2020+ | Preserve existing logic; avoid framework churn |
| Frontend build | Vite | 5.x | Zero-config bundler; native ESM; fast HMR in dev |
| Visualization | D3 v7 + d3-sankey 0.12.3 | (same as V5.9) | No change to Sankey rendering |
| HTTP client | Fetch API (native browser) | — | No extra library needed |
| Backend language | Python | 3.11+ | Team familiarity; rich data processing ecosystem |
| Backend framework | FastAPI | 0.110+ | Async, OpenAPI auto-docs, Pydantic validation |
| ORM | SQLAlchemy 2.x (async) | 2.0+ | Python standard; works well with FastAPI |
| Database | PostgreSQL | 15+ | Reliable, ACID-compliant, suitable for shared internal use |
| DB migrations | Alembic | 1.13+ | SQLAlchemy-native migration tool |
| Reverse proxy | Nginx | 1.25+ | Serves frontend static files; proxies `/api` to FastAPI |
| Containerization | Docker + Docker Compose | 24+ | Reproducible private deployment |

---

## 3. Repository Structure (Target)

```
adas-quality-trace/
├── frontend/                    # Vite project
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.js              # App entry point, router
│       ├── api.js               # All fetch calls to backend
│       ├── state.js             # Reactive state (replaces S object)
│       ├── constants/
│       │   ├── iso.js           # ISO constant (read-only, can also come from API)
│       │   ├── aspects.js       # ASPECTS, MAP, ARCH constants
│       │   └── products.js      # PRODUCT profiles
│       ├── views/
│       │   ├── CommonView.js    # renderCommon() logic
│       │   ├── ProjectView.js   # renderProjects() / renderProjectDetail()
│       │   └── Modal.js         # saveProject() wizard
│       ├── components/
│       │   ├── sankey.js        # sankey(), branch(), filter(), rows()
│       │   ├── dashboard.js     # Dashboard stats rendering
│       │   └── table.js         # Trace chain table
│       └── styles/
│           └── main.css
│
├── backend/                     # FastAPI project
│   ├── main.py                  # FastAPI app, CORS, router mounts
│   ├── requirements.txt
│   ├── alembic/                 # DB migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── config.py            # Settings via env vars (pydantic-settings)
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── project.py
│   │   │   ├── scope.py
│   │   │   └── common.py
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── project.py
│   │   │   ├── scope.py
│   │   │   └── common.py
│   │   ├── routers/             # FastAPI route handlers
│   │   │   ├── projects.py
│   │   │   ├── scope.py
│   │   │   └── common.py
│   │   └── services/            # Business logic
│   │       ├── project_service.py
│   │       ├── scope_service.py
│   │       └── seed_service.py  # Replaces seedDemo()
│   └── tests/
│       ├── test_projects.py
│       └── test_scope.py
│
├── data/                        # Read-only reference JSON (seed data source)
│   ├── 05_ISO25010_Common_Model.json
│   ├── 06_Product_Line_Recommendation_Rules.json
│   ├── 07_ADAS_Quality_Aspect_Mapping.json
│   └── 13_Sample_Project_Data_ADAS.json
│
├── nginx/
│   └── nginx.conf
│
├── docker-compose.yml
├── docker-compose.dev.yml
└── .env.example
```

---

## 4. Frontend Architecture

### 4.1 Module Boundaries

The single `<script>` block of V5.9.1 is split across modules following the same logical structure. No new abstractions are introduced — the goal is a 1:1 refactor.

| V5.9.1 function / block | V6.2 module |
|---|---|
| `ISO`, `ASPECTS`, `MAP`, `ARCH`, `PRODUCT` constants | `src/constants/` |
| Global `S` state object | `src/state.js` |
| `persist()` / `restore()` | Removed — replaced by API calls |
| `renderCommon()` | `src/views/CommonView.js` |
| `renderProjects()` / `renderProjectDetail()` | `src/views/ProjectView.js` |
| `saveProject()`, modal wizard | `src/views/Modal.js` |
| `sankey()`, `branch()`, `filter()`, `rows()` | `src/components/sankey.js` |
| `makeScope()` | `src/services/scopeService.js` (called on project create) |
| All `fetch` / data calls | `src/api.js` |

### 4.2 State Management

`state.js` exports a single reactive `S` object identical in shape to V5.9.1, with the following changes:

- `S.projects` is populated by `GET /api/v1/projects` on page load (replaces `restore()`)
- Mutations that previously called `persist()` now call the appropriate API endpoint
- `S.selectedProject` holds the full project object including scope, fetched on demand via `GET /api/v1/projects/:id`

### 4.3 API Communication

All backend calls are centralized in `src/api.js`. The module exposes named async functions:

```js
export const api = {
  getProjects(),
  getProject(id),
  createProject(data),
  updateProject(id, data),
  deleteProject(id),
  getScope(projectId),
  updateScope(projectId, decisions),
  getCommonModel(),
  exportProject(id),
  importProject(data),
}
```

On error, functions throw with a structured `{ status, message }` object. The UI handles errors at the call site.

---

## 5. Backend Architecture

### 5.1 Layered Design

```
Router (HTTP boundary) → Service (business logic) → Repository (DB queries)
```

Routers handle only request parsing and response serialization. Services contain all domain logic (scope tailoring rules, dashboard calculations, assessment readiness). Repositories contain only SQL/ORM operations.

### 5.2 Common Model Handling

The ISO IEC 25010 common model (`ISO`, `MAP`, `ARCH` constants) is seeded into the database once at startup from the `data/` JSON files. It is read-only at runtime. The frontend may either:

- Fetch it once via `GET /api/v1/common/model` and cache in memory, or
- Continue to embed it as a JS constant (same as V5.9.1) — acceptable since the model is stable

The recommended approach is to keep the common model as a JS constant in the frontend for V6.2, deferring full DB-backed common model management to a later version.

### 5.3 Scope Calculation

`makeScope(productLine)` logic moves to `backend/app/services/scope_service.py`. When a project is created, the backend generates the default `ProjectQualityScope` and persists it. The frontend does not compute scope locally.

---

## 6. Data Flow Comparison

| Operation | V5.9.1 | V6.2 |
|---|---|---|
| Load projects | `restore()` from localStorage | `GET /api/v1/projects` |
| Create project | `saveProject()` → `persist()` | `POST /api/v1/projects` |
| Edit project scope | in-memory + `persist()` | `PATCH /api/v1/projects/:id/scope` |
| Delete project | splice from `S.projects` + `persist()` | `DELETE /api/v1/projects/:id` |
| Export project | `JSON.stringify(S.projects[i])` → download | `GET /api/v1/projects/:id/export` |
| Import project | parse JSON → push to `S.projects` + `persist()` | `POST /api/v1/projects/import` |
| Render Sankey | `build()` → `filter()` → `sankey()` (client-side) | Same — Sankey rendering stays client-side |

Sankey graph construction (`build`, `filter`, `branch`, `rows`) remains entirely client-side — these are pure data transformation functions with no persistence concern.

---

## 7. Development Environment

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop (for PostgreSQL in dev)
- `psql` client (optional, for direct DB inspection)

### Starting the dev environment

```bash
# 1. Start PostgreSQL via Docker
docker compose -f docker-compose.dev.yml up -d db

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head           # run migrations
uvicorn main:app --reload --port 8000

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev                    # Vite dev server on :5173
```

In development, Vite proxies `/api` requests to `http://localhost:8000` via `vite.config.js`.

---

## 8. Non-Functional Requirements for V6.2

| NFR | Target |
|---|---|
| API response time (p95) | < 500 ms for all CRUD endpoints |
| Concurrent users | 10–20 internal users (no horizontal scaling required at V6.2) |
| Data durability | PostgreSQL with daily backup (backup strategy to be defined by ops) |
| Availability | Best-effort; no SLA defined for internal tool |
| Security | HTTPS enforced via Nginx TLS termination; no public internet exposure |
| Browser support | Latest Chrome and Edge (Chromium-based, internal standard) |

---

## 9. Out of Scope for V6.2

The following remain excluded and are not designed for in this version:

- User authentication and role-based access control
- Multi-user concurrent editing or locking
- Integration with external ALM or test management tools
- Excel import / PDF export
- File attachment storage
- Audit logging
- Horizontal scaling / load balancing
