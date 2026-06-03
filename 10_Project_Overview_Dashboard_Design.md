# 10 Project Overview Dashboard Design

## 1. Purpose

The Project Overview Dashboard is shown after a user clicks a project card or list item.

Project View itself shows the project cards or list.

Project Detail shows the dashboard.

This document defines the project detail entry dashboard. The full audit/report dashboard for management risk review is defined in `22_Audit_Report_And_Lifecycle_Maturity_Design.md`.

The project detail entry dashboard shall link to the Audit Report Dashboard, but it shall not duplicate the full audit report model.

## 2. Project View

The Project View shall show:

- Project overview header
- Plus button
- Project cards or list items

## 3. Project Card

Each project card shall show:

- Project name
- Product line
- Project phase
- System boundary summary
- Selected quality subcharacteristic count
- Open risk count
- Evidence gap count
- Assessment readiness

Clicking the card opens project detail.

## 4. Project Detail Dashboard

Project detail shall first show dashboard information.

Dashboard cards:

- Selected Characteristics
- Selected Subcharacteristics
- Excluded Items
- Open Risks
- Evidence Gaps
- Assessment Readiness
- Recommended Attention Level
- Product Risk
- Process Maturity Risk
- Gate Progression Signal
- Risk Confidence

## 5. Quality Aspect Distribution

The dashboard shall show distribution by:

- QM
- FuSA
- CS
- SOTIF
- AI Safety

## 6. Risk and Evidence Summary

The dashboard shall show:

- Open risk count
- High risk count
- Evidence gap count
- Missing evidence count
- Failed evidence count
- Assessment readiness
- Current Gate blocking gaps
- Official assessment coverage
- Trace coverage
- Evidence coverage
- Risk Confidence reason breakdown when Low or Unknown

The risk signals shall use the definitions from `22_Audit_Report_And_Lifecycle_Maturity_Design.md`:

| Signal | Values |
| --- | --- |
| Recommended Attention Level | Normal, Watch, At Risk, Critical, Escalation Needed |
| Product Risk | Low, Medium, High, Critical, Unknown |
| Process Maturity Risk | Low, Medium, High, Critical, Unknown |
| Gate Progression Signal | Ready, Conditional, Blocked, Unknown |
| Risk Confidence | High, Medium, Low, Unknown |

The dashboard is a risk display and attention mechanism. It shall not store management final decisions, approval workflow status, or decision records.

## 7. Dashboard Actions

Project detail shall provide:

- Back to Project List
- Edit Quality Scope
- Open Sankey Trace
- Open Audit Report Dashboard

## 8. Relationship to Trace View

The dashboard is the first project detail view.

Project Sankey Trace View is opened only when the user clicks Open Sankey Trace.

## 9. Acceptance Criteria

1. Project View shows project cards or list.
2. Plus button creates new project.
3. Project card opens project detail.
4. Project detail shows dashboard first.
5. Dashboard shows quality scope, risk, evidence, readiness, and executive risk signals.
6. Dashboard allows editing quality scope.
7. Dashboard allows opening Project Sankey Trace View.
8. Dashboard allows opening the Audit Report Dashboard defined in `22_Audit_Report_And_Lifecycle_Maturity_Design.md`.
9. Dashboard does not maintain approval decisions or management decision records.
