# 16 — REST API Specification

## 1. Conventions

- Base path: `/api/v1`
- All request and response bodies are `application/json`
- Dates: ISO 8601 string — date-only fields use `"2026-06-01"`, datetime fields use `"2026-06-01T09:00:00Z"`
- IDs: UUID v4 strings (system-generated); human-readable IDs (e.g. `"PRJ-001"`) are separate string fields
- HTTP status codes: 200 OK, 201 Created, 204 No Content, 400 Bad Request, 404 Not Found, 422 Unprocessable Entity, 500 Internal Server Error
- Error response body (all 4xx/5xx):

```json
{ "detail": "Human-readable error message" }
```

### Enum reference

| Type | Values |
|---|---|
| `quality_aspect` | `"QM"`, `"FuSA"`, `"CS"`, `"SOTIF"`, `"AI Safety"` |
| `product_line` | `"AreneTools"`, `"ADAS"`, `"WovenCity"`, `"CloudAI"` |
| `project_phase` | `"Concept"`, `"Development"`, `"Validation"`, `"Production"` |
| `applicability` | `"Applicable"`, `"Partially applicable"`, `"Not applicable"`, `"Deferred"`, `"Covered by platform"`, `"Covered by supplier"`, `"Out of project scope"` |
| `risk_level` | `"Critical"`, `"High"`, `"Medium"`, `"Low"` |
| `risk_status` | `"Open"`, `"Mitigated"`, `"Accepted"`, `"Closed"` |
| `test_result` | `"Pass"`, `"Fail"`, `"Blocked"`, `"Not run"` |
| `evidence_status` | `"Complete"`, `"Partial"`, `"Missing"`, `"Failed"` |
| `review_status` | `"Draft"`, `"Reviewed"`, `"Approved"` |
| `finding_status` | `"Open"`, `"In Progress"`, `"Resolved"`, `"Closed"` |
| `action_status` | `"Open"`, `"In Progress"`, `"Closed"` |

---

## 2. Projects

### 2.1 List Projects

```
GET /api/v1/projects
```

Returns all projects as summary cards. Does not include full scope or trace chain data.

**Response 200**

```json
[
  {
    "id": "uuid",
    "project_id": "PRJ-001",
    "name": "ADAS Highway Pilot",
    "product_type": "ADAS ECU",
    "product_line": "ADAS",
    "phase": "Concept",
    "system_boundary": "Onboard perception and planning stack",
    "assessment_target": "ISO 26262 ASIL-B, SOTIF",
    "customer": "Woven by Toyota",
    "selected_aspects": ["QM", "FuSA", "SOTIF"],
    "selected_subchar_count": 18,
    "open_risk_count": 3,
    "evidence_gap_count": 5,
    "assessment_readiness": "Conditionally ready",
    "created_at": "2026-06-01T09:00:00Z",
    "updated_at": "2026-06-01T12:00:00Z"
  }
]
```

---

### 2.2 Get Project Detail

```
GET /api/v1/projects/{id}
```

Returns the full project object including scope decisions. Trace chain objects (goals, requirements, architecture elements, etc.) are loaded via separate endpoints.

**Response 200**

```json
{
  "id": "uuid",
  "project_id": "PRJ-001",
  "name": "ADAS Highway Pilot",
  "product_type": "ADAS ECU",
  "product_line": "ADAS",
  "phase": "Concept",
  "system_boundary": "Onboard perception and planning stack",
  "assessment_target": "ISO 26262 ASIL-B, SOTIF",
  "customer": "Woven by Toyota",
  "selected_aspects": ["QM", "FuSA", "SOTIF"],
  "scope": [
    {
      "id": "uuid",
      "subchar_id": "perf-eff-time",
      "subchar_name": "Time Behaviour",
      "characteristic_id": "perf-eff",
      "characteristic_name": "Performance Efficiency",
      "applicability": "Applicable",
      "rationale": "Real-time processing is safety-critical",
      "recommended_applicability": "Applicable",
      "recommendation_reason": "ADAS systems require deterministic timing",
      "selected_quality_aspects": ["QM", "FuSA"],
      "manual_override": false,
      "decision_owner": "J. Smith",
      "decision_date": "2026-06-01",
      "review_status": "Reviewed"
    }
  ],
  "created_at": "2026-06-01T09:00:00Z",
  "updated_at": "2026-06-01T12:00:00Z"
}
```

**Response 404**

---

### 2.3 Create Project

```
POST /api/v1/projects
```

Creates a new project and persists it atomically in a single transaction. The `scope` field is optional:
- If omitted, the backend generates the default `ProjectQualityScope` from the product line recommendations.
- If provided, the backend uses the supplied scope decisions directly.

The project is **not created until this endpoint is called** — the Create Project wizard holds all data in frontend memory until Step 5 is confirmed (no draft/rollback needed).

**Request body**

```json
{
  "project_id": "PRJ-001",
  "name": "ADAS Highway Pilot",
  "product_type": "ADAS ECU",
  "product_line": "ADAS",
  "phase": "Concept",
  "system_boundary": "Onboard perception and planning stack",
  "assessment_target": "ISO 26262 ASIL-B, SOTIF",
  "customer": "Woven by Toyota",
  "selected_aspects": ["QM", "FuSA", "SOTIF"],
  "scope": [
    {
      "subchar_id": "perf-eff-time",
      "applicability": "Applicable",
      "rationale": "Real-time processing is safety-critical",
      "selected_quality_aspects": ["QM", "FuSA"],
      "manual_override": true,
      "decision_owner": "J. Smith",
      "decision_date": "2026-06-01",
      "review_status": "Draft"
    }
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `project_id` | string | Yes | Must be unique |
| `name` | string | Yes | |
| `product_type` | string | Yes | Free text |
| `product_line` | enum | Yes | |
| `phase` | enum | Yes | |
| `system_boundary` | string | Yes | |
| `assessment_target` | string | No | |
| `customer` | string | No | |
| `selected_aspects` | array of enum | Yes | Subset of quality aspects |
| `scope` | array | No | If omitted, backend generates default scope from product line recommendations. If provided, used as-is. All `subchar_id` values must exist in `common_subcharacteristics`. |

**Response 201** — full project object (same shape as GET detail)

**Response 422** — duplicate `project_id` or invalid enum value

---

### 2.4 Update Project

```
PUT /api/v1/projects/{id}
```

Updates project metadata. Does not affect scope decisions.

**Request body** — same fields as Create; all optional except `name`

**Response 200** — updated project summary (same shape as list item)

**Response 404**

---

### 2.5 Delete Project

```
DELETE /api/v1/projects/{id}
```

Permanently deletes the project and all associated data (scope, trace chain, risks, evidence, findings, actions).

**Response 204**

**Response 404**

---

### 2.6 Export Project

```
GET /api/v1/projects/{id}/export
```

Returns the complete project as a portable JSON document.

**Response 200** — `Content-Disposition: attachment; filename="PRJ-001.json"`

```json
{
  "export_version": "1.0",
  "exported_at": "2026-06-01T12:00:00Z",
  "project": { /* full project object including scope, trace chain, risks, evidence */ }
}
```

---

### 2.7 Import Project

```
POST /api/v1/projects/import
```

Imports a project from an export document. Fails if `project_id` already exists.

**Request body** — same shape as export response

**Response 201** — imported project (full detail shape)

**Response 422** — invalid format or duplicate `project_id`

---

## 3. Project Scope

### 3.1 Get Project Scope

```
GET /api/v1/projects/{id}/scope
```

**Response 200** — array of scope decision objects (same shape as `scope` array in project detail)

---

### 3.2 Update Single Scope Decision

```
PATCH /api/v1/projects/{id}/scope/{subchar_id}
```

**Request body**

```json
{
  "applicability": "Partially applicable",
  "rationale": "Only relevant for autonomous mode",
  "selected_quality_aspects": ["QM", "FuSA"],
  "manual_override": true,
  "decision_owner": "J. Smith",
  "decision_date": "2026-06-01",
  "review_status": "Draft"
}
```

All fields optional; only provided fields are updated.

**Response 200** — updated scope decision object

**Response 404** — project or subcharacteristic not found

**Response 422** — invalid enum value

---

### 3.3 Batch Update Scope

```
PUT /api/v1/projects/{id}/scope
```

Replaces all scope decisions in one operation. Used when saving the full tailoring table from the Create Project wizard (Step 4 → Step 5 → Save).

**Request body**

```json
[
  {
    "subchar_id": "perf-eff-time",
    "applicability": "Applicable",
    "rationale": "...",
    "selected_quality_aspects": ["QM", "FuSA"],
    "manual_override": false,
    "decision_owner": "J. Smith",
    "decision_date": "2026-06-01",
    "review_status": "Draft"
  }
]
```

**Response 200** — full updated scope array

**Response 422** — unknown `subchar_id` or invalid enum value

---

### 3.4 Reset Scope to Default

```
POST /api/v1/projects/{id}/scope/reset
```

Regenerates default scope from product line recommendations, discarding all manual tailoring.

**Response 200** — regenerated scope array

---

## 4. Architecture Elements and Software Modules

### 4.1 Architecture Elements

```
GET    /api/v1/projects/{id}/architecture-elements
POST   /api/v1/projects/{id}/architecture-elements
PUT    /api/v1/projects/{id}/architecture-elements/{ae_id}
DELETE /api/v1/projects/{id}/architecture-elements/{ae_id}
```

**Architecture element fields**

| Field | Type | Required | Notes |
|---|---|---|---|
| `element_id` | string | Yes | Human-readable, e.g. `"AE-001"` |
| `name` | string | Yes | |
| `description` | string | No | |

**GET response 200**

```json
[
  {
    "id": "uuid",
    "element_id": "AE-001",
    "name": "Perception Module",
    "description": "Camera and lidar processing pipeline",
    "software_modules": [
      { "id": "uuid", "module_id": "SM-001", "name": "cam_pipeline" }
    ]
  }
]
```

---

### 4.2 Software Modules

```
GET    /api/v1/projects/{id}/architecture-elements/{ae_id}/software-modules
POST   /api/v1/projects/{id}/architecture-elements/{ae_id}/software-modules
PUT    /api/v1/projects/{id}/architecture-elements/{ae_id}/software-modules/{sm_id}
DELETE /api/v1/projects/{id}/architecture-elements/{ae_id}/software-modules/{sm_id}
```

**Software module fields**

| Field | Type | Required | Notes |
|---|---|---|---|
| `module_id` | string | Yes | Human-readable, e.g. `"SM-001"` |
| `name` | string | Yes | |
| `description` | string | No | |

---

## 5. Quality Goals, Requirements, and Sub-Requirements

### 5.1 Quality Goals

```
GET    /api/v1/projects/{id}/scope/{subchar_id}/goals
POST   /api/v1/projects/{id}/scope/{subchar_id}/goals
PUT    /api/v1/projects/{id}/scope/{subchar_id}/goals/{goal_id}
DELETE /api/v1/projects/{id}/scope/{subchar_id}/goals/{goal_id}
```

**Quality goal fields**

| Field | Type | Required | Notes |
|---|---|---|---|
| `goal_id` | string | Yes | Human-readable, e.g. `"QG-001"` |
| `goal_text` | string | Yes | The goal statement |
| `description` | string | No | |

**GET response 200**

```json
[
  {
    "id": "uuid",
    "goal_id": "QG-001",
    "goal_text": "Perception latency shall not exceed 100ms under normal operation",
    "description": "",
    "requirements": []
  }
]
```

---

### 5.2 Quality Requirements

```
GET    /api/v1/projects/{id}/scope/{subchar_id}/goals/{goal_id}/requirements
POST   /api/v1/projects/{id}/scope/{subchar_id}/goals/{goal_id}/requirements
PUT    /api/v1/projects/{id}/scope/{subchar_id}/goals/{goal_id}/requirements/{req_id}
DELETE /api/v1/projects/{id}/scope/{subchar_id}/goals/{goal_id}/requirements/{req_id}
```

**Quality requirement fields**

| Field | Type | Required | Notes |
|---|---|---|---|
| `req_id` | string | Yes | e.g. `"QR-001"` |
| `requirement_text` | string | Yes | |
| `scenario` | string | No | |
| `applicable_aspects` | array of enum | No | |
| `architecture_element_id` | UUID | No | Links to architecture element |
| `risk_level` | enum | No | Default `"Low"` |
| `evidence_status` | enum | No | Default `"Missing"` |
| `owner` | string | No | |
| `assessment_status` | enum | No | Default `"Draft"` |

**GET response 200**

```json
[
  {
    "id": "uuid",
    "req_id": "QR-001",
    "requirement_text": "Perception pipeline shall process one frame within 100ms at p95",
    "scenario": "Highway driving at 120 km/h",
    "applicable_aspects": ["QM", "FuSA"],
    "architecture_element_id": "uuid",
    "architecture_element_name": "Perception Module",
    "risk_level": "Medium",
    "evidence_status": "Partial",
    "owner": "J. Smith",
    "assessment_status": "Draft",
    "sub_requirements": []
  }
]
```

---

### 5.3 Sub-Quality Requirements

```
GET    /api/v1/projects/{id}/requirements/{req_id}/sub-requirements
POST   /api/v1/projects/{id}/requirements/{req_id}/sub-requirements
PUT    /api/v1/projects/{id}/requirements/{req_id}/sub-requirements/{sub_req_id}
DELETE /api/v1/projects/{id}/requirements/{req_id}/sub-requirements/{sub_req_id}
```

**Sub-requirement fields**

| Field | Type | Required | Notes |
|---|---|---|---|
| `sub_req_id` | string | Yes | e.g. `"SQR-001"` |
| `acceptance_criterion` | string | No | |
| `verification_condition` | string | No | |
| `input_condition` | string | No | |
| `expected_output` | string | No | |
| `measured_value` | string | No | |
| `pass_fail_criterion` | string | No | |
| `architecture_element_id` | UUID | No | Optional trace link |

---

## 6. Test Cases and Test Results

### 6.1 Test Cases

```
GET    /api/v1/projects/{id}/software-modules/{sm_id}/test-cases
POST   /api/v1/projects/{id}/software-modules/{sm_id}/test-cases
PUT    /api/v1/projects/{id}/software-modules/{sm_id}/test-cases/{tc_id}
DELETE /api/v1/projects/{id}/software-modules/{sm_id}/test-cases/{tc_id}
```

**Test case fields**

| Field | Type | Required | Notes |
|---|---|---|---|
| `tc_id` | string | Yes | e.g. `"TC-001"` |
| `description` | string | Yes | |
| `test_objective` | string | No | |
| `test_method` | string | No | |
| `input_data` | string | No | |
| `precondition` | string | No | |
| `expected_result` | string | No | |
| `pass_fail_criterion` | string | No | |
| `evidence_link` | string | No | |
| `automated` | boolean | No | Default `false` |
| `sub_req_id` | UUID | No | Optional explicit trace to sub-requirement |

---

### 6.2 Test Results

Each test case has at most one active result.

```
GET  /api/v1/projects/{id}/test-cases/{tc_id}/result
PUT  /api/v1/projects/{id}/test-cases/{tc_id}/result
```

**PUT request body**

```json
{
  "result": "Pass",
  "actual_result": "P95 latency measured at 87ms",
  "measured_value": "87ms",
  "deviation": null,
  "conclusion": "Requirement met",
  "evidence_file": null,
  "evidence_link": "https://jira.internal/TC-001",
  "executed_at": "2026-06-01T10:30:00Z",
  "tester": "K. Tanaka",
  "notes": null
}
```

**Response 200** — updated test result object

---

## 7. Risk Items

### 7.1 List Project Risks

```
GET /api/v1/projects/{id}/risks
```

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `status` | enum | Filter by risk status |
| `risk_level` | enum | Filter by risk level |
| `aspect` | enum | Filter by quality aspect |

**Response 200**

```json
[
  {
    "id": "uuid",
    "risk_id": "RISK-001",
    "title": "Perception latency under adverse weather",
    "description": "...",
    "quality_aspects": ["FuSA", "SOTIF"],
    "severity": "High",
    "likelihood": "Medium",
    "risk_level": "High",
    "status": "Open",
    "risk_reason": "No test evidence under rain conditions",
    "impact": "May cause delayed braking decision",
    "mitigation_action": "Add wet weather test cases",
    "owner": "J. Smith",
    "due_date": "2026-09-01",
    "target_milestone": "Gate Review 2",
    "related_subchar_id": "perf-eff-time",
    "related_req_id": "uuid",
    "related_test_result_id": null,
    "created_at": "2026-06-01T09:00:00Z",
    "updated_at": "2026-06-01T09:00:00Z"
  }
]
```

---

### 7.2 Create Risk

```
POST /api/v1/projects/{id}/risks
```

**Request body** — all fields from risk object above; `risk_level` is computed by the backend from `severity` × `likelihood` if not provided explicitly.

**Risk level computation rule:**
- Either `severity` or `likelihood` is `Critical` → `risk_level = Critical`
- Both `High` → `risk_level = High`
- Both `Low` → `risk_level = Low`
- All other combinations → `risk_level = Medium`

**Response 201** — created risk object

---

### 7.3 Update Risk

```
PUT /api/v1/projects/{id}/risks/{risk_id}
```

**Response 200** — updated risk object

---

### 7.4 Delete Risk

```
DELETE /api/v1/projects/{id}/risks/{risk_id}
```

**Response 204**

---

## 8. Evidence Items

```
GET    /api/v1/projects/{id}/evidence
POST   /api/v1/projects/{id}/evidence
PUT    /api/v1/projects/{id}/evidence/{evidence_id}
DELETE /api/v1/projects/{id}/evidence/{evidence_id}
```

**Evidence item fields**

| Field | Type | Required | Notes |
|---|---|---|---|
| `evidence_id` | string | Yes | e.g. `"EV-001"` |
| `title` | string | Yes | |
| `description` | string | No | |
| `evidence_type` | string | No | e.g. `"Test Report"`, `"Review Record"`, `"Analysis"` |
| `status` | enum | Yes | `evidence_status` |
| `source_link` | string | No | URL or document reference |
| `related_req_id` | UUID | No | |
| `related_test_result_id` | UUID | No | |

---

## 9. Assessment Findings

```
GET    /api/v1/projects/{id}/findings
POST   /api/v1/projects/{id}/findings
PUT    /api/v1/projects/{id}/findings/{finding_id}
DELETE /api/v1/projects/{id}/findings/{finding_id}
```

**Finding fields**

| Field | Type | Required | Notes |
|---|---|---|---|
| `finding_id` | string | Yes | e.g. `"AF-001"` |
| `title` | string | Yes | |
| `description` | string | Yes | |
| `finding_type` | string | No | e.g. `"Gap"`, `"Non-conformance"`, `"Observation"` |
| `severity` | enum | Yes | `risk_level` |
| `status` | enum | Yes | `finding_status` |
| `related_subchar_id` | string | No | |
| `related_req_id` | UUID | No | |
| `owner` | string | No | |
| `due_date` | date | No | |

---

## 10. Action Items

```
GET    /api/v1/projects/{id}/actions
POST   /api/v1/projects/{id}/actions
PUT    /api/v1/projects/{id}/actions/{action_id}
DELETE /api/v1/projects/{id}/actions/{action_id}
```

**Action item fields**

| Field | Type | Required | Notes |
|---|---|---|---|
| `action_id` | string | Yes | e.g. `"AI-001"` |
| `title` | string | Yes | |
| `description` | string | No | |
| `status` | enum | Yes | `action_status` |
| `priority` | enum | Yes | `risk_level` |
| `owner` | string | No | |
| `due_date` | date | No | |
| `target_milestone` | string | No | |
| `related_finding_id` | UUID | No | |
| `related_risk_id` | UUID | No | |

---

## 11. Project Full Data (Sankey Source)

```
GET /api/v1/projects/{id}/full
```

Returns the complete project data as a flat structure for Sankey graph construction. This endpoint is called once when the user opens a project's Sankey view. All subsequent filtering, highlighting, and node selection operate on the in-memory result — no further requests are made.

**Response 200**

```json
{
  "project":    { "id": "uuid", "project_id": "PRJ-001", "name": "...", "selected_aspects": ["QM", "FuSA"] },
  "scope":      [{ "id": "uuid", "subchar_id": "perf-eff-time", "applicability": "Applicable", "selected_quality_aspects": ["QM", "FuSA"] }],
  "goals":      [{ "id": "uuid", "goal_id": "QG-001", "goal_text": "...", "scope_decision_id": "uuid" }],
  "requirements": [{ "id": "uuid", "req_id": "QR-001", "requirement_text": "...", "goal_id": "uuid", "architecture_element_id": "uuid", "applicable_aspects": ["QM"], "risk_level": "Medium", "evidence_status": "Partial" }],
  "sub_requirements": [{ "id": "uuid", "sub_req_id": "SQR-001", "req_id": "uuid", "architecture_element_id": "uuid" }],
  "architecture_elements": [{ "id": "uuid", "element_id": "AE-001", "name": "Perception Module" }],
  "software_modules": [{ "id": "uuid", "module_id": "SM-001", "name": "cam_pipeline", "architecture_element_id": "uuid" }],
  "test_cases":  [{ "id": "uuid", "tc_id": "TC-001", "description": "...", "software_module_id": "uuid", "sub_req_id": "uuid" }],
  "test_results": [{ "id": "uuid", "tc_id": "uuid", "result": "Pass", "evidence_link": "..." }],
  "risks":       [{ "id": "uuid", "risk_id": "RISK-001", "title": "...", "risk_level": "High", "status": "Open", "related_req_id": "uuid" }]
}
```

All arrays use flat objects with UUID references — no nesting. The frontend `normalize()` function in `state.js` converts each array into a `Map<id, object>` for O(1) lookup before passing to `build()`.

**Response 404** — project not found

---

## 12. Common Model

These endpoints expose the read-only ISO IEC 25010 data. The Common View fetches `GET /common/model` once on page load and caches the result in memory — no JS constants are used in the frontend.

### 11.1 Get Full Common Model

```
GET /api/v1/common/model
```

**Response 200**

```json
{
  "characteristics": [
    {
      "id": "perf-eff",
      "name": "Performance Efficiency",
      "subcharacteristics": [
        {
          "id": "perf-eff-time",
          "name": "Time Behaviour",
          "applicable_aspects": ["QM", "FuSA", "SOTIF"],
          "architecture_element": "System Runtime"
        }
      ]
    }
  ]
}
```

---

### 11.2 Get Product Line Recommendations

```
GET /api/v1/common/product-lines/{product_line}/recommendations
```

Returns the default scope and aspect recommendations for a product line. Used to pre-populate Step 4 of the Create Project wizard.

**Response 200**

```json
[
  {
    "subchar_id": "perf-eff-time",
    "recommended_applicability": "Applicable",
    "recommended_aspects": ["QM", "FuSA"],
    "default_rationale": "Real-time constraints are central to ADAS operation"
  }
]
```

---

## 12. Dashboard

```
GET /api/v1/projects/{id}/dashboard
```

Returns pre-computed dashboard metrics.

**Response 200**

```json
{
  "project_id": "PRJ-001",
  "selected_characteristics_count": 7,
  "selected_subchar_count": 18,
  "excluded_count": 29,
  "open_risk_count": 3,
  "high_risk_count": 1,
  "critical_risk_count": 0,
  "evidence_gap_count": 5,
  "missing_evidence_count": 2,
  "failed_evidence_count": 1,
  "open_finding_count": 2,
  "open_action_count": 4,
  "assessment_readiness": "Conditionally ready",
  "aspect_distribution": {
    "QM":        { "applicable": 8, "partial": 2, "not_applicable": 3 },
    "FuSA":      { "applicable": 6, "partial": 1, "not_applicable": 5 },
    "CS":        { "applicable": 0, "partial": 0, "not_applicable": 12 },
    "SOTIF":     { "applicable": 5, "partial": 2, "not_applicable": 5 },
    "AI Safety": { "applicable": 3, "partial": 1, "not_applicable": 8 }
  }
}
```

**`assessment_readiness` values:** `"Ready"` | `"Conditionally ready"` | `"Not ready"`

---

## 13. Health Check

```
GET /api/v1/health
```

**Response 200**

```json
{
  "status": "ok",
  "version": "6.2.0",
  "db": "connected"
}
```

Used by Docker health check and Nginx upstream probing.

---

## 15. Admin

### 15.1 Seed Demo Data

```
POST /api/v1/admin/seed-demo
```

Populates the database with two sample ADAS projects from `data/13_Sample_Project_Data_ADAS.json`. Intended for first-time setup after deployment. Safe to call multiple times — skipped if projects with the same `project_id` already exist.

**Response 200**

```json
{
  "seeded": 2,
  "skipped": 0,
  "projects": ["PRJ_ADAS_L2_001", "PRJ_ADAS_L3_002"]
}
```

**Usage during deployment:**

```bash
curl -X POST http://localhost:8000/api/v1/admin/seed-demo
# or via Docker Compose:
docker compose exec backend python -m app.services.seed_service
```

---

## 16. Gate Assessment

Gate Assessment endpoints support structured quality gate reviews. Full specification in `20_Gate_Assessment_Design.md` and `21_AI_Agent_Integration_Spec.md`.

### 16.1 Get Gate Definitions

```
GET /api/v1/assessment/gates/{gate_id}/definitions
```

Returns all check item definitions for a gate. Used by the AI Agent to retrieve `pass_criteria` and `required_evidence` before evaluation.

**Valid `gate_id` values:** `QG0`, `QG1`, `QG2`, `QG3`, `QG4`, `QG5`

**Response 200** — array of check item definition objects (see `21_AI_Agent_Integration_Spec.md` §3.1)

---

### 16.2 List Assessment Runs

```
GET /api/v1/projects/{id}/assessment/runs
```

**Query parameters:** `gate_id` (optional filter)

**Response 200** — array of assessment run summaries ordered by `executed_at` descending

---

### 16.3 Get Assessment Run Detail

```
GET /api/v1/projects/{id}/assessment/runs/{run_id}
```

Returns the full run including all 17 check results with `ai_rationale` and `ai_confidence`.

**Response 200** — full run object (see `21_AI_Agent_Integration_Spec.md` §3.4)

---

### 16.4 Submit AI Agent Assessment Run

```
POST /api/v1/projects/{id}/assessment/runs/import
```

Submits a complete gate assessment from the AI Agent. Atomically creates one `assessment_run` and 17 `assessment_check_result` records. Recomputes `assessment_readiness` on the project.

**Request body** — see `21_AI_Agent_Integration_Spec.md` §3.2

**Response 201** — run summary with `overall_result` and updated `assessment_readiness`

---

### 16.5 Create Manual Assessment Run

```
POST /api/v1/projects/{id}/assessment/runs
```

Creates a new manual assessment run in `In Progress` status with all 17 results pre-set to `Open`.

**Request body**

```json
{
  "gate_id": "QG2",
  "executed_by": "J. Smith",
  "notes": "Manual gate review — sprint review 2026-06-01"
}
```

**Response 201** — run object

---

### 16.6 Update Single Check Result

```
PATCH /api/v1/projects/{id}/assessment/runs/{run_id}/results/{result_id}
```

Updates a single check item result (human override or manual entry).

**Request body**

```json
{
  "result": "Pass",
  "findings": "Verified in HIL test session 2026-05-30",
  "evidence_ref": "HIL_Report_20260530.pdf",
  "reviewed_by": "J. Smith"
}
```

**Response 200** — updated result object

---

### 16.7 Complete Assessment Run

```
POST /api/v1/projects/{id}/assessment/runs/{run_id}/complete
```

Marks a run as `Completed`, computes `overall_result` from check results, and updates project `assessment_readiness`. Previous runs for the same gate are not affected (history preserved).

**Response 200**

```json
{
  "run_id": "uuid",
  "overall_result": "Conditional",
  "p0_fail_count": 0,
  "p1_fail_count": 1,
  "p2_fail_count": 0,
  "assessment_readiness": "Conditionally ready"
}
```

---

### 16.8 Get Project Assessment Dashboard

```
GET /api/v1/projects/{id}/assessment/dashboard
```

Returns gate status overview for all QG0–QG5 gates — used to render the Gate Assessment Panel in the Project Dashboard.

**Response 200**

```json
{
  "current_gate": "QG2",
  "assessment_readiness": "Conditionally ready",
  "gates": [
    {
      "gate_id": "QG0",
      "gate_name": "Project Scope and Plan",
      "latest_run_number": 1,
      "overall_result": "Pass",
      "p0_fail_count": 0,
      "p1_fail_count": 0,
      "p2_fail_count": 0,
      "executed_at": "2026-04-01T09:00:00Z"
    },
    {
      "gate_id": "QG1",
      "gate_name": "Requirement Feasibility",
      "latest_run_number": 2,
      "overall_result": "Conditional",
      "p0_fail_count": 0,
      "p1_fail_count": 1,
      "p2_fail_count": 0,
      "executed_at": "2026-05-01T09:00:00Z"
    },
    {
      "gate_id": "QG2",
      "gate_name": "Implementation Completed",
      "latest_run_number": null,
      "overall_result": null,
      "executed_at": null
    }
  ]
}
```
