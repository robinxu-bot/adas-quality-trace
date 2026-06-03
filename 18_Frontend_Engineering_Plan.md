# 18 — Frontend Engineering Plan

## 1. Goal

Refactor the V5.9.1 single-file `index_v5_9_1_persistent.html` into a Vite-based ES Module project. The refactor is a **structural decomposition, not a rewrite** — all existing rendering logic, D3 Sankey code, and UI/UX are preserved. The diff between V5.9.1 and V6.2 should be zero in visual output and user interaction.

---

## 2. What Changes vs. What Stays

| Concern | V5.9.1 | V6.2 | Notes |
|---|---|---|---|
| UI layout and CSS | Inline `<style>` | `src/styles/main.css` | Extracted verbatim |
| HTML shell | Everything in one file | `index.html` (minimal shell) | Only `<div id="app">` and script tag |
| `ISO`, `MAP`, `ARCH` constants | Inline in `<script>` | Deleted — data from `GET /common/model` | |
| `PRODUCT` constant | Inline in `<script>` | Deleted — data from `GET /common/product-lines/:pl/recommendations` | |
| `ASPECTS` constant | Inline in `<script>` | `src/constants/aspects.js` | Only constant kept |
| Application state (`S`) | Global var | `src/state.js` (exported object) | Same shape |
| `persist()` / `restore()` | localStorage calls | Removed — replaced by API | See api.js |
| `renderCommon()` | Global function | `src/views/CommonView.js` | Extracted |
| `renderProjects()` / `renderProjectDetail()` | Global function | `src/views/ProjectView.js` | Extracted |
| Modal wizard (`saveProject()`) | Global function | `src/views/Modal.js` | Extracted |
| `sankey()`, `branch()`, `filter()`, `rows()` | Global functions | `src/components/sankey.js` | Extracted verbatim |
| `makeScope()` | Client-side | Removed — server computes scope | Called via `POST /api/v1/projects` |
| `seedDemo()` | Client-side | Removed — server handles seeding | Backend `seed_service.py` |
| D3 / d3-sankey | CDN `<script>` tags | npm packages (`d3`, `d3-sankey`) | Bundled by Vite |

---

## 3. Target File Structure

```
frontend/
├── index.html                  # Minimal HTML shell
├── vite.config.js
├── package.json
└── src/
    ├── main.js                 # Entry: init(), nav event handlers, initial render
    ├── api.js                  # All fetch calls (replaces persist/restore)
    ├── state.js                # S object + normalize() — converts /full response to Maps
    ├── constants/
    │   └── aspects.js          # ASPECTS = ["QM","FuSA","CS","SOTIF","AI Safety"] only
    ├── views/
    │   ├── CommonView.js       # renderCommon() — data from GET /common/model
    │   ├── ProjectView.js      # renderProjects(), renderProjectDetail()
    │   └── Modal.js            # openModal(), saveProject(), wizard step logic
    ├── components/
    │   ├── sankey.js           # build(), branch(), filter(), rows(), renderSankey()
    │   ├── dashboard.js        # renderDashboard() stats cards
    │   └── table.js            # renderTraceTable() chain table
    └── styles/
        └── main.css
```

Audit Report Dashboard additions:

- `src/views/AuditReportView.js` renders the full Audit Report Dashboard.
- `src/components/auditReport.js` renders Audit Snapshot, Quality Gate Maturity, Project Risk Posture, and Lifecycle & Process Maturity sections.
- `src/components/dashboard.js` renders the project detail entry dashboard and may show executive risk signals, but it does not own approval or decision workflows.
- The view structure, risk signals, and scoring semantics are defined in `22_Audit_Report_And_Lifecycle_Maturity_Design.md`.

---

## 4. Module Boundaries and Contracts

### 4.1 `src/state.js`

Exports the single `S` object. All view modules import `S` from here — no module holds its own copy of project data.

```js
// state.js
export const S = {
  view: 'common',             // 'common' | 'projects' | 'project-detail'
  commonChar: null,
  commonModel: null,          // cached response from GET /common/model
  projects: [],               // loaded from GET /api/v1/projects on init
  selectedProject: null,      // summary object from project list
  projectFull: null,          // normalized full data from GET /projects/:id/full
  selectedNode: null,         // UUID of selected Sankey node
  formScope: [],              // wizard in-memory scope (not persisted until Step 5)
  formMode: 'create',         // 'create' | 'edit'
  editId: null,
  showExcluded: false,
  mAspect: null,
  mApp: null,
  filters: {}
}

// normalize() converts the flat /full response into Maps for O(1) lookup.
// Called once after GET /projects/:id/full; result stored in S.projectFull.
export function normalize(fullResponse) {
  return {
    project:              fullResponse.project,
    scope:                new Map(fullResponse.scope.map(x => [x.subchar_id, x])),
    goals:                new Map(fullResponse.goals.map(x => [x.id, x])),
    reqs:                 new Map(fullResponse.requirements.map(x => [x.id, x])),
    subReqs:              new Map(fullResponse.sub_requirements.map(x => [x.id, x])),
    archElems:            new Map(fullResponse.architecture_elements.map(x => [x.id, x])),
    modules:              new Map(fullResponse.software_modules.map(x => [x.id, x])),
    testCases:            new Map(fullResponse.test_cases.map(x => [x.id, x])),
    testResults:          new Map(fullResponse.test_results.map(x => [x.tc_id, x])),  // keyed by tc_id
    risks:                new Map(fullResponse.risks.map(x => [x.id, x])),
  }
}
```

State mutations trigger re-renders by calling the appropriate render function explicitly — no reactive framework (same pattern as V5.9.1).

`S.formScope` holds the wizard's in-memory scope decisions during Create Project. It is **never persisted** until the user confirms Step 5, at which point the entire payload is sent as a single `POST /api/v1/projects` request.

### 4.2 `src/api.js`

All network calls are in one module. No other module calls `fetch` directly.

```js
// api.js
const BASE = '/api/v1'

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw { status: res.status, message: err.detail }
  }
  return res.status === 204 ? null : res.json()
}

export const api = {
  // Projects
  getProjects:              ()                  => request('GET',    '/projects'),
  getProject:               (id)                => request('GET',    `/projects/${id}`),
  getProjectFull:           (id)                => request('GET',    `/projects/${id}/full`),
  createProject:            (data)              => request('POST',   '/projects', data),
  updateProject:            (id, data)          => request('PUT',    `/projects/${id}`, data),
  deleteProject:            (id)                => request('DELETE', `/projects/${id}`),
  exportProject:            (id)                => request('GET',    `/projects/${id}/export`),
  importProject:            (data)              => request('POST',   '/projects/import', data),
  getDashboard:             (id)                => request('GET',    `/projects/${id}/dashboard`),
  getAuditReportDashboard:  (id, params)        => request('GET',    `/projects/${id}/audit-report/dashboard${params ? '?' + new URLSearchParams(params) : ''}`),

  // Scope
  getScope:                 (pid)               => request('GET',    `/projects/${pid}/scope`),
  updateScopeDecision:      (pid, scid, data)   => request('PATCH',  `/projects/${pid}/scope/${scid}`, data),
  batchUpdateScope:         (pid, data)         => request('PUT',    `/projects/${pid}/scope`, data),
  resetScope:               (pid)               => request('POST',   `/projects/${pid}/scope/reset`),

  // Architecture elements & software modules
  getArchElements:          (pid)               => request('GET',    `/projects/${pid}/architecture-elements`),
  createArchElement:        (pid, data)         => request('POST',   `/projects/${pid}/architecture-elements`, data),
  updateArchElement:        (pid, eid, data)    => request('PUT',    `/projects/${pid}/architecture-elements/${eid}`, data),
  deleteArchElement:        (pid, eid)          => request('DELETE', `/projects/${pid}/architecture-elements/${eid}`),
  getSoftwareModules:       (pid, eid)          => request('GET',    `/projects/${pid}/architecture-elements/${eid}/software-modules`),
  createSoftwareModule:     (pid, eid, data)    => request('POST',   `/projects/${pid}/architecture-elements/${eid}/software-modules`, data),
  updateSoftwareModule:     (pid, eid, mid, d)  => request('PUT',    `/projects/${pid}/architecture-elements/${eid}/software-modules/${mid}`, d),
  deleteSoftwareModule:     (pid, eid, mid)     => request('DELETE', `/projects/${pid}/architecture-elements/${eid}/software-modules/${mid}`),

  // Quality goals
  getGoals:                 (pid, scid)         => request('GET',    `/projects/${pid}/scope/${scid}/goals`),
  createGoal:               (pid, scid, data)   => request('POST',   `/projects/${pid}/scope/${scid}/goals`, data),
  updateGoal:               (pid, scid, gid, d) => request('PUT',    `/projects/${pid}/scope/${scid}/goals/${gid}`, d),
  deleteGoal:               (pid, scid, gid)    => request('DELETE', `/projects/${pid}/scope/${scid}/goals/${gid}`),

  // Quality requirements
  getRequirements:          (pid, scid, gid)    => request('GET',    `/projects/${pid}/scope/${scid}/goals/${gid}/requirements`),
  createRequirement:        (pid, scid, gid, d) => request('POST',   `/projects/${pid}/scope/${scid}/goals/${gid}/requirements`, d),
  updateRequirement:        (pid, scid, gid, rid, d) => request('PUT', `/projects/${pid}/scope/${scid}/goals/${gid}/requirements/${rid}`, d),
  deleteRequirement:        (pid, scid, gid, rid)    => request('DELETE', `/projects/${pid}/scope/${scid}/goals/${gid}/requirements/${rid}`),

  // Sub-requirements
  getSubRequirements:       (pid, rid)          => request('GET',    `/projects/${pid}/requirements/${rid}/sub-requirements`),
  createSubRequirement:     (pid, rid, data)    => request('POST',   `/projects/${pid}/requirements/${rid}/sub-requirements`, data),
  updateSubRequirement:     (pid, rid, sid, d)  => request('PUT',    `/projects/${pid}/requirements/${rid}/sub-requirements/${sid}`, d),
  deleteSubRequirement:     (pid, rid, sid)     => request('DELETE', `/projects/${pid}/requirements/${rid}/sub-requirements/${sid}`),

  // Test cases & results
  getTestCases:             (pid, mid)          => request('GET',    `/projects/${pid}/software-modules/${mid}/test-cases`),
  createTestCase:           (pid, mid, data)    => request('POST',   `/projects/${pid}/software-modules/${mid}/test-cases`, data),
  updateTestCase:           (pid, mid, tid, d)  => request('PUT',    `/projects/${pid}/software-modules/${mid}/test-cases/${tid}`, d),
  deleteTestCase:           (pid, mid, tid)     => request('DELETE', `/projects/${pid}/software-modules/${mid}/test-cases/${tid}`),
  getTestResult:            (pid, tid)          => request('GET',    `/projects/${pid}/test-cases/${tid}/result`),
  updateTestResult:         (pid, tid, data)    => request('PUT',    `/projects/${pid}/test-cases/${tid}/result`, data),

  // Risks
  getRisks:                 (pid, params)       => request('GET',    `/projects/${pid}/risks${params ? '?' + new URLSearchParams(params) : ''}`),
  createRisk:               (pid, data)         => request('POST',   `/projects/${pid}/risks`, data),
  updateRisk:               (pid, rid, data)    => request('PUT',    `/projects/${pid}/risks/${rid}`, data),
  deleteRisk:               (pid, rid)          => request('DELETE', `/projects/${pid}/risks/${rid}`),

  // Evidence
  getEvidence:              (pid)               => request('GET',    `/projects/${pid}/evidence`),
  createEvidence:           (pid, data)         => request('POST',   `/projects/${pid}/evidence`, data),
  updateEvidence:           (pid, eid, data)    => request('PUT',    `/projects/${pid}/evidence/${eid}`, data),
  deleteEvidence:           (pid, eid)          => request('DELETE', `/projects/${pid}/evidence/${eid}`),

  // Assessment findings
  getFindings:              (pid)               => request('GET',    `/projects/${pid}/findings`),
  createFinding:            (pid, data)         => request('POST',   `/projects/${pid}/findings`, data),
  updateFinding:            (pid, fid, data)    => request('PUT',    `/projects/${pid}/findings/${fid}`, data),
  deleteFinding:            (pid, fid)          => request('DELETE', `/projects/${pid}/findings/${fid}`),

  // Action items
  getActions:               (pid)               => request('GET',    `/projects/${pid}/actions`),
  createAction:             (pid, data)         => request('POST',   `/projects/${pid}/actions`, data),
  updateAction:             (pid, aid, data)    => request('PUT',    `/projects/${pid}/actions/${aid}`, data),
  deleteAction:             (pid, aid)          => request('DELETE', `/projects/${pid}/actions/${aid}`),

  // Common model
  getCommonModel:           ()                  => request('GET',    '/common/model'),
  getProductLineRecs:       (pl)                => request('GET',    `/common/product-lines/${pl}/recommendations`),

  // Admin
  seedDemo:                 ()                  => request('POST',   '/admin/seed-demo'),
}
```

### 4.3 `src/components/sankey.js`

Pure data transformation and rendering functions. No API calls, no state mutation.

```
build(normalizedData)         → { nodes[], links[] }
filter(graphData, filters)    → { nodes[], links[] }
branch(nodeUUID, graphData)   → { ids: Set, keys: Set }
rows(graphData)               → traceRow[]
renderSankey(elementId, graphData, opts)  → void (D3 DOM mutation only)
```

**`build(normalizedData)`** receives `S.projectFull` (the output of `normalize()`) — a set of Maps keyed by UUID. It iterates `normalizedData.scope.values()`, follows the chain through goals → requirements → sub-requirements → architecture elements → modules → test cases → test results, and produces Sankey `nodes` and `links`. Node IDs are the database UUIDs directly.

**Key difference from V5.9.1:** `build()` no longer generates mock text or computes status values — all labels, risk levels, evidence status, and aspect tags come from the real data in the Maps.

`renderSankey()` is renamed from V5.9.1's `sankey()` to avoid collision with the imported `d3-sankey` `sankey` layout function.

### 4.4 `src/main.js`

Application entry point. Responsibilities:
1. On `DOMContentLoaded`: call `api.getProjects()`, populate `S.projects`, call `renderCommon()`
2. Wire nav click handlers (Common / Projects tabs)
3. Wire global event delegation (project card clicks, modal open/close, filter changes)

---

## 5. `index.html` Shell

The full HTML markup from V5.9.1 (header, nav, content containers, modal scaffold) moves into `index.html` as static HTML. D3 is loaded via npm + Vite, not CDN `<script>` tags.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PQRETS — Product Quality Risk and Evidence Traceability System</title>
  <link rel="stylesheet" href="/src/styles/main.css" />
</head>
<body>
  <!-- Header, nav, content divs extracted from V5.9.1 -->
  <header id="app-header">...</header>
  <nav id="app-nav">...</nav>
  <main id="app-content"></main>
  <div id="modal-overlay" class="hidden">...</div>

  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

---

## 6. `vite.config.js`

```js
import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: '../nginx/static',   // Vite build output goes to nginx/static/
    emptyOutDir: true
  }
})
```

---

## 7. `package.json`

```json
{
  "name": "pqrets-frontend",
  "version": "6.2.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "d3": "^7.9.0",
    "d3-sankey": "^0.12.3"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
```

---

## 8. Handling the `makeScope` Removal

In V5.9.1, `makeScope(productLine)` runs client-side when a new project is created (Step 2 of the wizard). In V6.2, the wizard calls `api.createProject(data)`, and the backend runs `makeScope` logic during `POST /api/v1/projects`. The wizard receives the created project with pre-populated scope decisions in the response.

The Step 4 tailoring table is then populated from `response.scope` rather than from a local call to `makeScope()`.

---

## 9. Error Handling Pattern

All `api.js` calls are wrapped with try/catch at the call site in view/modal code:

```js
try {
  const project = await api.createProject(formData)
  S.projects.push(project)
  renderProjects()
  closeModal()
} catch (err) {
  showInlineError(`Failed to create project: ${err.message}`)
}
```

A shared `showInlineError(msg)` utility renders an error banner at the top of the active content area. No `alert()` calls.

---

## 10. Development Workflow

```bash
# Start backend + DB (see 19_Deployment_Guide.md for Docker Compose setup)
cd backend
uvicorn main:app --reload --port 8000

# Start frontend dev server (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
# → /api/* proxied to http://localhost:8000
```

No separate build step is required during development. Vite's HMR handles file changes.

For production:
```bash
cd frontend
npm run build
# Output to nginx/static/ — served by Nginx
```

---

## 11. Migration Path from V5.9.1

1. Create `frontend/` and initialize Vite project (`npm create vite@latest`)
2. Copy inline CSS from V5.9.1 `<style>` block → `src/styles/main.css`
3. Copy HTML structure from V5.9.1 `<body>` → `index.html`
4. Create `src/constants/aspects.js` with only the `ASPECTS` array; delete `ISO`, `MAP`, `ARCH`, `PRODUCT` — these come from the API
5. Extract `sankey()`, `branch()`, `filter()`, `rows()` → `src/components/sankey.js`; rename `sankey()` → `renderSankey()`; update `build()` to accept `normalizedData` (Maps) instead of the V5.9.1 project object
6. Extract render functions → `src/views/`
7. Write `src/state.js` with `S` object and `normalize()` function
8. Write `src/api.js` with all endpoints including `getProjectFull()` and `getCommonModel()`
9. Write `src/main.js`: on load call `api.getCommonModel()` → cache in `S.commonModel`, then `api.getProjects()` → `S.projects`, then `renderCommon()`
10. Replace CDN D3 `<script>` tags with `import * as d3 from 'd3'` and `import { sankey as d3Sankey } from 'd3-sankey'`
11. Delete `makeScope()`, `seedDemo()`, `persist()`, `restore()`, `eStatus()`, `rLevel()`, `rStatus()`, `reqs()` — all replaced by real data from backend
12. Wire Sankey open: on project card click, call `api.getProjectFull(id)` → `normalize()` → `S.projectFull` → `build(S.projectFull)` → `renderSankey()`
13. Run `npm run dev` and verify visual parity against V5.9.1 using the backend's demo data
