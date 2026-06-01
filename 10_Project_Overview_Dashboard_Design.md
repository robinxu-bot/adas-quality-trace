# 10 Project Overview Dashboard Design

# Updated Project Overview Dashboard Design

## 1. Purpose

The Project Overview Dashboard is shown after a user clicks a project card or list item.

Project View itself shows the project cards or list.

Project Detail shows the dashboard.

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

## 7. Dashboard Actions

Project detail shall provide:

- Back to Project List
- Edit Quality Scope
- Open Sankey Trace

## 8. Relationship to Trace View

The dashboard is the first project detail view.

Project Sankey Trace View is opened only when the user clicks Open Sankey Trace.

## 9. Acceptance Criteria

1. Project View shows project cards or list.
2. Plus button creates new project.
3. Project card opens project detail.
4. Project detail shows dashboard first.
5. Dashboard shows quality scope, risk, evidence and readiness.
6. Dashboard allows editing quality scope.
7. Dashboard allows opening Project Sankey Trace View.
