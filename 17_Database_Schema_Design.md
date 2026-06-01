# 17 — Database Schema Design

## 1. Overview

The database schema is a direct relational mapping of the logical data model defined in `04_Data_Model_Design.md`. PostgreSQL 15+ is the target. All tables use UUID primary keys. Timestamps are stored as `TIMESTAMPTZ` (UTC).

The ISO IEC 25010 common model (characteristics, subcharacteristics, aspect mappings, product line rules) is seeded from the `data/` reference JSON files and is read-only at runtime.

---

## 2. Schema Diagram

```
common_characteristics
    │ 1
    │ ∞
common_subcharacteristics ──── common_aspect_mappings
    │
    │ (referenced by scope decisions)
    ▼
project_scope_decisions ◄──── projects
    │                              │
    ▼                              ├── architecture_elements
quality_goals                      │       │
    │                              │       ▼
    ▼                              │   software_modules
quality_requirements ──────────────┤       │
    │           │                  │       ▼
    ▼           └──────────────────┼── test_cases ──► test_results
sub_quality_requirements           │
    │                              ├── risk_items
    └──► architecture_elements     ├── evidence_items
                                   ├── assessment_findings
product_line_recommendations       └── action_items
```

---

## 3. Shared Enum Types

```sql
CREATE TYPE quality_aspect AS ENUM ('QM', 'FuSA', 'CS', 'SOTIF', 'AI Safety');

CREATE TYPE product_line AS ENUM ('AreneTools', 'ADAS', 'WovenCity', 'CloudAI');

CREATE TYPE applicability_value AS ENUM (
    'Applicable',
    'Partially applicable',
    'Not applicable',
    'Deferred',
    'Covered by platform',
    'Covered by supplier',
    'Out of project scope'
);

CREATE TYPE project_phase AS ENUM ('Concept', 'Development', 'Validation', 'Production');

-- Used for risk severity, likelihood, and risk level
CREATE TYPE risk_level AS ENUM ('Critical', 'High', 'Medium', 'Low');

CREATE TYPE risk_item_status AS ENUM ('Open', 'Mitigated', 'Accepted', 'Closed');

CREATE TYPE test_result_value AS ENUM ('Pass', 'Fail', 'Blocked', 'Not run');

CREATE TYPE review_status AS ENUM ('Draft', 'Reviewed', 'Approved');

CREATE TYPE evidence_status AS ENUM ('Complete', 'Partial', 'Missing', 'Failed');

CREATE TYPE finding_status AS ENUM ('Open', 'In Progress', 'Resolved', 'Closed');

CREATE TYPE action_status AS ENUM ('Open', 'In Progress', 'Closed');
```

---

## 4. Common Model Tables (Read-Only After Seed)

### 4.1 `common_characteristics`

```sql
CREATE TABLE common_characteristics (
    id              VARCHAR(64)  PRIMARY KEY,   -- e.g. "perf-eff"
    name            VARCHAR(128) NOT NULL,
    description     TEXT,
    display_order   INTEGER      NOT NULL DEFAULT 0
);
```

### 4.2 `common_subcharacteristics`

```sql
CREATE TABLE common_subcharacteristics (
    id                   VARCHAR(64)  PRIMARY KEY,   -- e.g. "perf-eff-time"
    characteristic_id    VARCHAR(64)  NOT NULL REFERENCES common_characteristics(id),
    name                 VARCHAR(128) NOT NULL,
    description          TEXT,
    architecture_element VARCHAR(128),               -- from ARCH mapping
    display_order        INTEGER      NOT NULL DEFAULT 0
);

CREATE INDEX idx_subchar_characteristic ON common_subcharacteristics(characteristic_id);
```

### 4.3 `common_aspect_mappings`

One row per (subcharacteristic, aspect) pair.

```sql
CREATE TABLE common_aspect_mappings (
    subchar_id  VARCHAR(64)   NOT NULL REFERENCES common_subcharacteristics(id),
    aspect      quality_aspect NOT NULL,
    PRIMARY KEY (subchar_id, aspect)
);
```

### 4.4 `product_line_recommendations`

```sql
CREATE TABLE product_line_recommendations (
    id                          UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
    product_line                product_line        NOT NULL,
    subchar_id                  VARCHAR(64)         NOT NULL REFERENCES common_subcharacteristics(id),
    recommended_applicability   applicability_value NOT NULL,
    recommended_aspects         quality_aspect[]    NOT NULL DEFAULT '{}',
    default_rationale           TEXT,
    UNIQUE (product_line, subchar_id)
);

CREATE INDEX idx_plrec_product_line ON product_line_recommendations(product_line);
```

---

## 5. Project Tables

### 5.1 `projects`

```sql
CREATE TABLE projects (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          VARCHAR(64)   NOT NULL UNIQUE,   -- human-readable, e.g. PRJ-001
    name                VARCHAR(256)  NOT NULL,
    product_type        VARCHAR(128)  NOT NULL,
    product_line        product_line  NOT NULL,
    phase               project_phase NOT NULL,
    system_boundary     TEXT          NOT NULL,
    assessment_target   TEXT,
    customer            VARCHAR(256),
    selected_aspects    quality_aspect[] NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX idx_projects_project_id ON projects(project_id);
```

### 5.2 `project_scope_decisions`

One row per (project, subcharacteristic) pair. Holds the tailoring decision and the selected quality aspects for that scope item.

```sql
CREATE TABLE project_scope_decisions (
    id                      UUID                 PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id              UUID                 NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    subchar_id              VARCHAR(64)          NOT NULL REFERENCES common_subcharacteristics(id),
    applicability           applicability_value  NOT NULL,
    rationale               TEXT,
    recommended_applicability applicability_value,          -- from product_line_recommendations
    recommendation_reason   TEXT,
    selected_quality_aspects quality_aspect[]    NOT NULL DEFAULT '{}',
    manual_override         BOOLEAN              NOT NULL DEFAULT FALSE,
    decision_owner          VARCHAR(128),
    decision_date           DATE,
    review_status           review_status        NOT NULL DEFAULT 'Draft',
    updated_at              TIMESTAMPTZ          NOT NULL DEFAULT now(),
    UNIQUE (project_id, subchar_id)
);

CREATE INDEX idx_scope_project ON project_scope_decisions(project_id);
```

---

## 6. Trace Chain Tables

The trace chain follows: **QualityGoal → QualityRequirement → SubQualityRequirement → ArchitectureElement → SoftwareModule → TestCase → TestResult**

### 6.1 `quality_goals`

Quality goals sit between a scope decision (subcharacteristic) and quality requirements.

```sql
CREATE TABLE quality_goals (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_decision_id   UUID        NOT NULL REFERENCES project_scope_decisions(id) ON DELETE CASCADE,
    goal_id             VARCHAR(64) NOT NULL,    -- human-readable, e.g. QG-001
    goal_text           TEXT        NOT NULL,
    description         TEXT,
    display_order       INTEGER     NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (scope_decision_id, goal_id)
);

CREATE INDEX idx_goal_scope ON quality_goals(scope_decision_id);
```

### 6.2 `quality_requirements`

```sql
CREATE TABLE quality_requirements (
    id                      UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id                 UUID              NOT NULL REFERENCES quality_goals(id) ON DELETE CASCADE,
    req_id                  VARCHAR(64)       NOT NULL,    -- e.g. QR-001
    requirement_text        TEXT              NOT NULL,
    scenario                TEXT,
    applicable_aspects      quality_aspect[]  NOT NULL DEFAULT '{}',
    architecture_element_id UUID              REFERENCES architecture_elements(id),
    risk_level              risk_level        NOT NULL DEFAULT 'Low',
    evidence_status         evidence_status   NOT NULL DEFAULT 'Missing',
    owner                   VARCHAR(128),
    assessment_status       review_status     NOT NULL DEFAULT 'Draft',
    display_order           INTEGER           NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ       NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ       NOT NULL DEFAULT now()
);

CREATE INDEX idx_qreq_goal ON quality_requirements(goal_id);
CREATE INDEX idx_qreq_arch ON quality_requirements(architecture_element_id);
```

> **Note:** `architecture_elements` is defined in Section 6.4. Due to the forward reference, apply the FK constraint after both tables are created (or use deferred constraints).

### 6.3 `sub_quality_requirements`

```sql
CREATE TABLE sub_quality_requirements (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    req_id                  UUID        NOT NULL REFERENCES quality_requirements(id) ON DELETE CASCADE,
    sub_req_id              VARCHAR(64) NOT NULL,
    acceptance_criterion    TEXT,
    verification_condition  TEXT,
    input_condition         TEXT,
    expected_output         TEXT,
    measured_value          TEXT,
    pass_fail_criterion     TEXT,
    architecture_element_id UUID        REFERENCES architecture_elements(id),   -- Sankey trace link
    display_order           INTEGER     NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (req_id, sub_req_id)
);

CREATE INDEX idx_subreq_req ON sub_quality_requirements(req_id);
CREATE INDEX idx_subreq_arch ON sub_quality_requirements(architecture_element_id);
```

### 6.4 `architecture_elements`

Project-scoped. Can be referenced by multiple requirements and sub-requirements.

```sql
CREATE TABLE architecture_elements (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID         NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    element_id      VARCHAR(64)  NOT NULL,    -- e.g. AE-001
    name            VARCHAR(256) NOT NULL,
    description     TEXT,
    display_order   INTEGER      NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (project_id, element_id)
);

CREATE INDEX idx_arch_project ON architecture_elements(project_id);
```

### 6.5 `software_modules`

Belong to an architecture element.

```sql
CREATE TABLE software_modules (
    id                      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    architecture_element_id UUID         NOT NULL REFERENCES architecture_elements(id) ON DELETE CASCADE,
    module_id               VARCHAR(64)  NOT NULL,    -- e.g. SM-001
    name                    VARCHAR(256) NOT NULL,
    description             TEXT,
    display_order           INTEGER      NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (architecture_element_id, module_id)
);

CREATE INDEX idx_module_arch ON software_modules(architecture_element_id);
```

### 6.6 `test_cases`

Linked to a software module. Optionally also linked to a sub-requirement for explicit trace path.

```sql
CREATE TABLE test_cases (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    software_module_id  UUID        NOT NULL REFERENCES software_modules(id) ON DELETE CASCADE,
    sub_req_id          UUID        REFERENCES sub_quality_requirements(id),   -- optional explicit trace
    tc_id               VARCHAR(64) NOT NULL,    -- e.g. TC-001
    description         TEXT        NOT NULL,
    test_objective      TEXT,
    test_method         VARCHAR(128),
    input_data          TEXT,
    precondition        TEXT,
    expected_result     TEXT,
    pass_fail_criterion TEXT,
    evidence_link       TEXT,
    automated           BOOLEAN     NOT NULL DEFAULT FALSE,
    display_order       INTEGER     NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tc_module ON test_cases(software_module_id);
CREATE INDEX idx_tc_subreq ON test_cases(sub_req_id);
```

### 6.7 `test_results`

One active result per test case (one-to-one). Stores the latest execution outcome.

```sql
CREATE TABLE test_results (
    id              UUID               PRIMARY KEY DEFAULT gen_random_uuid(),
    tc_id           UUID               NOT NULL UNIQUE REFERENCES test_cases(id) ON DELETE CASCADE,
    result          test_result_value  NOT NULL DEFAULT 'Not run',
    actual_result   TEXT,
    measured_value  TEXT,
    deviation       TEXT,
    conclusion      TEXT,
    evidence_file   TEXT,
    evidence_link   TEXT,
    executed_at     TIMESTAMPTZ,
    tester          VARCHAR(128),
    notes           TEXT,
    created_at      TIMESTAMPTZ        NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ        NOT NULL DEFAULT now()
);
```

---

## 7. Risk, Evidence, Findings, and Actions

### 7.1 `risk_items`

```sql
CREATE TABLE risk_items (
    id                      UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id              UUID             NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    risk_id                 VARCHAR(64)      NOT NULL,    -- e.g. RISK-001
    title                   VARCHAR(256)     NOT NULL,
    description             TEXT             NOT NULL,
    quality_aspects         quality_aspect[] NOT NULL DEFAULT '{}',
    severity                risk_level       NOT NULL,
    likelihood              risk_level       NOT NULL,
    -- risk_level: Critical×any=Critical, High×High=High, Low×Low=Low, otherwise Medium
    risk_level              risk_level       NOT NULL,
    status                  risk_item_status NOT NULL DEFAULT 'Open',
    risk_reason             TEXT,
    impact                  TEXT,
    mitigation_action       TEXT,
    owner                   VARCHAR(128),
    due_date                DATE,
    target_milestone        VARCHAR(128),
    related_subchar_id      VARCHAR(64)      REFERENCES common_subcharacteristics(id),
    related_req_id          UUID             REFERENCES quality_requirements(id),
    related_test_result_id  UUID             REFERENCES test_results(id),
    created_at              TIMESTAMPTZ      NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ      NOT NULL DEFAULT now(),
    UNIQUE (project_id, risk_id)
);

CREATE INDEX idx_risk_project ON risk_items(project_id);
CREATE INDEX idx_risk_status  ON risk_items(project_id, status);
```

### 7.2 `evidence_items`

```sql
CREATE TABLE evidence_items (
    id                   UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id           UUID            NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    evidence_id          VARCHAR(64)     NOT NULL,    -- e.g. EV-001
    title                VARCHAR(256)    NOT NULL,
    description          TEXT,
    evidence_type        VARCHAR(128),               -- e.g. Test Report, Review Record, Analysis
    status               evidence_status NOT NULL DEFAULT 'Missing',
    source_link          TEXT,
    related_req_id       UUID            REFERENCES quality_requirements(id),
    related_test_result_id UUID          REFERENCES test_results(id),
    created_at           TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ     NOT NULL DEFAULT now(),
    UNIQUE (project_id, evidence_id)
);

CREATE INDEX idx_evidence_project ON evidence_items(project_id);
```

### 7.3 `assessment_findings`

```sql
CREATE TABLE assessment_findings (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID            NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    finding_id          VARCHAR(64)     NOT NULL,    -- e.g. AF-001
    title               VARCHAR(256)    NOT NULL,
    description         TEXT            NOT NULL,
    finding_type        VARCHAR(128),               -- e.g. Gap, Non-conformance, Observation
    severity            risk_level      NOT NULL DEFAULT 'Low',
    status              finding_status  NOT NULL DEFAULT 'Open',
    related_subchar_id  VARCHAR(64)     REFERENCES common_subcharacteristics(id),
    related_req_id      UUID            REFERENCES quality_requirements(id),
    owner               VARCHAR(128),
    due_date            DATE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    UNIQUE (project_id, finding_id)
);

CREATE INDEX idx_finding_project ON assessment_findings(project_id);
```

### 7.4 `action_items`

```sql
CREATE TABLE action_items (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID          NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    action_id           VARCHAR(64)   NOT NULL,    -- e.g. AI-001
    title               VARCHAR(256)  NOT NULL,
    description         TEXT,
    status              action_status NOT NULL DEFAULT 'Open',
    priority            risk_level    NOT NULL DEFAULT 'Medium',
    owner               VARCHAR(128),
    due_date            DATE,
    target_milestone    VARCHAR(128),
    related_finding_id  UUID          REFERENCES assessment_findings(id),
    related_risk_id     UUID          REFERENCES risk_items(id),
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ   NOT NULL DEFAULT now(),
    UNIQUE (project_id, action_id)
);

CREATE INDEX idx_action_project ON action_items(project_id);
```

---

## 8. Seed Data

The following tables are populated once at application startup from `data/` JSON files. No runtime writes occur after seeding.

| Table | Source file |
|---|---|
| `common_characteristics` | `05_ISO25010_Common_Model.json` |
| `common_subcharacteristics` | `05_ISO25010_Common_Model.json` |
| `common_aspect_mappings` | `07_ADAS_Quality_Aspect_Mapping.json` |
| `product_line_recommendations` | `06_Product_Line_Recommendation_Rules.json` |

Seeding is idempotent: if rows already exist, seeding is skipped. Implemented in `backend/app/services/seed_service.py`.

---

## 9. Triggers

### `updated_at` auto-update

```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

Apply to every table with an `updated_at` column:

```sql
-- Example pattern — repeat for each table:
CREATE TRIGGER {table}_updated_at
    BEFORE UPDATE ON {table}
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

Tables requiring this trigger: `projects`, `project_scope_decisions`, `quality_goals`, `quality_requirements`, `sub_quality_requirements`, `architecture_elements`, `software_modules`, `test_cases`, `test_results`, `risk_items`, `evidence_items`, `assessment_findings`, `action_items`.

---

## 10. Forward Reference Resolution

`quality_requirements.architecture_element_id` and `sub_quality_requirements.architecture_element_id` reference `architecture_elements`, which is created after them in standard DDL order. Resolve by adding the FK constraint after both tables exist:

```sql
ALTER TABLE quality_requirements
    ADD CONSTRAINT fk_qreq_arch
    FOREIGN KEY (architecture_element_id) REFERENCES architecture_elements(id);

ALTER TABLE sub_quality_requirements
    ADD CONSTRAINT fk_subreq_arch
    FOREIGN KEY (architecture_element_id) REFERENCES architecture_elements(id);
```

In Alembic, handle this by placing the `ALTER TABLE` statements in the same migration after both table `CREATE` statements.

---

## 11. Alembic Migration Strategy

- `0001_initial_schema.py` — creates all tables and enum types
- `0002_seed_common_model.py` — populates seed tables from `data/` JSON
- Subsequent migrations are numbered sequentially; each change gets its own file
- `alembic upgrade head` runs automatically at container startup before FastAPI starts
- No destructive migrations (DROP COLUMN, DROP TABLE) without a paired data migration step

---

## 12. Connection Configuration

| Environment variable | Default | Description |
|---|---|---|
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_DB` | `pqrets` | Database name |
| `POSTGRES_USER` | `pqrets` | Database user |
| `POSTGRES_PASSWORD` | *(required)* | Database password |

Connection URL assembled in `backend/app/config.py`:

```
postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}
```

---

## 13. Dashboard Calculation Queries

Used by `GET /api/v1/projects/{id}/dashboard`:

**Selected subcharacteristics count**
```sql
SELECT COUNT(*) FROM project_scope_decisions
WHERE project_id = :pid
AND applicability IN ('Applicable', 'Partially applicable', 'Deferred');
```

**Open risk count**
```sql
SELECT COUNT(*) FROM risk_items
WHERE project_id = :pid AND status = 'Open';
```

**High and critical risk count**
```sql
SELECT COUNT(*) FROM risk_items
WHERE project_id = :pid AND status = 'Open' AND risk_level IN ('Critical', 'High');
```

**Evidence gap count** (test cases without a passing result)
```sql
SELECT COUNT(*) FROM test_results tr
JOIN test_cases tc ON tr.tc_id = tc.id
JOIN software_modules sm ON tc.software_module_id = sm.id
JOIN architecture_elements ae ON sm.architecture_element_id = ae.id
WHERE ae.project_id = :pid
AND tr.result IN ('Fail', 'Blocked', 'Not run');
```

**Assessment readiness** is computed in Python in `scope_service.py` applying the rules from `04_Data_Model_Design.md` §10:
- `Ready` — no open Critical/High risks and no missing critical evidence
- `Conditionally ready` — some Medium risks or partial evidence
- `Not ready` — any open Critical/High risk or failed key evidence
