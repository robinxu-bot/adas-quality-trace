# 08 Project Workspace UI Design

# Updated UI Design for V5.8.4

## 1. Purpose

This document defines the updated UI design after the decision to simplify top level navigation and move Create Project and Quality Scope Tailoring into contextual workflows.

## 2. Top Level UI

The system shall have only two top level entries:

```text
Common
Project
```

Create Project shall not be a top level tab.

Quality Scope Tailoring shall not be a top level tab.

## 3. Common View

## 3.1 Purpose

Common View is used to show original common information.

It shall include:

- Full original ISO IEC 25010 Product Quality model
- All quality characteristics
- All quality subcharacteristics
- Common descriptions
- Common product line recommendation context
- Common Sankey Trace Tree

## 3.2 Common View Layout

Recommended layout:

```text
Header
→ Common statistics
→ Quality characteristic selector
→ Subcharacteristic list
→ Common Sankey Trace Tree
```

## 3.3 Common Sankey Trace Tree

Common Sankey Trace Tree shall show:

```text
Product Quality
→ Quality Characteristic
→ Quality Subcharacteristic
→ Quality Goal
→ Quality Requirement
→ Sub Quality Requirement
→ Architecture Element
→ Software Module
→ Test Case
→ Test Result
→ Risk Status
```

This view is not project specific.

## 4. Project View

## 4.1 Purpose

Project View is the entry point for all project based work.

It shall show project cards or project list.

## 4.2 Project View Layout

Recommended layout:

```text
Project Overview Header
→ Plus Button
→ Project Cards or Project List
```

## 4.3 Project Card

Each project card shall show:

- Project name
- Product line
- Project phase
- System boundary
- Selected quality scope count
- Open risk count
- Evidence gap count
- Assessment readiness

Clicking a project card opens project detail.

## 4.4 Plus Button

The plus button shall be placed in the Project Overview header.

Clicking plus opens Create Project.

## 5. Create Project Workflow

Create Project shall be an intermediate workflow.

It appears only after clicking plus.

Recommended display mode:

- Modal
- Drawer
- Wizard page inside Project View

Recommended steps:

```text
Step 1 Project Basic Information
Step 2 Product Line Selection
Step 3 Quality Aspect Context
Step 4 Quality Scope Tailoring
Step 5 Confirmation
```

## 6. Quality Scope Tailoring

Quality Scope Tailoring appears in two contexts only:

1. During Create Project
2. When editing the quality scope of an existing project

It may also be opened after selecting a specific quality attribute and choosing edit.

It shall not be displayed as a permanent top level view.

## 7. Project Detail View

Clicking a project card opens project detail.

Project detail shall first show dashboard.

Recommended layout:

```text
Project Header
→ Back to Project List
→ Edit Quality Scope
→ Open Sankey Trace
→ Dashboard Cards
→ Quality Aspect Distribution
→ Open Risk and Evidence Summary
```

## 8. Project Sankey Trace View

Project Sankey Trace View is opened from project detail.

It shall show only the tailored project quality scope by default.

It shall include:

- Sankey trace graph
- Trace filters
- Node detail panel
- Structured trace chain table

## 9. Interaction Summary

```text
Common tab
→ view common model and common trace tree

Project tab
→ view project cards
→ click plus
→ create project
→ tailor quality scope
→ save project
→ project card appears

Project card
→ open project detail
→ view dashboard
→ edit quality scope
→ open project Sankey trace view
```

## 10. Acceptance Criteria

1. Top level navigation has only Common and Project.
2. Common shows full model and common Sankey trace tree.
3. Project shows cards or list.
4. Plus opens Create Project.
5. Create Project includes Quality Scope Tailoring.
6. Project detail opens after clicking a project card.
7. Project detail shows dashboard before trace view.
8. Project Sankey only shows tailored scope by default.
