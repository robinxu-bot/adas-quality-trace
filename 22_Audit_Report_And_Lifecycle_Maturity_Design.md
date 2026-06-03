# 22 Audit Report and Lifecycle Maturity Design

## 1. Purpose

This document defines the PQRETS audit report model and the lifecycle maturity model used to generate report views.

The report is not a single gate run record. It is a project-level audit snapshot at a specific point in time.

```text
Audit Report
= Project + snapshot time + current gate + latest reviewed assessment data + current risks + lifecycle maturity
```

The dashboard is a risk display and attention mechanism. It does not maintain approval decisions, management conclusions, or decision records.

The design extends the Gate Assessment model in `20_Gate_Assessment_Design.md` and the AI Agent workflow in `21_AI_Agent_Integration_Spec.md`.

Reference inputs:

- `input/qualityGateDefinition.drawio.png` for QG0-QG5 gate progression and QM/FuSA/CS gate check structure.
- `input/aspice_process_maturity.png` for the visual style of domain maturity bars.
- `image/AGENTS/1780380843105.png` for the ISO/PAS 8800 AI safety lifecycle structure.
- ISO public overview pages:
  - ISO 26262 overview: https://www.iso.org/publication/PUB200262.html
  - ISO/SAE 21434: https://www.iso.org/standard/70918.html
  - ISO/PAS 8800: https://www.iso.org/standard/83303.html

---

## 2. Report Views

The report shall have one snapshot section and three fixed analytical views.

```text
0. Audit Snapshot
1. Quality Gate Maturity
2. Project Risk Posture
3. Lifecycle & Process Maturity
```

### 2.1 Audit Snapshot

Audit Snapshot summarises:

- Project identity
- Product line and quality aspects
- Snapshot date/time
- Current gate
- Overall readiness
- Recommended attention level
- Product risk level
- Process maturity risk level
- Gate readiness and progression signal
- Risk confidence
- Official maturity score
- Draft maturity score
- Open risk summary
- Pending human confirmation count

Example:

| Field                      | Example Value                       |
| -------------------------- | ----------------------------------- |
| Project                    | ADAS L2 Camera Fusion ECU           |
| Product line               | ADAS L2/L2+                         |
| Snapshot time              | 2026-06-02 10:00 JST                |
| Current gate               | QG2 System Architecture Baseline    |
| Enabled quality aspects    | QM, FuSA, CS, SOTIF, AI Safety      |
| Recommended attention      | At Risk                             |
| Product risk               | Medium                              |
| Process maturity risk      | High                                |
| Gate progression signal    | Conditional                         |
| Risk confidence            | Low                                 |
| Official integrated score  | 45% Insufficient                    |
| Draft integrated score     | 69% In progress                     |
| Assessment coverage        | 60%                                 |
| Pending human confirmation | 18 Activity x Gate results          |
| Current gate impact        | 3 blocking gaps, 5 conditional risks |

The project may look better in draft because AI/system results exist, but the official report remains lower until those assessment results are human-confirmed.

### 2.1.1 Executive Dashboard Risk Signals

Audit Snapshot shall show five executive risk signals:

```text
Recommended Attention Level
Product Risk
Process Maturity Risk
Gate Readiness
Risk Confidence
```

These signals are for risk attention and prioritisation. They are not approval decisions.

Dashboard shall not store:

- Management final decision
- Approval workflow status
- Management decision record
- Residual risk acceptance signature

If approval or residual risk acceptance is needed, the dashboard may link to an external workflow or record, but it shall not own that workflow.

### 2.1.2 Recommended Attention Level

Recommended Attention Level is the dashboard-level summary of how much management attention the project currently needs.

| Level             | Meaning                                                                    |
| ----------------- | -------------------------------------------------------------------------- |
| Normal            | No significant risk signal is visible                                      |
| Watch             | Minor risk or coverage weakness exists and should be monitored             |
| At Risk           | Clear risk exists and may affect the current gate or later delivery        |
| Critical          | Serious risk, P0 blocker, or critical unknown exists                       |
| Escalation Needed | Risk, resource, or responsibility issue exceeds the project team's control |

Recommended Attention Level is driven by:

```text
Product Risk
Process Maturity Risk
Gate Readiness
Risk Confidence
```

Example rules:

| Condition                                                        | Recommended Attention Level |
| ---------------------------------------------------------------- | --------------------------- |
| No significant risk, coverage meets thresholds, gate is ready     | Normal                      |
| Minor coverage weakness or medium risk                           | Watch                       |
| Gate readiness is insufficient, or Product Risk is High           | At Risk                     |
| P0 blocker, P0 Fail, or critical unknown exists                  | Critical                    |
| Cross-team resource, responsibility, or authority issue is blocked | Escalation Needed           |

### 2.1.3 Product Risk

Product Risk describes the current product risk exposure. It is independent of whether the process appears mature.

| Level    | Meaning                                           |
| -------- | ------------------------------------------------- |
| Low      | No significant product risk is visible            |
| Medium   | Product risk exists but is controlled or bounded  |
| High     | Product risk may affect gate readiness or release |
| Critical | Product risk is not acceptable without action     |
| Unknown  | Product risk cannot be judged from current data   |

Product Risk shall consider FuSA, CS, SOTIF, AI Safety, QM risks, evidence gaps, failed checks, and unresolved residual risk.

### 2.1.4 Process Maturity Risk

Process Maturity Risk describes the risk caused by immature lifecycle activities, weak evidence, weak reviews, or incomplete process execution.

| Level    | Meaning                                                       |
| -------- | ------------------------------------------------------------- |
| Low      | Lifecycle activities are mature enough for the current gate    |
| Medium   | Some process gaps exist but are controlled                     |
| High     | Process gaps may make risk conclusions unreliable             |
| Critical | P0 process blocker or critical lifecycle activity failure      |
| Unknown  | Process maturity cannot be judged from current assessment data |

Product Risk and Process Maturity Risk must be shown separately. A low product risk with weak process maturity may still mean the risk judgement is not trustworthy.

### 2.1.5 Gate Readiness and Gate Progression Signal

Gate Readiness describes whether the current gate has enough official maturity, evidence, and P0 status to support progression.

Gate Readiness shall include:

- Current Gate Official maturity score
- Current Gate P0 status
- Current Gate blocking gaps
- Gate Progression Signal

Gate Progression Signal keeps the Go/No-Go meaning without becoming an approval decision.

| Signal      | Meaning                                                              |
| ----------- | -------------------------------------------------------------------- |
| Ready       | Current gate appears ready to progress                               |
| Conditional | Progression may be possible, but conditions or coverage gaps remain  |
| Blocked     | Current gate is blocked by P0 Fail, critical risk, or evidence gap   |
| Unknown     | Data is insufficient to judge gate progression                       |

Example rules:

| Condition                                                                    | Gate Progression Signal |
| ---------------------------------------------------------------------------- | ----------------------- |
| Current Gate Official maturity >= 70%, no P0 Fail, Official coverage >= 80%  | Ready                   |
| Current gate is close to thresholds, or conditional risks remain             | Conditional             |
| P0 Fail, critical evidence gap, or current gate maturity far below threshold | Blocked                 |
| Required assessment data is missing                                          | Unknown                 |

### 2.1.6 Risk Confidence

Risk Confidence describes how trustworthy the dashboard's risk judgement is.

It is not the same as Product Risk or Process Maturity Risk.

```text
Product Risk = how risky the product appears
Process Maturity Risk = how risky the process maturity appears
Risk Confidence = how trustworthy those judgements are
```

Risk Confidence shall be calculated from:

- Evidence coverage
- Trace coverage
- Official assessment coverage
- Review freshness
- Unknown or unassessed critical item ratio

Thresholds:

| Input                        | Baseline Threshold |
| ---------------------------- | -----------------: |
| Evidence coverage            |              >=70% |
| Trace coverage               |              >=70% |
| Official assessment coverage |              >=80% |

Risk Confidence levels:

| Level   | Meaning                                                                           |
| ------- | --------------------------------------------------------------------------------- |
| High    | Evidence, trace, and official coverage are strong; no critical unknown exists     |
| Medium  | Baseline thresholds are met; remaining unknowns are controlled                    |
| Low     | One or more baseline thresholds are missed, or critical unknowns exist            |
| Unknown | There is not enough data to judge the trustworthiness of the risk result          |

Risk Confidence shall affect Recommended Attention Level:

| Risk Confidence | Effect on Recommended Attention Level                                  |
| --------------- | ---------------------------------------------------------------------- |
| High            | Can support Normal or Watch if other risks are low                     |
| Medium          | Can support Watch or At Risk depending on other risks                  |
| Low             | Cannot support Normal when Product Risk appears Low                    |
| Unknown         | Shall raise attention to At Risk or Critical depending on missing data |

When Risk Confidence is Low or Unknown, the dashboard must show reason breakdown.

Example:

```text
Risk Confidence: Low
Primary reason: Official assessment coverage below threshold

Breakdown:
- Evidence coverage: 58%
- Trace coverage: 64%
- Official assessment coverage: 42%
- Review freshness: 71%
- Critical unknown items: 7
```

### 2.2 Quality Gate Maturity

Quality Gate Maturity is gate-centred.

It answers:

```text
How mature is this project across QG0-QG5, by quality aspect and quality attribute?
```

It groups Activity Gate Results by:

```text
Gate -> Quality Aspect -> Quality Characteristic/Subcharacteristic
```

The view shall cover all five Quality Aspects:

```text
QM
FuSA
CS
SOTIF
AI Safety
```

Example:

| Gate | QM  | FuSA | CS  | SOTIF | AI Safety |
| ---- | --: | ---: | --: | ----: | --------: |
| QG0  | 85% | 75%  | 70% | 60%   | 55%       |
| QG1  | 78% | 50%  | 62% | 58%   | 46%       |
| QG2  | 72% | 50%  | 55% | 52%   | 44%       |

The same underlying Activity x Gate Results can also be grouped by Quality Characteristic/Subcharacteristic for detailed quality attribute maturity.

### 2.3 Project Risk Posture

Project Risk Posture is project-risk-centred.

It answers:

```text
What is the current risk condition of this project at the snapshot time?
```

It shall show:

- Overall open risk count
- Risk severity distribution
- Risk distribution by Quality Aspect
- Risk distribution by Quality Characteristic/Subcharacteristic
- Evidence gaps
- Action item status
- Current Gate Impact, including risks and evidence gaps that block or conditionally affect the current gate

The default scope is all open project risks. The current gate impact is highlighted separately.

Example:

| Risk View             | Example Value                       |
| --------------------- | ----------------------------------- |
| Open risks            | 18                                  |
| High risks            | 5                                   |
| Current gate blockers | 3                                   |
| Largest risk aspect   | FuSA                                |
| Largest evidence gap  | Safety analysis and SOTIF scenarios |

### 2.4 Lifecycle & Process Maturity

Lifecycle & Process Maturity is framework/activity-centred.

It answers:

```text
How mature are the project's lifecycle activities across QM, FuSA, CS, SOTIF, and AI Safety?
```

It groups Activity Gate Results by:

```text
Framework -> Lifecycle Phase -> Activity -> Gate progression
```

The visual style may use ASPICE-like domain maturity bars, but the score shall not be presented as a formal ASPICE capability level.

Example:

| Framework | Score | Main Blocker                     |
| --------- | ----: | -------------------------------- |
| QM        | 78%   | Architecture review not accepted |
| FuSA      | 50%   | P0 FSC below Evidence complete   |
| CS        | 55%   | TARA treatment rationale missing |
| SOTIF     | 52%   | Scenario coverage incomplete     |
| AI Safety | 44%   | AI safety argument not evaluated |

---

## 3. Lifecycle Framework Library

PQRETS shall provide a built-in lifecycle activity library. The library is project-tailored through applicability decisions, similar to Project Quality Scope tailoring.

The five framework groups are fixed:

```text
QM Lifecycle
FuSA Lifecycle / ISO 26262
CS Lifecycle / ISO/SAE 21434
SOTIF Lifecycle / ISO 21448
AI Safety Lifecycle / ISO/PAS 8800
```

SOTIF and AI Safety shall remain separate frameworks. They may have explicit trace links, but they shall not be merged into one framework.

### 3.1 QM Lifecycle Activity Families

QM activities cover general engineering quality management and non-safety-specific delivery maturity.

Recommended activity families:

| Activity Family                          | Typical Evidence                                      |
| ---------------------------------------- | ----------------------------------------------------- |
| Project scope and quality plan           | Scope definition, quality plan, responsibility matrix |
| Schedule, resource, and method alignment | Plan baseline, tool/process list, review records      |
| Requirements baseline                    | SW/system requirements review record                  |
| Architecture baseline                    | System/software architecture review record            |
| Implementation completion                | Implementation completion report, code review record  |
| Integration and qualification test       | Integration test report, qualification test report    |
| Release readiness                        | Release review record, open issue list                |
| Project closure and lessons learned      | LLBP record, documentation cleanup record             |

### 3.2 FuSA Lifecycle / ISO 26262 Activity Families

FuSA activities cover the functional safety lifecycle.

Recommended activity families:

| Activity Family                                 | Typical Evidence                                                   |
| ----------------------------------------------- | ------------------------------------------------------------------ |
| Safety management planning                      | Safety plan, confirmation measure plan                             |
| Item definition                                 | Item definition document                                           |
| HARA                                            | Hazard analysis and risk assessment                                |
| Safety goals and ASIL                           | Safety goal list, ASIL rationale                                   |
| Functional safety concept                       | FSC document                                                       |
| Technical safety concept                        | TSC document                                                       |
| System safety requirements                      | System safety requirement baseline                                 |
| Hardware/software safety requirements           | HW/SW safety requirement baseline                                  |
| Safety analysis                                 | FMEA, FTA, DFA, dependent failure analysis                         |
| Verification and validation                     | Safety verification report, validation report                      |
| Safety case                                     | Safety argument and evidence package                               |
| Production, operation, service, decommissioning | Production control, field monitoring, service/decommissioning plan |

### 3.3 CS Lifecycle / ISO/SAE 21434 Activity Families

CS activities cover cybersecurity engineering across concept, development, production, operation, and decommissioning.

Recommended activity families:

| Activity Family                              | Typical Evidence                                           |
| -------------------------------------------- | ---------------------------------------------------------- |
| Cybersecurity management planning            | CS plan, role assignment                                   |
| Cybersecurity item definition                | CS item definition                                         |
| TARA                                         | Threat analysis and risk assessment                        |
| Cybersecurity goals and claims               | CS goals, claims, rationale                                |
| Cybersecurity concept                        | CS concept                                                 |
| Cybersecurity requirements                   | CS requirement baseline                                    |
| Product development cybersecurity activities | Design controls, implementation evidence                   |
| Cybersecurity verification and validation    | Pen test report, vulnerability test report, review records |
| Production cybersecurity controls            | Production security control evidence                       |
| Operations and monitoring                    | Monitoring plan, vulnerability monitoring records          |
| Incident response and remediation            | Incident response plan, remediation records                |
| Decommissioning                              | Decommissioning security plan                              |
| Cybersecurity case                           | CS case or assurance argument                              |

### 3.4 SOTIF Lifecycle / ISO 21448 Activity Families

SOTIF activities shall be explicitly included.

Recommended activity families:

| Activity Family                                  | Typical Evidence                              |
| ------------------------------------------------ | --------------------------------------------- |
| Intended functionality definition                | Function definition, assumptions              |
| ODD and use-case definition                      | ODD document, use-case list                   |
| Hazard identification for intended functionality | SOTIF hazard analysis                         |
| Triggering condition analysis                    | Triggering condition catalogue                |
| Known unsafe scenario analysis                   | Known scenario analysis                       |
| Unknown unsafe scenario discovery                | Exploration strategy, field data analysis     |
| Scenario coverage                                | Scenario catalogue, coverage report           |
| Verification and validation                      | Simulation, proving ground, road test reports |
| Residual risk evaluation                         | Residual risk rationale                       |
| Field monitoring and update loop                 | Monitoring plan, update records               |
| SOTIF argument and evidence                      | SOTIF assurance argument                      |

### 3.5 AI Safety Lifecycle / ISO/PAS 8800 Activity Families

AI Safety activities shall follow the ISO/PAS 8800 lifecycle concept shown in `image/AGENTS/1780380843105.png`.

Recommended activity families:

| Activity Family                            | Typical Evidence                                     |
| ------------------------------------------ | ---------------------------------------------------- |
| AI safety requirements allocation          | AI safety requirements allocated to AI system        |
| AI system definition                       | AI element/system definition                         |
| Data requirements                          | Data requirements, data acceptance criteria          |
| Dataset definition                         | Dataset specification                                |
| Data collection                            | Collection plan, source record                       |
| Data labelling and annotation              | Labelling guideline, annotation quality record       |
| Data quality and completeness              | Data quality report, completeness analysis           |
| Training/validation/test split control     | Split strategy, leakage check                        |
| Model training evidence                    | Training configuration and result record             |
| Model verification                         | Model verification report                            |
| Model validation                           | Model validation report                              |
| ODD and scenario coverage for AI behaviour | Scenario coverage report                             |
| Robustness and generalisation evidence     | Robustness tests, stress tests                       |
| AI safety argument                         | AI safety argument package                           |
| Evaluation of safety argument              | Safety argument evaluation record                    |
| Operation and monitoring                   | Runtime monitoring and assurance maintenance records |

AI Safety may depend on SOTIF outputs such as ODD, triggering conditions, scenario coverage, and residual risk. The dependency shall be traceable but the frameworks remain separate.

Example AI Safety activity with SOTIF link:

| Field              | Example Value                                      |
| ------------------ | -------------------------------------------------- |
| Framework          | AI Safety Lifecycle / ISO/PAS 8800                 |
| Lifecycle activity | Evaluation of safety argument                      |
| Gate               | QG4 Validation Complete                            |
| Expected maturity  | 4 Deliverable accepted                             |
| Required evidence  | AI safety argument, model validation report, scenario coverage report, runtime monitoring plan |
| Dependency link    | SOTIF ODD definition, SOTIF scenario coverage, SOTIF residual risk evaluation |

The link supports drill-down from AI Safety to SOTIF evidence, but it does not merge the two framework scores.

---

## 4. Project Lifecycle Scope

The built-in lifecycle activity library shall be tailored per project.

Each Activity Definition receives a project applicability state:

```text
Applicable
Partially applicable
Not applicable
Deferred
Covered by platform
Covered by supplier
Out of project scope
```

Applicability rationale is mandatory when the state is not `Applicable`.

Only applicable, partially applicable, and deferred activities are included in the default maturity calculation. Excluded activities remain reviewable in the tailoring UI.

---

## 5. Assessment Unit: Activity x Gate

The minimum assessment unit is:

```text
Lifecycle Activity x Quality Gate
```

This is required because the expected maturity of the same activity changes across QG0-QG5.

Example:

| Activity | QG0     | QG1                   | QG2                         | QG3                  | QG4                     | QG5                      |
| -------- | ------- | --------------------- | --------------------------- | -------------------- | ----------------------- | ------------------------ |
| HARA     | Planned | Initial HARA complete | Updated after design change | Assumptions verified | Accepted in safety case | Lessons learned captured |

### 5.1 Definition Object

`LifecycleActivityDefinition`:

| Field                          | Meaning                                                  |
| ------------------------------ | -------------------------------------------------------- |
| `id`                         | Stable UUID                                              |
| `framework`                  | QM, FuSA, CS, SOTIF, AI Safety                           |
| `standard_context`           | ISO 26262, ISO/SAE 21434, ISO 21448, ISO/PAS 8800, or QM |
| `lifecycle_phase`            | Concept, development, V&V, operation, closure, etc.      |
| `activity_name`              | Canonical activity name                                  |
| `description`                | Short explanation                                        |
| `typical_evidence`           | Expected evidence artifacts                              |
| `related_quality_aspects`    | Usually one, but may include dependencies                |
| `related_subcharacteristics` | Optional ISO 25010 links                                 |

`GateLifecycleCheckDefinition`:

| Field                 | Meaning                                  |
| --------------------- | ---------------------------------------- |
| `id`                | Stable UUID                              |
| `gate_id`           | QG0-QG5                                  |
| `activity_id`       | LifecycleActivityDefinition reference    |
| `expected_maturity` | Expected activity state at this gate     |
| `pass_criteria`     | Gate judgement criteria                  |
| `required_evidence` | Evidence needed for assessment           |
| `blocking_level`    | P0, P1, P2                               |
| `weight`            | Relative contribution to framework score |

Example GateLifecycleCheckDefinition:

| Field             | Example Value                                 |
| ----------------- | --------------------------------------------- |
| Framework         | FuSA Lifecycle / ISO 26262                    |
| Lifecycle activity | HARA                                         |
| Gate              | QG1 Concept Baseline                          |
| Expected maturity | 3 Evidence complete                           |
| Required evidence | HARA report, safety goal list, ASIL rationale |
| Blocking level    | P0                                            |
| Weight            | 2                                             |

---

## 6. Activity Gate Result

Each applicable Activity x Gate result stores both maturity and judgement.

| Field                              | Meaning                                          |
| ---------------------------------- | ------------------------------------------------ |
| `maturity_state`                 | Activity/evidence/deliverable maturity           |
| `judgement`                      | Gate judgement: Pass, Fail, Waived, Not Assessed |
| `source`                         | manual, ai_agent, imported                       |
| `ai_maturity_state`              | AI-proposed maturity state                       |
| `ai_judgement`                   | AI-proposed judgement                            |
| `ai_confidence`                  | AI confidence 0.0-1.0                            |
| `ai_rationale`                   | AI reasoning                                     |
| `human_confirmed_maturity_state` | Human-confirmed assessment result                |
| `human_confirmed_judgement`      | Human-confirmed gate judgement                   |
| `assessment_reviewed_by`         | Person confirming the assessment result          |
| `assessment_reviewed_at`         | Confirmation timestamp                           |
| `evidence_ids`                   | Linked Evidence Items                            |
| `risk_ids`                       | Linked Risk Items                                |
| `trace_node_ids`                 | Optional links into Trace Chain nodes            |

Example ActivityGateResult:

| Field                          | Example Value                                                |
| ------------------------------ | ------------------------------------------------------------ |
| maturity_state                 | 3 Evidence complete                                          |
| judgement                      | Fail                                                         |
| source                         | ai_agent                                                     |
| ai_maturity_state              | 3 Evidence complete                                          |
| ai_judgement                   | Fail                                                         |
| ai_confidence                  | 0.91                                                         |
| ai_rationale                   | HARA exists, but severity/exposure/controllability rationale is incomplete |
| human_confirmed_maturity_state | 3 Evidence complete                                          |
| human_confirmed_judgement      | Fail                                                         |
| evidence_ids                   | HARA-001, SG-001                                             |
| risk_ids                       | R-FUSA-004                                                   |

The evidence package exists, so maturity can reach 3. The deliverable is not accepted, so maturity cannot reach 4. The gate judgement is Fail because a P0 criterion is not satisfied.

### 6.1 Maturity State

Maturity state describes the actual maturity of the activity, evidence, or deliverable. It does not describe whether the AI result has been reviewed.

| State | Name                 | Meaning                                                                                  |
| ----- | -------------------- | ---------------------------------------------------------------------------------------- |
| N/A   | Not applicable       | Activity does not apply to this project                                                  |
| 0     | Not assessed         | No assessment basis yet                                                                  |
| 1     | Insufficient         | Evidence is absent or clearly insufficient                                               |
| 2     | In progress          | Activity is underway; evidence is partial                                                |
| 3     | Evidence complete    | Required evidence package is complete enough for assessment                              |
| 4     | Deliverable accepted | Required deliverable/evidence passed its required technical/process review or acceptance |

### 6.2 Judgement

Judgement answers whether the Activity x Gate item satisfies the gate criteria.

```text
Pass
Fail
Waived
Not Assessed
Not Applicable
```

Maturity state and judgement are related but not identical.

Example:

```text
Activity: HARA
Gate: QG1
maturity_state: 3 Evidence complete
judgement: Fail
reason: HARA exists but rating rationale is incomplete
```

### 6.3 Review Terminology

Two review concepts must not be confused:

| Review Type                   | Affects                         | Meaning                                                                                    |
| ----------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------ |
| Deliverable / Evidence Review | `maturity_state`              | The artifact itself has been technically reviewed, process-reviewed, approved, or accepted |
| Assessment Result Review      | official/draft reporting status | A human confirms or overrides an AI/system judgement about the maturity state              |

`Deliverable accepted` means the artifact is accepted. It does not mean the AI assessment result was accepted.

---

## 7. Maturity Caps

The maturity state is capped by evidence condition.

| Condition                         | Maximum maturity_state |
| --------------------------------- | ---------------------- |
| No linked evidence                | 2 In progress          |
| Evidence exists but is incomplete | 2 In progress          |
| Evidence package complete         | 3 Evidence complete    |
| Evidence/deliverable accepted     | 4 Deliverable accepted |

For applicable P0 checks:

| Condition                                 | Framework maturity cap     |
| ----------------------------------------- | -------------------------- |
| Any P0 judgement = Fail                   | Framework maturity max = 2 |
| Any P0 maturity_state < 3                 | Framework maturity max = 2 |
| Any P0 maturity_state = 3                 | Framework maturity max = 3 |
| All P0 maturity_state >= 4 and no P0 Fail | Framework may reach 4      |

Overall integrated maturity shall show the P0 blocking warning. The overall score may be optionally capped by product-line policy.

Example P0 cap:

| Activity x Gate Item | Human-confirmed maturity_state | Numeric State | P0? |
| -------------------- | ------------------------------ | ------------: | --- |
| Item definition QG2  | 4 Deliverable accepted         | 4             | Yes |
| HARA QG2             | 3 Evidence complete            | 3             | Yes |
| FSC QG2              | 2 In progress                  | 2             | Yes |
| Safety analysis QG2  | 0 Not assessed                 | 0             | No  |

```text
Raw score = (4 + 3 + 2 + 0) / (4 items * max state 4) = 56.25%
FSC QG2 is P0 and maturity_state = 2.
Framework maturity max = 2 / 4 = 50%.
Final FuSA QG2 score = min(56.25%, 50%) = 50% In progress.
```

---

## 8. Official and Draft Scores

The report shall compute two scores.

### 8.1 Official Score

Official score uses human-confirmed assessment results only.

Rules:

- Applicable Activity x Gate items without human-confirmed result count as 0 Not assessed.
- Not applicable items are excluded.
- Assessment coverage is shown separately.

```text
Official coverage
= human-confirmed applicable items / total applicable items
```

### 8.2 Draft Score

Draft score uses:

- Human-confirmed results, full weight
- AI-proposed results not yet human-confirmed, confidence weighted

AI confidence weighting:

| AI confidence | Draft weight                 |
| ------------- | ---------------------------- |
| >= 0.80       | Full weight                  |
| 0.60-0.79     | Half weight                  |
| < 0.60        | Treated as 0 for draft score |

Report display:

```text
Official maturity: 62% In progress
Draft maturity: 78% Review-ready
Pending human confirmation: 12 items
Assessment coverage: 68%
```

`Review-ready` may be used as a display band, but the underlying maturity state name is `Evidence complete`.

Example official vs draft score:

| Item Group                       | Count | Contribution Rule                 | Numerator |
| -------------------------------- | ----: | --------------------------------- | --------: |
| Human-confirmed applicable items | 6     | Full weight                       | 18.0      |
| AI confidence >= 0.80            | 2     | Full draft weight, states 4 and 4 | 8.0       |
| AI confidence 0.60-0.79          | 1     | Half draft weight, state 3        | 1.5       |
| AI confidence < 0.60             | 1     | Treated as 0                      | 0.0       |

Assume 10 applicable equal-weight items:

```text
Maximum numerator = 10 * 4 = 40
Official score = 18.0 / 40 = 45%
Official coverage = 6 / 10 = 60%
Draft score = (18.0 + 8.0 + 1.5) / 40 = 68.75%
```

---

## 9. Score Display

Internal calculation uses maturity state 0-4.

The report displays maturity as percentage plus band.

| Percentage | Band                    |
| ---------- | ----------------------- |
| 0-24%      | Not assessed / no basis |
| 25-49%     | Insufficient            |
| 50-69%     | In progress             |
| 70-89%     | Evidence complete       |
| 90-100%    | Deliverable accepted    |

Framework score:

```text
weighted average of applicable Activity x Gate maturity states within the framework
then apply P0 gating cap
then convert 0-4 to percentage
```

Integrated score:

```text
weighted average of framework scores
```

Default framework weights:

| Framework | Default Weight |
| --------- | -------------: |
| QM        |            20% |
| FuSA      |            25% |
| CS        |            20% |
| SOTIF     |            15% |
| AI Safety |            20% |

Weights may be adjusted by product line. ADAS and AI-heavy ADAS projects may assign higher weight to FuSA, SOTIF, and AI Safety.

---

## 10. Traceability Links

Activity x Gate Results must be traceable to project evidence and risk.

Required or recommended links:

| Link                       | Requirement                                             |
| -------------------------- | ------------------------------------------------------- |
| Evidence Item              | Required for maturity_state 3 or 4                      |
| Risk Item                  | Recommended when judgement is Fail or Conditional       |
| Quality Subcharacteristic  | Recommended for maturity reporting by quality attribute |
| Quality Goal / Requirement | Recommended for detailed traceability                   |
| Test Result                | Recommended when verification evidence is test-based    |
| Sankey Trace Node          | Optional but useful for drill-down                      |

If no Evidence Item is linked, maturity_state shall not exceed 2.

Report drill-down from any low maturity or failed item shall show:

- Activity and gate
- Required evidence
- Linked evidence
- Missing evidence gaps
- Related risks
- Related quality aspect and subcharacteristic
- Related trace chain nodes when available

Example low-maturity drill-down:

| Field                     | Example Value                                      |
| ------------------------- | -------------------------------------------------- |
| Framework                 | CS Lifecycle / ISO/SAE 21434                       |
| Activity                  | TARA                                               |
| Gate                      | QG1 Concept Baseline                               |
| maturity_state            | 2 In progress                                      |
| judgement                 | Fail                                               |
| Required evidence         | TARA report, threat scenarios, treatment rationale |
| Linked evidence           | TARA draft v0.3                                    |
| Missing evidence gap      | Treatment option rationale missing                 |
| Related risk              | R-CS-003 High                                      |
| Related quality aspect    | CS                                                 |
| Related subcharacteristic | Integrity                                          |
| Related trace chain node  | Cybersecurity requirement CSR-017                  |

---

## 11. Relationship to Existing Gate Assessment

The current Gate Assessment model in `20_Gate_Assessment_Design.md` is a gate checklist model.

This document generalises that model:

```text
assessment_gate_definitions
-> GateLifecycleCheckDefinition

assessment_check_results
-> ActivityGateResult
```

V6.2 may keep the current gate tables as the first implementation slice. Later versions should migrate toward Activity x Gate definitions so QM, FuSA, CS, SOTIF, and AI Safety lifecycle activities are all represented.

---

## 12. Acceptance Criteria

This feature is accepted when:

1. An audit report can be generated for a project at a snapshot time.
2. The report includes Audit Snapshot, Quality Gate Maturity, Project Risk Posture, and Lifecycle & Process Maturity.
3. Audit Snapshot shows Recommended Attention Level, Product Risk, Process Maturity Risk, Gate Readiness, and Risk Confidence.
4. The dashboard does not store approval decisions, management final decisions, or decision records.
5. Gate Readiness includes a Gate Progression Signal: Ready, Conditional, Blocked, or Unknown.
6. Risk Confidence uses Evidence coverage, Trace coverage, Official assessment coverage, review freshness, and unknown item ratio.
7. Risk Confidence shows reason breakdown when Low or Unknown.
8. Quality Gate Maturity shows QG0-QG5 across QM, FuSA, CS, SOTIF, and AI Safety.
9. Lifecycle & Process Maturity includes QM, ISO 26262, ISO/SAE 21434, ISO 21448, and ISO/PAS 8800 activity families.
10. SOTIF and AI Safety are separate frameworks.
11. Activity x Gate is the minimum assessment unit.
12. Activity x Gate stores both maturity_state and judgement.
13. Official score uses only human-confirmed assessment results.
14. Draft score uses human-confirmed plus confidence-weighted AI-proposed results.
15. Applicable but unconfirmed items count as 0 in the Official score and are reflected in coverage.
16. Maturity state names distinguish deliverable/evidence acceptance from assessment-result confirmation.
17. Low maturity report items can drill down to linked evidence, risk, and trace chain context.
