# 02 User Scenario Derived Requirements

# User Scenario Derived Requirements

## 1. Purpose

This document derives system requirements from user scenarios and recent UI workflow decisions.

The user roles are not intended to be displayed directly in the system interface. They are used as requirement sources.

Input roles:

- Product Assessor
- Product Assessment Manager
- Project Manager

Additional UI workflow decisions:

- The system shall have only two top level entry views: Common and Project.
- Common shall show the original full ISO IEC 25010 product quality model and common information.
- Common shall include a Common Sankey Trace Tree.
- Project shall show projects as cards or list items.
- Project shall provide a plus button to create a new project.
- Create Project shall be an intermediate workflow shown only after clicking the plus button from the Project page.
- Quality Scope Tailoring shall be shown during Create Project and when editing the quality scope of an existing project.
- Project specific Sankey shall only show the tailored project quality scope by default.

## 2. User Scenario Analysis Method

The derivation logic is:

```text
User Role
→ User Objective
→ Business Scenario
→ User Task
→ Required System Capability
→ System Requirement
```

The UI structure is derived as:

```text
Common View
→ Standard model and common trace tree

Project View
→ Project card overview
→ Project detail
→ Project specific traceability
→ Project quality scope editing

Create Project
→ Intermediate project creation and tailoring workflow
```

## 3. Product Assessor Scenario

## 3.1 User Objective

The Product Assessor needs to systematically inspect how each quality requirement is checked and maintain the complete system data for one project.

The Product Assessor focuses on:

- Project quality scope
- Applicability decision and rationale
- Requirement evidence completeness
- Traceability correctness
- Test coverage
- Test result adequacy
- Quality risk status
- Assessment finding recording
- Data consistency

## 3.2 Typical Questions

The Product Assessor needs to answer:

- Which ISO IEC 25010 quality characteristics and subcharacteristics are applicable to this project
- Why is a subcharacteristic not applicable
- Which common quality attributes exist in the original ISO IEC 25010 model
- Which project quality scope is currently used by this project
- Which quality requirements are derived from a selected subcharacteristic
- Is each quality requirement decomposed into verifiable sub quality requirements
- Which architecture element and software module implement the requirement
- Which test cases verify the requirement
- Which test results support the assessment conclusion
- What is the risk status after test result
- Is there missing evidence
- Is there failed evidence
- Are there traceability gaps
- Can the quality scope be updated after project creation

## 3.3 User Tasks

The Product Assessor performs the following tasks:

1. Open Common View to understand the full ISO IEC 25010 model.
2. Review Common Sankey Trace Tree to understand the generic trace structure.
3. Open Project View.
4. Select a project card.
5. Open project detail.
6. Review project dashboard and project specific risk summary.
7. Open Project Sankey Trace View.
8. Select a quality node, requirement node, test case or risk status.
9. Inspect exact structured trace chain.
10. Edit project quality scope if the selected attribute needs to be included, excluded or reclassified.
11. Maintain applicability rationale.
12. Review evidence status and risk status.

## 3.4 Required System Capabilities

The system shall provide:

- Common View with original full ISO IEC 25010 model
- Common Sankey Trace Tree
- Project card or list overview
- Project detail view
- Project specific quality scope view
- Quality Scope Tailoring workflow
- Project specific Sankey Trace View
- Exact trace chain highlighting
- Structured Trace Chain Table
- Quality aspect tags
- Evidence status
- Risk status
- Data maintenance for applicability decision and rationale

## 3.5 Derived Requirements

### USRREQ PA 001

The system shall allow the Product Assessor to access a Common View that displays the complete original ISO IEC 25010 Product Quality model.

### USRREQ PA 002

The Common View shall include common information such as quality characteristics, quality subcharacteristics, product line recommendation context and common trace structure.

### USRREQ PA 003

The Common View shall include a Common Sankey Trace Tree showing the generic trace structure:

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

### USRREQ PA 004

The system shall allow the Product Assessor to open the Project View and select a project from a card or list based project overview.

### USRREQ PA 005

The system shall allow the Product Assessor to inspect project detail after clicking a project card.

### USRREQ PA 006

The project detail shall show project specific quality scope, quality aspect distribution, evidence summary and risk summary.

### USRREQ PA 007

The Product Assessor shall be able to open the Project Sankey Trace View from project detail.

### USRREQ PA 008

The Project Sankey Trace View shall show only the tailored project quality scope by default.

### USRREQ PA 009

The Project Sankey Trace View shall support exact structured trace chain highlighting from quality requirement to risk status.

### USRREQ PA 010

The system shall allow the Product Assessor to edit quality scope after selecting a project or selecting a specific quality attribute.

### USRREQ PA 011

Quality Scope Tailoring shall not be shown as a permanent top level page. It shall appear during project creation or when editing a project quality scope.

### USRREQ PA 012

The system shall allow editing applicability decision and applicability rationale for each quality characteristic and subcharacteristic.

## 4. Product Assessment Manager Scenario

## 4.1 User Objective

The Product Assessment Manager needs to understand the overall product quality attribute risk across projects and within a selected project.

The manager focuses on:

- Risk distribution by quality characteristic
- Risk distribution by quality aspect
- Assessment readiness
- Open findings
- High risk quality requirements
- Evidence gap trend
- Project comparison
- Product level quality risk summary

## 4.2 Typical Questions

The Product Assessment Manager needs to answer:

- Which projects have high risk quality attributes
- Which project is not ready for assessment
- Which project has missing evidence
- Which quality aspects have open risks
- Are FuSA, CS, SOTIF and AI Safety concerns covered
- Which quality subcharacteristics were excluded and why
- Which project should be reviewed first
- What is the overall quality risk status

## 4.3 User Tasks

The Product Assessment Manager performs the following tasks:

1. Open Project View.
2. Review project cards or project list.
3. Compare project readiness, risk count and evidence gap count.
4. Click a project card to inspect project detail.
5. Review project dashboard.
6. Review quality aspect distribution.
7. Review project specific Sankey Trace View when needed.
8. Review excluded quality scope and rationale if risk is suspected.
9. Prepare management summary.

## 4.4 Required System Capabilities

The system shall provide:

- Project card or list overview
- Plus button for project creation
- Project dashboard
- Quality scope coverage summary
- Quality aspect risk summary
- Evidence gap summary
- Assessment readiness status
- Project detail navigation
- Project risk drill down

## 4.5 Derived Requirements

### USRREQ PAM 001

The Project View shall display projects using cards or a list.

### USRREQ PAM 002

Each project card shall show project name, product line, project phase, quality scope count, open risk count, evidence gap count and assessment readiness.

### USRREQ PAM 003

The Project View shall provide a visible plus button for creating a new project.

### USRREQ PAM 004

Clicking a project card shall open the project detail view.

### USRREQ PAM 005

The project detail view shall provide dashboard information, not directly enter the create project workflow.

### USRREQ PAM 006

The project detail dashboard shall show quality scope coverage, quality aspect distribution, evidence status, risk status and assessment readiness.

### USRREQ PAM 007

The project detail view shall provide navigation to Project Sankey Trace View.

### USRREQ PAM 008

The manager shall be able to review excluded items and rationales through project quality scope editing, not through the default project trace graph.

### USRREQ PAM 009

The system shall support comparing project risk status through project cards.

## 5. Project Manager Scenario

## 5.1 User Objective

The Project Manager needs to understand current project quality risks and their impact on delivery.

The Project Manager focuses on:

- Project list status
- Project readiness
- Open risks
- High risks
- Failed tests
- Missing evidence
- Owner
- Due date
- Milestone impact
- Gate Review readiness
- Risk closure progress

## 5.2 Typical Questions

The Project Manager needs to answer:

- Which projects exist
- Which project should be opened
- What is the current project quality risk status
- Which risks may affect delivery
- Which test results failed
- Which evidence is missing
- Which quality aspects are affected
- Is the project ready for Gate Review
- How to create a new project
- How to update project quality scope after project creation

## 5.3 User Tasks

The Project Manager performs the following tasks:

1. Open Project View.
2. Review project cards.
3. Click plus button to create a new project when needed.
4. Create project through intermediate Create Project workflow.
5. Confirm project quality scope.
6. Open project detail.
7. Review project dashboard.
8. Open project Sankey only when detailed traceability is needed.
9. Edit quality scope if project scope changes.

## 5.4 Required System Capabilities

The system shall provide:

- Project View as the main project management page
- Project cards or list
- Plus button for Create Project
- Create Project as an intermediate modal or workflow
- Project detail view
- Project dashboard
- Project specific trace view
- Project quality scope editing
- Assessment readiness indicator

## 5.5 Derived Requirements

### USRREQ PM 001

The system shall provide a Project View that starts with project overview cards or a project list.

### USRREQ PM 002

Create Project shall not be a permanent top level menu item. It shall be invoked from the Project View using the plus button.

### USRREQ PM 003

Create Project shall behave as an intermediate workflow before a project is added to the project list.

### USRREQ PM 004

After project creation, the new project shall appear in the Project View as a card or list item.

### USRREQ PM 005

Clicking the project card shall open project detail.

### USRREQ PM 006

The Project Manager shall be able to open the project dashboard without entering the Sankey trace view first.

### USRREQ PM 007

The project dashboard shall provide risk and evidence summary sufficient for project management.

### USRREQ PM 008

The Project Manager shall be able to open Project Sankey Trace View from project detail when detailed analysis is needed.

### USRREQ PM 009

The Project Manager shall be able to trigger project quality scope editing from project detail.

## 6. Consolidated System Capability Requirements

The three user scenarios jointly require the following system capabilities:

1. Common View
2. Common full ISO IEC 25010 model display
3. Common Sankey Trace Tree
4. Project View
5. Project card or list overview
6. Plus button to create project
7. Create Project intermediate workflow
8. Project Quality Scope Tailoring during creation or editing
9. Project detail dashboard
10. Project specific Sankey Trace View
11. Quality aspect classification
12. Evidence status
13. Risk status
14. Exact structured trace highlighting

## 7. Top Level UI Requirement Summary

The system shall use the following top level UI structure:

```text
Common
Project
```

The system shall not use Create Project or Quality Scope Tailoring as permanent top level tabs.

Create Project shall be shown after clicking plus from Project View.

Quality Scope Tailoring shall be shown during project creation or when editing quality scope from project detail or selected attribute detail.

## 8. Acceptance Criteria

The scenario based requirements are acceptable if:

1. Common View shows the original full ISO IEC 25010 quality model.
2. Common View includes a Common Sankey Trace Tree.
3. Project View displays projects as cards or list items.
4. Project View provides a plus button to create a new project.
5. Create Project appears only after clicking plus.
6. New project creation includes project information, product line selection and quality scope tailoring.
7. Quality Scope Tailoring is not a permanent top level page.
8. Project card click opens project detail.
9. Project detail shows dashboard first.
10. Project Sankey Trace View can be opened from project detail.
11. Project Sankey Trace View uses only tailored project quality scope by default.
12. Excluded quality items remain reviewable through quality scope editing.
13. QM, FuSA, CS, SOTIF and AI Safety are supported as project quality aspect tags.
14. Risk Status appears after Test Result in the trace chain.
