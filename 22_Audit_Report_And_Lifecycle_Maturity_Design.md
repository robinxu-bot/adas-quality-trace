# 22 Assessment Dashboard and Lifecycle Maturity Design

## 1. Purpose

This document defines the PQRETS Assessment Dashboard model and the lifecycle maturity model used to generate assessment views.

The dashboard is not a single gate run record. It is a project-level assessment snapshot at a specific point in time.

```text
Assessment Dashboard
= Project + snapshot time + current gate + formal assessment results + current risks + lifecycle maturity
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

The dashboard shall have one snapshot section and five fixed analytical views.

```text
0. Assessment Snapshot
1. Quality Gate Maturity
2. Project Risk Posture
3. Quality Sub-Characteristic Maturity
4. Lifecycle Activity Maturity
5. Team Activity & Work Product Matrix
```

`Quality Gate Maturity`, `Quality Sub-Characteristic Maturity`, `Lifecycle Activity Maturity`, and `Team Activity & Work Product Matrix` are not separate scoring systems. They are different aggregation views over the same formal Activity x Gate result base.

```text
Activity x Gate Results
-> Gate / Quality Aspect
   = Quality Gate Maturity

Activity x Gate Results
-> Quality Sub-Characteristic / Quality Aspect
   = Quality Sub-Characteristic Maturity

Activity x Gate Results
-> Framework / Lifecycle Phase / Activity
   = Lifecycle Activity Maturity

Activity x Gate Results
-> Activity / Team / Work Product
   = Team Activity & Work Product Matrix
```

### 2.1 Assessment Snapshot

Assessment Snapshot summarises:

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
- Integrated maturity score
- Open risk summary

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
| Integrated score           | 45% Insufficient                    |
| Assessment coverage        | 60%                                 |
| Current gate impact        | 3 blocking gaps, 5 conditional risks |

The dashboard shows one formal report result. Any preparatory analysis outside the dashboard is not represented as a separate report stream.

### 2.1.1 Executive Dashboard Risk Signals

Assessment Snapshot shall show five executive risk signals:

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
| Current Gate maturity >= 70%, no P0 Fail, Assessment coverage >= 80% | Ready |
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
- Assessment coverage
- Review freshness
- Unknown or unassessed critical item ratio

Thresholds:

| Input                        | Baseline Threshold |
| ---------------------------- | -----------------: |
| Evidence coverage            |              >=70% |
| Trace coverage               |              >=70% |
| Assessment coverage |              >=80% |

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
Primary reason: Assessment coverage below threshold

Breakdown:
- Evidence coverage: 58%
- Trace coverage: 64%
- Assessment coverage: 42%
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

The same underlying Activity x Gate Results can also be grouped by Quality Sub-Characteristic and Quality Aspect for sub-characteristic maturity.

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

### 2.4 Quality Sub-Characteristic Maturity

Quality Sub-Characteristic Maturity is sub-characteristic-centred.

It answers:

```text
How well is a quality sub-characteristic, such as Functional completeness,
realised across applicable QM, FuSA, CS, SOTIF, and AI Safety aspects?
```

It groups the same Activity x Gate result base by:

```text
Quality Sub-Characteristic -> Quality Aspect -> Activity x Gate
```

The example table should make the judgement chain readable: why the sub-characteristic is related to each aspect, where the maturity comes from, and which aspect is weakest.

| Characteristic | Quality Sub-Characteristic | Related Quality Aspects and Technical Rationale | Aspect Realisation | Overall Maturity | Weakest Aspect / Main Weakness |
| --- | --- | --- | --- | ---: | --- |
| Functional suitability | Functional completeness | QM: functions cover project needs and user tasks; FuSA: safety-related functions, safety mechanisms, and degradation functions must be complete; SOTIF: ODD, trigger conditions, and scenario coverage determine intended-function completeness; AI Safety: data lifecycle, model capability boundaries, and runtime constraints must be covered | QM 85% / FuSA 60% / SOTIF 55% / AI Safety 40% | 62% | AI Safety: data lifecycle and model capability boundary evidence incomplete |
| Functional suitability | Functional correctness | QM: outputs meet functional specification; FuSA: incorrect perception, fusion, or control outputs may create safety risk; SOTIF: correctness must cover known trigger scenarios and performance limitations; AI Safety: model output correctness, robustness, and error boundaries require evidence | QM 80% / FuSA 58% / SOTIF 52% / AI Safety 45% | 59% | AI Safety: corner-case and misclassification boundary evidence incomplete |
| Performance efficiency | Time behaviour | QM: response time affects usability; FuSA: warning, braking, or steering latency can affect safety goals; SOTIF: latency may increase trigger-scenario risk; AI Safety: inference latency and degradation strategy affect runtime safety | QM 70% / FuSA 55% / SOTIF 50% / AI Safety 45% | 58% | AI Safety: inference latency and degradation evidence incomplete |
| Safety | Risk identification | FuSA: hazards and safety-goal risks must be identified; SOTIF: intended-function insufficiency, trigger conditions, and scenario risks must be identified; AI Safety: data, model, runtime monitoring, and misuse risks must be identified | FuSA 60% / SOTIF 50% / AI Safety 45% | 52% | SOTIF: trigger scenario risk identification incomplete |
| Safety | Fail safe | FuSA: faults must lead to a safe state or controlled degradation; SOTIF: non-fault functional limitation scenarios must also avoid unsafe behaviour | FuSA 68% / SOTIF 48% | 56% | SOTIF: fail-safe evidence for limitation scenarios incomplete |
| Safety | Hazard warning | FuSA: safety-relevant hazardous states require recognisable warning; SOTIF: ODD boundaries, functional limitations, and misuse risks require warning or driver guidance; QM: warnings must be understandable and consistent with user tasks | QM 76% / FuSA 62% / SOTIF 50% | 60% | SOTIF: ODD boundary warning evidence incomplete |

Rows should be ordered by `Characteristic -> Quality Sub-Characteristic`, so related Safety sub-characteristics such as `Risk identification`, `Fail safe`, and `Hazard warning` are shown together.

This view does not directly score the sub-characteristic itself. It aggregates the related Activity x Gate results, evidence, risks, and trace context that realise the sub-characteristic across applicable quality aspects.

The table shall show `Mapped Aspects & Rationale`, explaining why the sub-characteristic is related to QM, FuSA, CS, SOTIF, or AI Safety. The rationale comes from the ADAS quality aspect mapping, such as `mappingReason` in `07_ADAS_Quality_Aspect_Mapping.json`. A project scope selection only means that the aspect is assessed for this project; it is not a technical rationale. If the common mapping model has no rationale for the sub-characteristic and aspect pair, the UI shall expose that as a model-definition gap instead of presenting the scope selection as the reason.

### 2.5 Lifecycle Activity Maturity

Lifecycle Activity Maturity is lifecycle-activity-centred.

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

### 2.6 Team Activity & Work Product Matrix

Team Activity & Work Product Matrix is the team-oriented breakdown of lifecycle activity maturity. Rows are QM, FuSA, CS, SOTIF, and AI Safety activities; columns are project teams. Each cell shows responsibility, maturity, work product status, evidence status, and blocking risk context.

Default ADAS team columns:

| Team Column | Team / Scope | Safety Classification |
| --- | --- | --- |
| PdM/PgM/PjM AD/ADAS | Product / Program / Project management | Cross-functional AD/ADAS coordination |
| 360 deg Perception AD/ADAS Safety | AD/ADAS perception team | AD/ADAS Safety |
| Map (Vehicle) CA & AD/ADAS Non-Safety | Vehicle map team | CA and AD/ADAS Non-Safety |
| LaneLevelLocalization AD/ADAS Non-Safety | Lane-level localization team | AD/ADAS Non-Safety |
| MotionPlanner AD/ADAS Safety-Rule | Rule-based motion planning team | AD/ADAS Safety |
| MotionPlanner AD/ADAS Safety-ML (SWC: DDTP) | ML-based motion planning team | AD/ADAS Safety-ML |
| InterCommBev (Application Framework) | Application framework / inter-communication team | Application Framework |
| Controller AD/ADAS Safety | AD/ADAS controller team | AD/ADAS Safety |
| Product Integrity | Product integrity / independent quality integrity role | Cross-functional review |
| Product Delivery (Optional) | Product delivery coordination | Optional |

The team list is project-configurable. Projects may tailor, rename, add, or remove team columns.

Cell role values:

| Role | Meaning |
| --- | --- |
| A | Accountable team |
| C | Contributing team |
| R | Reviewer / Approver |
| N/A | Not applicable |

The visual matrix shall prioritise `activity rows x team columns`. Rows are approved lifecycle-family activities, not long gate checklist question text. Supporting fields such as gate, quality context, responsible role, expected maturity, work product, evidence, and judgement should be shown inside the activity cell or a trailing detail column, not between the activity column and the team columns. Cells must not be blank: applicable teams show `A / C / R + maturity + work product status + evidence status`; non-applicable teams show `N/A`.

Example matrix:

| Framework / Activity | PdM/PgM/PjM AD/ADAS | 360 deg Perception AD/ADAS Safety | Map (Vehicle) CA & AD/ADAS Non-Safety | LaneLevelLocalization AD/ADAS Non-Safety | MotionPlanner AD/ADAS Safety-Rule | MotionPlanner AD/ADAS Safety-ML (SWC: DDTP) | InterCommBev (Application Framework) | Controller AD/ADAS Safety | Product Integrity | Product Delivery (Optional) | Assessment Detail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FuSA: HARA | C / 60% | C / 55% | N/A | C / 45% | A / 70% | C / 50% | N/A | C / 62% | R / 65% | N/A | QG1 / HARA report |
| SOTIF: Triggering condition identification | C / 55% | C / 50% | A / 40% | C / 45% | C / 48% | C / 45% | N/A | C / 52% | R / 58% | N/A | QG1 / triggering condition catalogue |
| AI Safety: Data lifecycle planning | C / 42% | C / 45% | C / 50% | A / 38% | C / 40% | N/A | N/A | C / 42% | R / 48% | N/A | QG2 / data lifecycle plan and governance model |
| CS: TARA | N/A | C / 55% | A / 68% | C / 52% | C / 55% | C / 50% | N/A | C / 55% | R / 62% | N/A | QG1 / TARA report |
| QM: Requirement review | A / 75% | A / 70% | A / 70% | A / 68% | A / 72% | A / 69% | A / 70% | A / 72% | R / 80% | C / 65% | QG1 / Functional suitability / requirement review |

Rules:

1. Each applicable activity should have at least one Accountable team.
2. An activity may have multiple Contributing teams.
3. Product Integrity may be Reviewer / Approver, but should not replace the accountable activity owner.
4. Product Delivery (Optional) is optional and should appear only when delivery coordination is in project scope.
5. Multi-team participation must not inflate overall scores; aggregation uses activity and work product weights, not team count.
6. Activities without an Accountable team contribute to critical unknowns or assessment coverage gaps.
7. Missing work products contribute to evidence coverage gaps.
8. Work products that exist but are not reviewed cannot reach `4 Deliverable accepted`.
9. `Responsible Role` from the Excel gate checklist is not the same as concrete development team assignment. The matrix should use a configured activity-team responsibility model. The system may provide a default ADAS responsibility model, but project teams must be able to tailor, override, or extend it.
10. Non-applicable team cells must show `N/A`, not blank cells.

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
| `source`                         | manual, imported, system                         |
| `assessment_result_status`       | Formal result status                             |
| `assessment_result_owner`        | Person or role responsible for the result        |
| `assessment_result_date`         | Result timestamp                                 |
| `evidence_ids`                   | Linked Evidence Items                            |
| `risk_ids`                       | Linked Risk Items                                |
| `trace_node_ids`                 | Optional links into Trace Chain nodes            |

Example ActivityGateResult:

| Field                          | Example Value                                                |
| ------------------------------ | ------------------------------------------------------------ |
| maturity_state                 | 3 Evidence complete                                          |
| judgement                      | Fail                                                         |
| source                         | manual                                                       |
| assessment_result_status       | Formal                                                       |
| assessment_result_owner        | Safety assessor                                              |
| assessment_result_date         | 2026-06-02                                                   |
| evidence_ids                   | HARA-001, SG-001                                             |
| risk_ids                       | R-FUSA-004                                                   |

The evidence package exists, so maturity can reach 3. The deliverable is not accepted, so maturity cannot reach 4. The gate judgement is Fail because a P0 criterion is not satisfied.

### 6.1 Maturity State

Maturity state describes the actual maturity of the activity, evidence, or deliverable. It does not represent a separate AI review state.

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
| Assessment Result Status      | formal report result            | The assessment result is valid for the report                                              |

`Deliverable accepted` means the artifact is accepted. It is not a separate statement about an AI-generated assessment result.

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

| Activity x Gate Item | maturity_state | Numeric State | P0? |
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

## 8. Integrated Score

The report shall compute one formal integrated score.

Rules:

- Applicable Activity x Gate items without a formal assessment result count as 0 Not assessed.
- Not applicable items are excluded.
- Assessment coverage is shown separately.

```text
Assessment coverage
= applicable items with formal assessment result / total applicable items
```

Report display:

```text
Integrated maturity: 62% In progress
Assessment coverage: 68%
```

Example integrated score:

| Item Group                       | Count | Contribution Rule                 | Numerator |
| -------------------------------- | ----: | --------------------------------- | --------: |
| Applicable formal result items   | 6     | Full weight                       | 18.0      |
| Applicable items without result  | 4     | Count as 0 Not assessed           | 0.0       |

Assume 10 applicable equal-weight items:

```text
Maximum numerator = 10 * 4 = 40
Integrated score = 18.0 / 40 = 45%
Assessment coverage = 6 / 10 = 60%
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

Lifecycle activity score:

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
| Linked evidence           | TARA v0.3                                          |
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

1. An Assessment Dashboard can be generated for a project at a snapshot time.
2. The dashboard includes Assessment Snapshot, Quality Gate Maturity, Project Risk Posture, Quality Sub-Characteristic Maturity, Lifecycle Activity Maturity, and Team Activity & Work Product Matrix.
3. Assessment Snapshot shows Recommended Attention Level, Product Risk, Process Maturity Risk, Gate Readiness, and Risk Confidence.
4. The dashboard does not store approval decisions, management final decisions, or decision records.
5. Gate Readiness includes a Gate Progression Signal: Ready, Conditional, Blocked, or Unknown.
6. Risk Confidence uses Evidence coverage, Trace coverage, Assessment coverage, review freshness, and unknown item ratio.
7. Risk Confidence shows reason breakdown when Low or Unknown.
8. Quality Gate Maturity shows QG0-QG5 across QM, FuSA, CS, SOTIF, and AI Safety.
9. Quality Sub-Characteristic Maturity groups by Quality Sub-Characteristic -> Quality Aspect -> Activity x Gate and shows weakest aspect and main weakness.
10. Lifecycle Activity Maturity includes QM, ISO 26262, ISO/SAE 21434, ISO 21448, and ISO/PAS 8800 activity families.
11. Team Activity & Work Product Matrix shows configurable ADAS team columns, activity responsibility, work product status, evidence status, and blocking risk context.
12. SOTIF and AI Safety are separate frameworks.
13. Activity x Gate is the minimum assessment unit.
14. Activity x Gate stores both maturity_state and judgement.
15. The report shows one integrated score based on formal assessment results.
16. Applicable items without a formal assessment result count as 0 and are reflected in coverage.
17. Maturity state names distinguish deliverable/evidence acceptance from assessment-result status.
18. Low maturity report items can drill down to linked evidence, risk, and trace chain context.
