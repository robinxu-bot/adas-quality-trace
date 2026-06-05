# 23 Assessment Dashboard Implementation Tasks

## 1. Purpose

This document breaks `22_Audit_Report_And_Lifecycle_Maturity_Design.md` into implementation-ready vertical slices.

The slices are written as issue drafts. They are not yet published to an issue tracker.

Design source:

- `22_Audit_Report_And_Lifecycle_Maturity_Design.md`
- `16_REST_API_Specification.md` section 12.1
- `11_Implementation_Plan.md` Slice 8

Scope boundary:

```text
Assessment Dashboard = risk display and attention mechanism
Not in scope = approval workflow, management final decision, decision record persistence
```

---

## 2. Proposed Vertical Slices

### Slice 1 - Assessment Dashboard Route and Snapshot Shell

Type: AFK

Blocked by: None

User stories covered:

- Management can open a project-level Assessment Dashboard.
- Project detail can navigate to the Assessment Dashboard.
- The system clearly separates dashboard risk display from approval workflow.

What to build:

Create the first end-to-end Assessment Dashboard path:

```text
Project Detail
-> Open Assessment Dashboard
-> GET /api/v1/projects/{id}/assessment-dashboard
-> AuditReportView renders Assessment Snapshot shell
```

The first implementation may return empty arrays for `quality_gate_maturity`, `project_risk_posture`, and `lifecycle_process_maturity`, but it must return a real project identity, snapshot time, current gate, and placeholder-safe executive risk signals.

Acceptance criteria:

- [ ] `GET /api/v1/projects/{id}/assessment-dashboard` exists.
- [ ] `GET /api/v1/projects/{id}/audit-report/dashboard` may remain as a backward-compatible alias, but it is not the preferred public path.
- [ ] The response contains `project_id`, `snapshot_at`, `current_gate`, and `audit_snapshot`.
- [ ] Frontend has an Assessment Dashboard view reachable from Project Detail.
- [ ] The view renders the six fixed sections: Assessment Snapshot, Quality Gate Maturity, Project Risk Posture, Quality Sub-Characteristic Maturity, Lifecycle Activity Maturity, Team Activity & Work Product Matrix.
- [ ] The dashboard UI does not show or store approval decisions, management final decisions, or decision records.

---

### Slice 2 - Executive Risk Signals from Existing Project Data

Type: AFK

Blocked by: Slice 1

User stories covered:

- Management can see the project's current attention level.
- Management can distinguish product risk, process risk, gate progression, and confidence.

What to build:

Compute the five executive risk signals using currently available project data:

```text
Recommended Attention Level
Product Risk
Process Maturity Risk
Gate Progression Signal
Risk Confidence
```

At this stage, `Process Maturity Risk` may be `Unknown` until Activity x Gate data exists.

Acceptance criteria:

- [ ] Assessment Snapshot returns all five executive risk signals.
- [ ] `Recommended Attention Level` uses Normal, Watch, At Risk, Critical, or Escalation Needed.
- [ ] `Product Risk` uses Low, Medium, High, Critical, or Unknown.
- [ ] `Process Maturity Risk` uses Low, Medium, High, Critical, or Unknown.
- [ ] `Gate Progression Signal` uses Ready, Conditional, Blocked, or Unknown.
- [ ] `Risk Confidence` uses High, Medium, Low, or Unknown.
- [ ] Frontend renders the five signals as first-screen cards.
- [ ] Tests cover at least Normal, At Risk, Critical, and Unknown cases.

---

### Slice 3 - Risk Confidence Metrics and Reason Breakdown

Type: AFK

Blocked by: Slice 2

User stories covered:

- Management can see whether the dashboard's risk judgement is trustworthy.
- Project teams can understand why confidence is Low or Unknown.

What to build:

Compute and display Risk Confidence reason breakdown:

```text
Evidence coverage
Trace coverage
Assessment coverage
Review freshness
Critical unknown item count
Primary reason
```

Baseline thresholds:

```text
Evidence coverage >= 70%
Trace coverage >= 70%
Assessment coverage >= 80%
```

Acceptance criteria:

- [ ] API returns a structured `risk_confidence` object with `level`, coverage metrics, `critical_unknown_count`, and `primary_reason`.
- [ ] Risk Confidence Low or Unknown always includes reason breakdown.
- [ ] Frontend shows the breakdown when Risk Confidence is Low or Unknown.
- [ ] Low Product Risk with Low Risk Confidence cannot produce Normal Recommended Attention Level.
- [ ] Tests cover Low due to evidence coverage, Low due to trace coverage, Low due to official coverage, and Unknown due to missing data.

---

### Slice 4 - Lifecycle Activity Library and Project Applicability Tailoring

Type: HITL

Blocked by: None

User stories covered:

- The audit model includes QM, FuSA, CS, SOTIF, and AI Safety lifecycle activities.
- SOTIF and AI Safety remain separate frameworks but can be linked.
- Project teams can tailor activity applicability.

What to build:

Create the built-in lifecycle activity library and project applicability model:

```text
QM Lifecycle
FuSA Lifecycle / ISO 26262
CS Lifecycle / ISO/SAE 21434
SOTIF Lifecycle / ISO 21448
AI Safety Lifecycle / ISO/PAS 8800
```

This slice is HITL because the activity list and evidence expectations require domain review before becoming seed data.

Acceptance criteria:

- [ ] Lifecycle activity definitions exist for all five frameworks.
- [ ] SOTIF and AI Safety are stored as separate frameworks.
- [ ] Each activity can be marked Applicable, Partially applicable, Not applicable, Deferred, Covered by platform, Covered by supplier, or Out of project scope.
- [ ] Non-Applicable states require rationale.
- [ ] Project applicability tailoring can be retrieved and updated through the API.
- [ ] Domain reviewer approves the initial activity library before merge.

---

### Slice 5 - Activity x Gate Definitions and Results

Type: AFK

Blocked by: Slice 4

User stories covered:

- The system can assess lifecycle maturity at Activity x Gate level.
- The same activity can have different expected maturity at QG0-QG5.
- Each result stores both maturity and judgement.

What to build:

Implement Activity x Gate definitions and results:

```text
LifecycleActivityDefinition
GateLifecycleCheckDefinition
ActivityGateResult
```

The result stores:

```text
maturity_state
judgement
source
assessment_result_status
assessment_result_owner
assessment_result_date
evidence_ids
risk_ids
trace_node_ids
```

Acceptance criteria:

- [ ] Activity x Gate definition data can be listed by project and gate.
- [ ] Activity Gate Results can be created or updated manually.
- [ ] Activity Gate Results store one formal result used by the report.
- [ ] Maturity state uses N/A, 0, 1, 2, 3, 4.
- [ ] Judgement uses Pass, Fail, Waived, Not Assessed, Not Applicable.
- [ ] Evidence cap rules prevent maturity_state from exceeding the allowed maximum.
- [ ] Tests cover maturity_state and judgement being different, for example Evidence complete plus Fail.

---

### Slice 6 - Integrated Maturity Score Calculation

Type: AFK

Blocked by: Slice 5

User stories covered:

- Management can see one formal integrated maturity score and understand how missing formal assessment results reduce score and coverage.
- Applicable items without a formal assessment result reduce integrated score and assessment coverage.

What to build:

Compute:

```text
Integrated score
Assessment coverage
Lifecycle activity scores
P0 caps
```

The report exposes one formal integrated score. Applicable items without a formal assessment result count as 0 and are reflected in assessment coverage.

Acceptance criteria:

- [ ] Applicable items without a formal assessment result count as 0 in the integrated score.
- [ ] Assessment coverage is returned separately from the integrated score.
- [ ] P0 caps apply to lifecycle activity scores.
- [ ] Report response returns one integrated score.
- [ ] Tests cover missing formal result items and P0 cap behavior.

---

### Slice 7 - Quality Gate Maturity View

Type: AFK

Blocked by: Slice 6

User stories covered:

- Management can see maturity across QG0-QG5.
- Users can compare QM, FuSA, CS, SOTIF, and AI Safety by gate.

What to build:

Render the Quality Gate Maturity section:

```text
Gate -> Quality Aspect -> Quality Characteristic/Subcharacteristic
```

Start with a gate x aspect matrix, then add drill-down into characteristics/subcharacteristics where data exists.

Acceptance criteria:

- [ ] API returns `quality_gate_maturity` data grouped by gate and quality aspect.
- [ ] Frontend renders a QG0-QG5 x QM/FuSA/CS/SOTIF/AI Safety matrix.
- [ ] Cells show score band and blocker indicator.
- [ ] Selecting a low maturity cell opens a detail panel.
- [ ] The view does not present scores as formal ASPICE capability levels.

---

### Slice 8 - Lifecycle and Process Maturity View

Type: AFK

Blocked by: Slice 6

User stories covered:

- Auditors can see process maturity across lifecycle frameworks.
- Management can see which framework causes process maturity risk.

What to build:

Render Lifecycle Activity Maturity:

```text
Framework -> Lifecycle Phase -> Activity -> Gate progression
```

Use ASPICE-like maturity bars as a visual style only. Do not call the result ASPICE capability level.

Acceptance criteria:

- [ ] API returns `lifecycle_process_maturity` grouped by framework, phase, activity, and gate.
- [ ] Frontend renders framework maturity bars for QM, FuSA, CS, SOTIF, and AI Safety.
- [ ] SOTIF and AI Safety appear as separate framework rows.
- [ ] Each framework row shows score, band, main blocker, and P0 warning when applicable.
- [ ] Clicking a framework or activity opens Activity x Gate detail.

---

### Slice 9 - Quality Sub-Characteristic Maturity View

Type: AFK

Blocked by: Slice 5, Slice 6, Slice 7

User stories covered:

- Quality engineers can understand whether an ISO 25010 sub-characteristic is actually realised across QM, FuSA, CS, SOTIF, and AI Safety.
- Management can see which quality sub-characteristics are weak and which quality aspect causes the weakness.

What to build:

Render Quality Sub-Characteristic Maturity:

```text
Quality Sub-Characteristic
-> Quality Aspect
-> Activity x Gate
```

The table should group rows by Characteristic first, then show related Sub-Characteristics together.

Acceptance criteria:

- [ ] API returns `quality_subcharacteristic_maturity` grouped by quality characteristic and sub-characteristic.
- [ ] Frontend renders Characteristic group rows with Sub-Characteristic detail rows below.
- [ ] Each sub-characteristic row shows overall maturity, aspect realisation, mapped aspects with mapping rationale, weakest aspect, evidence coverage, blockers, and main weakness.
- [ ] Mapping rationale comes from the ADAS quality aspect mapping, for example `mappingReason` in `07_ADAS_Quality_Aspect_Mapping.json`.
- [ ] A project scope selection is not shown as the technical rationale; if rationale is missing, the UI exposes the missing common mapping definition.
- [ ] Scores are shown as percentages with `%`.
- [ ] Low maturity rows can drill down to Activity x Gate, evidence, risk, and trace context when available.

---

### Slice 10 - Team Activity & Work Product Matrix

Type: AFK

Blocked by: Slice 5, Slice 8

User stories covered:

- Management can see which teams own or contribute to each required activity.
- Project managers can identify missing accountable teams, missing work products, and team-level blockers.
- Assessors can explain Risk Confidence gaps using concrete team/activity/work product facts.

What to build:

Render Team Activity & Work Product Matrix:

```text
Rows = QM / FuSA / CS / SOTIF / AI Safety activities
Columns = configurable ADAS teams
Cells = role + maturity + work product status + evidence status + blocking risks
```

Default team columns:

```text
PdM/PgM/PjM AD/ADAS
360 deg Perception AD/ADAS Safety
Map (Vehicle) CA & AD/ADAS Non-Safety
LaneLevelLocalization AD/ADAS Non-Safety
MotionPlanner AD/ADAS Safety-Rule
MotionPlanner AD/ADAS Safety-ML (SWC: DDTP)
InterCommBev (Application Framework)
Controller AD/ADAS Safety
Product Integrity
Product Delivery (Optional)
```

Acceptance criteria:

- [ ] API returns team matrix rows grouped by framework and approved lifecycle activity; rows must not use long gate checklist question text as the primary activity label.
- [ ] Team columns are project-configurable and can be tailored per project.
- [ ] The primary table is visually organised as `Framework / Activity -> Team columns -> Assessment Detail`; team columns must appear immediately after the activity column.
- [ ] Each activity row can show Accountable, Contributing, Reviewer / Approver, and Not applicable cells using `A / C / R / N/A`.
- [ ] Cells are not left blank; non-applicable responsibility is shown as `N/A`.
- [ ] Each cell can show maturity, work product status, evidence status, blocking risk count, and main weakness.
- [ ] Activities without an Accountable team are exposed as assessment coverage gaps or critical unknowns.
- [ ] Missing work products are exposed as evidence coverage gaps.
- [ ] Product Integrity can review or approve, but does not replace the accountable activity owner.
- [ ] Multi-team participation does not duplicate or inflate the overall maturity score.
- [ ] The matrix uses a configured activity-team responsibility model. A default ADAS responsibility model may be seeded, but project teams can tailor, override, or extend it.

---

### Slice 11 - Project Risk Posture View and Current Gate Impact

Type: AFK

Blocked by: Slice 2

User stories covered:

- Management can understand current product risk exposure.
- Project managers can see which risks affect the current gate.

What to build:

Render Project Risk Posture:

```text
All open project risks
Risk severity distribution
Risk by Quality Aspect
Risk by Quality Characteristic/Subcharacteristic
Evidence gaps
Current Gate Impact
```

Acceptance criteria:

- [ ] API returns `project_risk_posture` with open risk summary and current gate impact.
- [ ] Frontend shows all open project risks by default, not only the current gate risks.
- [ ] Current Gate Impact is highlighted separately.
- [ ] Risk distribution by Quality Aspect includes QM, FuSA, CS, SOTIF, and AI Safety.
- [ ] Selecting a risk shows linked evidence gaps and trace context where available.

---

### Slice 12 - Traceability Drill-Down from Report Items

Type: AFK

Blocked by: Slice 5, Slice 7, Slice 8, Slice 9, Slice 10, Slice 11

User stories covered:

- Users can explain why a maturity item or risk is low.
- Users can jump from report findings to evidence, risk, and Sankey trace context.

What to build:

Implement drill-down from low maturity or failed report items to:

```text
Activity and gate
Required evidence
Linked evidence
Missing evidence gaps
Related risks
Related quality aspect and subcharacteristic
Related trace chain nodes
```

Acceptance criteria:

- [ ] Low maturity Activity x Gate items expose evidence, risk, and trace links.
- [ ] Failed judgement items show missing evidence and blocker reason.
- [ ] Report detail panel can open the related project Sankey trace context.
- [ ] If no trace node is linked, the UI clearly shows that trace context is unavailable.
- [ ] Tests cover drill-down for at least one FuSA item, one CS item, one SOTIF item, and one AI Safety item.

---

### Slice 13 - Demo Data and Regression Coverage

Type: AFK

Blocked by: Slice 2, Slice 6, Slice 7, Slice 8, Slice 9, Slice 10, Slice 11

User stories covered:

- Stakeholders can evaluate the dashboard using realistic ADAS demo data.
- Future changes do not silently break scoring or dashboard risk signals.

What to build:

Extend seed/demo data to cover:

```text
Normal
Watch
At Risk
Critical
Escalation Needed
Low Risk Confidence
Unknown Risk Confidence
Ready / Conditional / Blocked / Unknown Gate Progression Signal
```

Acceptance criteria:

- [ ] Demo data includes at least one project with Low Risk Confidence.
- [ ] Demo data includes at least one P0 blocker case.
- [ ] Demo data includes separate SOTIF and AI Safety lifecycle maturity examples.
- [ ] Automated tests cover dashboard signal calculation.
- [ ] Frontend smoke test verifies Assessment Dashboard renders without blank sections.

---

## 3. Dependency Order

Recommended implementation order:

```text
1. Slice 1 - Assessment Dashboard Route and Snapshot Shell
2. Slice 2 - Executive Risk Signals from Existing Project Data
3. Slice 3 - Risk Confidence Metrics and Reason Breakdown
4. Slice 4 - Lifecycle Activity Library and Project Applicability Tailoring
5. Slice 5 - Activity x Gate Definitions and Results
6. Slice 6 - Integrated Maturity Score Calculation
7. Slice 7 - Quality Gate Maturity View
8. Slice 8 - Lifecycle and Process Maturity View
9. Slice 9 - Quality Sub-Characteristic Maturity View
10. Slice 10 - Team Activity & Work Product Matrix
11. Slice 11 - Project Risk Posture View and Current Gate Impact
12. Slice 12 - Traceability Drill-Down from Report Items
13. Slice 13 - Demo Data and Regression Coverage
```

Slice 4 is the only HITL slice in this draft because the lifecycle activity library needs domain approval. All other slices are intended to be AFK once Slice 4 is approved.

---

## 4. Open Review Questions

1. Does the granularity feel right, or should any slice be split further?
2. Is Slice 4 the only slice that should be HITL?
3. Should Project Risk Posture be implemented before Quality Gate Maturity, as proposed here?
4. Should demo data be a final slice, or should each slice add its own demo fixture?
5. Should these drafts be published as GitHub issues after review?
