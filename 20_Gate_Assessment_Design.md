# 20 — Gate Assessment Design

## 1. Overview

The Gate Assessment feature extends PQRETS with a structured quality gate review lifecycle. Each project progresses through six quality gates (QG0–QG5). At each gate, a set of 17 quality check items — mapped directly to ISO 25010 subcharacteristics — must be reviewed and judged Pass/Fail.

Gate Assessment results feed directly into the Project Dashboard:
- The **Gate Assessment Panel** shows pass/fail status per gate and per blocking level.
- The **Assessment Readiness** card is automatically computed from the latest assessment of the project's current gate.

The checklist source is `PA33_Product_Assessment_Lifecycle_Checklist_Combined_UL_Texus_v0_1.xlsx`, sheet `03_QG_Check_Matrix`.

---

## 2. Quality Gate Lifecycle

| Gate | Name | Lifecycle Phase | Expected Maturity |
|---|---|---|---|
| QG0 | Project Scope and Plan | Scope and Plan | Scope planned |
| QG1 | Requirement Feasibility | Requirement Definition | Requirement defined |
| QG2 | Implementation Completed | Architecture; Implementation and Test | Implemented |
| QG3 | Software Integrated | Integration and Verification | Integrated |
| QG4 | Ready for Release | Verification and Validation; Release | Release ready |
| QG5 | Project Close | Production and Operation | Closed |

Each project has a **current gate** field that determines which gate's latest assessment is used for Readiness calculation.

---

## 3. Checklist Structure

The checklist matrix defines **102 check items** = 6 gates × 17 subcharacteristics. Each check item has:

| Field | Description |
|---|---|
| `quality_gate` | QG0–QG5 |
| `quality_characteristic` | ISO 25010 characteristic name |
| `quality_subcharacteristic` | ISO 25010 subcharacteristic name |
| `what_to_check` | Description of what to inspect at this gate |
| `pass_criteria` | Explicit pass/fail condition |
| `required_evidence` | Semicolon-separated list of evidence artifacts |
| `review_method` | How the check is conducted (Review, Analysis, Test, etc.) |
| `blocking_level` | P0 (release blocker), P1 (major), P2 (minor) |
| `responsible_role` | Who performs the check |

The 17 subcharacteristics covered:

| Characteristic | Subcharacteristics |
|---|---|
| Safety | Operational constraint, Risk identification, Fail safe, Hazard warning, Safe integration |
| Functional Suitability | Functional completeness, Functional correctness, Functional appropriateness |
| Performance Efficiency | Time behaviour, Resource utilization, Capacity |
| Reliability | Faultlessness, Availability, Fault tolerance, Recoverability |
| Security | Integrity |
| Maintainability | Testability |

---

## 4. Data Model

### 4.1 `assessment_gate_definitions`

Read-only table seeded from the checklist Excel. One row per check item (102 rows total).

```sql
CREATE TABLE assessment_gate_definitions (
    id              VARCHAR(36)  PRIMARY KEY,
    gate_id         VARCHAR(8)   NOT NULL,        -- QG0, QG1, ... QG5
    gate_name       VARCHAR(128) NOT NULL,
    lifecycle_phase VARCHAR(128) NOT NULL,
    expected_maturity VARCHAR(128) NOT NULL,
    characteristic  VARCHAR(128) NOT NULL,         -- ISO 25010 characteristic name
    subcharacteristic VARCHAR(128) NOT NULL,        -- ISO 25010 subcharacteristic name
    subchar_id      VARCHAR(64)  REFERENCES common_subcharacteristics(id),  -- linked if matched
    what_to_check   TEXT         NOT NULL,
    pass_criteria   TEXT         NOT NULL,
    required_evidence TEXT,
    review_method   VARCHAR(256),
    blocking_level  VARCHAR(4)   NOT NULL,         -- P0, P1, P2
    responsible_role VARCHAR(128),
    display_order   INTEGER      NOT NULL DEFAULT 0
);

CREATE INDEX idx_agd_gate ON assessment_gate_definitions(gate_id);
CREATE INDEX idx_agd_subchar ON assessment_gate_definitions(subcharacteristic);
```

### 4.2 `assessment_runs`

One row per gate assessment execution. A project can have multiple runs per gate (history preserved).

```sql
CREATE TABLE assessment_runs (
    id              VARCHAR(36)  PRIMARY KEY,
    project_id      VARCHAR(36)  NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    gate_id         VARCHAR(8)   NOT NULL,          -- QG0–QG5
    gate_name       VARCHAR(128) NOT NULL,
    run_number      INTEGER      NOT NULL,           -- 1, 2, 3... per gate per project
    status          VARCHAR(32)  NOT NULL DEFAULT 'In Progress',  -- In Progress, Completed, Superseded
    source          VARCHAR(32)  NOT NULL DEFAULT 'manual',       -- manual, ai_agent
    ai_agent_version VARCHAR(64),                    -- version of AI agent if source=ai_agent
    overall_result  VARCHAR(32),                     -- Pass, Fail, Conditional — computed
    p0_fail_count   INTEGER      NOT NULL DEFAULT 0,
    p1_fail_count   INTEGER      NOT NULL DEFAULT 0,
    p2_fail_count   INTEGER      NOT NULL DEFAULT 0,
    executed_by     VARCHAR(128),
    executed_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    notes           TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (project_id, gate_id, run_number)
);

CREATE INDEX idx_ar_project_gate ON assessment_runs(project_id, gate_id);
```

### 4.3 `assessment_check_results`

One row per check item result within an assessment run.

```sql
CREATE TABLE assessment_check_results (
    id              VARCHAR(36)  PRIMARY KEY,
    run_id          VARCHAR(36)  NOT NULL REFERENCES assessment_runs(id) ON DELETE CASCADE,
    definition_id   VARCHAR(36)  NOT NULL REFERENCES assessment_gate_definitions(id),
    result          VARCHAR(32)  NOT NULL DEFAULT 'Open',  -- Open, Pass, Fail, Waived, Not Applicable
    findings        TEXT,                            -- free-text finding or closure action
    evidence_ref    TEXT,                            -- link or reference to evidence artifact
    ai_confidence   FLOAT,                           -- 0.0–1.0, populated by AI agent
    ai_rationale    TEXT,                            -- AI agent reasoning text
    reviewed_by     VARCHAR(128),
    reviewed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (run_id, definition_id)
);

CREATE INDEX idx_acr_run ON assessment_check_results(run_id);
CREATE INDEX idx_acr_result ON assessment_check_results(run_id, result);
```

### 4.4 `projects` table update

Add `current_gate` field to the existing `projects` table:

```sql
ALTER TABLE projects ADD COLUMN current_gate VARCHAR(8) DEFAULT 'QG0';
```

---

## 5. Assessment Readiness Calculation

The `assessment_readiness` field on the Project Dashboard is computed as follows:

1. Find the project's `current_gate` (e.g., `QG2`)
2. Find the latest `assessment_runs` record for that gate with `status = 'Completed'`
3. Apply the rule:

| Condition | Readiness |
|---|---|
| No completed assessment run for current gate | `Not ready` |
| Any `result = 'Fail'` where `blocking_level = 'P0'` | `Not ready` |
| Any `result = 'Fail'` where `blocking_level = 'P1'` | `Conditionally ready` |
| Only `result = 'Fail'` where `blocking_level = 'P2'`, or all Pass/Waived | `Ready` |

---

## 6. Gate Assessment Panel (Dashboard)

The Project Detail Dashboard gains a new **Gate Assessment** section showing:

### 6.1 Gate Status Overview

A row per gate (QG0–QG5):

| Gate | Name | Latest Run | Overall | P0 Fail | P1 Fail | P2 Fail | Date |
|---|---|---|---|---|---|---|---|
| QG0 | Project Scope and Plan | Run 1 | Pass | 0 | 0 | 0 | 2026-05-01 |
| QG1 | Requirement Feasibility | Run 2 | Conditional | 0 | 1 | 0 | 2026-05-15 |
| QG2 | Implementation Completed | — | Not run | — | — | — | — |

Clicking a gate row expands to show all 17 check item results for the latest run.

### 6.2 Check Item Detail (expanded view)

| # | Subcharacteristic | Blocking | Result | Findings | Evidence |
|---|---|---|---|---|---|
| 1 | Operational constraint | P0 | Pass | — | Safety Analysis v2.1 |
| 2 | Risk identification | P0 | Pass | — | HARA Rev C |
| 3 | Fail safe | P0 | Fail | Transition time exceeds HARA | HIL test report pending |

### 6.3 Assessment History

Each gate can show previous runs (Run 1, Run 2...) to visualise improvement over time.

---

## 7. Mapping: Gate Definitions to ISO 25010 Subcharacteristics

The `subchar_id` field in `assessment_gate_definitions` links each checklist item to the corresponding `common_subcharacteristics` record. This enables:

- Filtering the Project Sankey by gate result (e.g., show only subcharacteristics with P0 Fail in QG2)
- Updating the subcharacteristic's `evidence_status` and `risk_level` based on the latest gate assessment result
- Highlighting failing subcharacteristics in the Sankey with a distinct colour

### Mapping Rule

At seed time, match `subcharacteristic` text (case-insensitive) against `common_subcharacteristics.name`. Store the matched `id` in `assessment_gate_definitions.subchar_id`. Unmatched items have `subchar_id = NULL`.

---

## 8. Seeding Gate Definitions

Gate definitions are seeded from the checklist Excel at startup via `seed_service.py`. The seed is idempotent — if `assessment_gate_definitions` already has rows, the seed is skipped.

```python
async def seed_gate_definitions(session: AsyncSession) -> bool:
    """Seed gate check definitions from checklist Excel. Returns True if seeded."""
    ...
```

The Excel file path: `data/PA33_Product_Assessment_Lifecycle_Checklist_Combined_UL_Texus_v0_1.xlsx`

---

## 9. Out of Scope for This Version

- Approval workflow (assessment sign-off by manager)
- Automated email notifications on gate fail
- Cross-project gate comparison
- Custom checklist items beyond the standard 17 subcharacteristics
