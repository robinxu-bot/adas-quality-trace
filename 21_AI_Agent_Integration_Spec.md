# 21 — AI Agent Integration Specification

## 1. Overview

The AI Agent integration allows an external AI system to submit gate assessment results into PQRETS via a REST API. The AI Agent reads project technical documents, test reports, and other evidence artifacts, evaluates them against the checklist `pass_criteria` for a given quality gate, and submits structured results.

PQRETS defines the interface. The AI Agent adapts to it.

---

## 2. Integration Flow

```
Project technical documents
  (requirements specs, test reports, HARA, safety case, etc.)
          ↓
      AI Agent
      - Identifies the target project and gate
      - Retrieves checklist definitions from PQRETS
      - Evaluates each check item against available evidence
      - Produces structured result payload
          ↓
  POST /api/v1/projects/:id/assessment/runs/import
          ↓
      PQRETS
      - Creates an assessment_run record
      - Creates 17 assessment_check_result records
      - Recomputes Assessment Readiness
      - Updates Dashboard
```

---

## 3. API Endpoints

### 3.1 Get Gate Definitions (AI Agent reads this first)

```
GET /api/v1/assessment/gates/{gate_id}/definitions
```

Returns all 17 check item definitions for a gate. The AI Agent uses `what_to_check`, `pass_criteria`, and `required_evidence` to guide its evaluation.

**Path parameters**

| Name | Values |
|---|---|
| `gate_id` | `QG0`, `QG1`, `QG2`, `QG3`, `QG4`, `QG5` |

**Response 200**

```json
[
  {
    "id": "def-uuid",
    "gate_id": "QG2",
    "gate_name": "Implementation Completed",
    "lifecycle_phase": "Architecture; Implementation and Test",
    "characteristic": "Safety",
    "subcharacteristic": "Fail safe",
    "subchar_id": "QSC_Safety_FailSafe",
    "what_to_check": "Verify fail safe behaviour is implemented and tested per HARA",
    "pass_criteria": "Fault injection evidence proves safe state transition within fault reaction time",
    "required_evidence": "Fault Injection Evidence; Safe State Test Report; HARA",
    "review_method": "System Test; Analysis",
    "blocking_level": "P0",
    "responsible_role": "Safety Engineer"
  }
]
```

---

### 3.2 Submit AI Agent Assessment Run

```
POST /api/v1/projects/{project_id}/assessment/runs/import
```

Submits a complete gate assessment run produced by the AI Agent. PQRETS creates the `assessment_run` and all `assessment_check_results` in a single transaction.

**Request body**

```json
{
  "gate_id": "QG2",
  "source": "ai_agent",
  "ai_agent_version": "pqrets-agent-v1.2.0",
  "executed_by": "AI Agent",
  "notes": "Automated assessment based on document set: [HARA Rev C, HIL Test Report 2026-05-20, Safety Case v1.1]",
  "results": [
    {
      "definition_id": "def-uuid-001",
      "result": "Pass",
      "findings": null,
      "evidence_ref": "HIL Test Report 2026-05-20, Section 4.2",
      "ai_confidence": 0.92,
      "ai_rationale": "HIL test report Section 4.2 documents safe state transition at 180ms, within the 200ms HARA requirement. Pass criteria satisfied."
    },
    {
      "definition_id": "def-uuid-002",
      "result": "Fail",
      "findings": "Fail safe transition time measured at 340ms in worst-case scenario, exceeds HARA requirement of 200ms.",
      "evidence_ref": "HIL Test Report 2026-05-20, Section 4.3",
      "ai_confidence": 0.97,
      "ai_rationale": "Section 4.3 clearly states worst-case transition time of 340ms. HARA requires <= 200ms. Fail criteria triggered."
    },
    {
      "definition_id": "def-uuid-003",
      "result": "Not Applicable",
      "findings": "Capacity check not applicable to this system boundary (onboard ECU, no cloud service).",
      "evidence_ref": null,
      "ai_confidence": 0.85,
      "ai_rationale": "System boundary document explicitly excludes cloud/fleet services. Capacity subcharacteristic does not apply."
    }
  ]
}
```

**Request fields**

| Field | Type | Required | Description |
|---|---|---|---|
| `gate_id` | string | Yes | One of QG0–QG5 |
| `source` | string | Yes | Must be `"ai_agent"` for AI-submitted runs |
| `ai_agent_version` | string | Yes | Version identifier of the AI agent |
| `executed_by` | string | No | Display name of the agent or operator |
| `notes` | string | No | Summary of document set used for evaluation |
| `results` | array | Yes | One entry per check item; must cover all 17 definitions for the gate |

**Result object fields**

| Field | Type | Required | Description |
|---|---|---|---|
| `definition_id` | UUID | Yes | ID from `assessment_gate_definitions` |
| `result` | enum | Yes | `Pass`, `Fail`, `Waived`, `Not Applicable`, `Open` |
| `findings` | string | No | Required when `result = Fail`; describes the specific deficiency |
| `evidence_ref` | string | No | Document name, section, or URL that supports the judgment |
| `ai_confidence` | float | No | 0.0–1.0; AI agent's confidence in the result judgment |
| `ai_rationale` | string | No | AI agent's reasoning; shown in UI for human review |

**Response 201**

```json
{
  "run_id": "run-uuid",
  "project_id": "project-uuid",
  "gate_id": "QG2",
  "run_number": 1,
  "overall_result": "Fail",
  "p0_fail_count": 1,
  "p1_fail_count": 0,
  "p2_fail_count": 0,
  "assessment_readiness": "Not ready",
  "executed_at": "2026-06-01T09:00:00Z"
}
```

**Response 422** — missing required fields, unknown `definition_id`, or `results` array does not cover all 17 definitions

---

### 3.3 List Assessment Runs for a Project

```
GET /api/v1/projects/{project_id}/assessment/runs
```

**Query parameters**

| Parameter | Description |
|---|---|
| `gate_id` | Filter by gate (optional) |

**Response 200**

```json
[
  {
    "run_id": "run-uuid",
    "gate_id": "QG2",
    "gate_name": "Implementation Completed",
    "run_number": 2,
    "status": "Completed",
    "source": "ai_agent",
    "overall_result": "Conditional",
    "p0_fail_count": 0,
    "p1_fail_count": 1,
    "p2_fail_count": 0,
    "executed_at": "2026-06-01T09:00:00Z"
  }
]
```

---

### 3.4 Get Assessment Run Detail

```
GET /api/v1/projects/{project_id}/assessment/runs/{run_id}
```

Returns the full run with all 17 check results.

**Response 200**

```json
{
  "run_id": "run-uuid",
  "gate_id": "QG2",
  "run_number": 1,
  "source": "ai_agent",
  "ai_agent_version": "pqrets-agent-v1.2.0",
  "overall_result": "Fail",
  "p0_fail_count": 1,
  "executed_at": "2026-06-01T09:00:00Z",
  "notes": "...",
  "results": [
    {
      "definition_id": "def-uuid",
      "characteristic": "Safety",
      "subcharacteristic": "Fail safe",
      "blocking_level": "P0",
      "result": "Fail",
      "findings": "Transition time 340ms exceeds HARA requirement of 200ms",
      "evidence_ref": "HIL Test Report 2026-05-20, Section 4.3",
      "ai_confidence": 0.97,
      "ai_rationale": "..."
    }
  ]
}
```

---

### 3.5 Update Single Check Result (Human Override)

After an AI Agent run, a human reviewer can override individual results:

```
PATCH /api/v1/projects/{project_id}/assessment/runs/{run_id}/results/{result_id}
```

**Request body**

```json
{
  "result": "Waived",
  "findings": "Waived by Safety Manager — deviation accepted with mitigation action RISK-001",
  "reviewed_by": "J. Smith"
}
```

**Response 200** — updated result object

---

## 4. AI Agent Workflow

The recommended sequence for the AI Agent:

```
1. GET /api/v1/assessment/gates/{gate_id}/definitions
   → Retrieve all 17 check items with pass_criteria and required_evidence

2. Load project technical documents
   (provided externally — not managed by PQRETS in V6.2)

3. For each check item:
   - Locate relevant sections in documents matching required_evidence
   - Evaluate against pass_criteria
   - Assign result: Pass / Fail / Not Applicable
   - Record evidence_ref (document name + section)
   - Record ai_rationale (reasoning text)
   - Record ai_confidence (0.0–1.0)

4. POST /api/v1/projects/{project_id}/assessment/runs/import
   → Submit all 17 results in one call

5. Receive response: overall_result + updated assessment_readiness
```

---

## 5. Confidence Threshold Guidelines

| `ai_confidence` | Recommended handling in UI |
|---|---|
| >= 0.90 | Display result directly; no special warning |
| 0.70–0.89 | Show yellow indicator; recommend human review |
| < 0.70 | Show orange indicator; flag for mandatory human review before gate acceptance |

PQRETS stores `ai_confidence` per result and displays it in the check item detail view.

---

## 6. Result Values

| Value | Meaning |
|---|---|
| `Pass` | Check item satisfied; evidence supports pass criteria |
| `Fail` | Check item not satisfied; findings must be provided |
| `Waived` | Deviation accepted; requires findings explaining rationale |
| `Not Applicable` | Check item does not apply to this project scope |
| `Open` | Not yet evaluated (default for manual runs in progress) |

---

## 7. Overall Result Computation

Computed by PQRETS on the backend when a run is completed:

| Condition | Overall Result |
|---|---|
| Any `Fail` where `blocking_level = P0` | `Fail` |
| Any `Fail` where `blocking_level = P1`, no P0 Fail | `Conditional` |
| Only P2 Fails or all Pass/Waived/Not Applicable | `Pass` |

---

## 8. Error Handling

| HTTP Status | Cause | AI Agent action |
|---|---|---|
| 422 | Missing `definition_id` or unknown gate | Fix payload; retry |
| 422 | Results array incomplete (fewer than 17 items) | Add missing items as `Open` and retry |
| 404 | Project not found | Verify project ID before submission |
| 500 | Server error | Retry after 60 seconds; log error |

---

## 9. Out of Scope for V6.2

- AI Agent authentication (API key / OAuth) — no auth in V6.2
- Streaming partial results during evaluation
- AI Agent pulling documents directly from PQRETS (documents are provided externally)
- Automated re-run scheduling
