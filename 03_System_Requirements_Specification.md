# 03 System Requirements Specification

# Product Quality Risk and Evidence Traceability System

## 1. Introduction

## 1.1 Purpose

This document specifies system requirements for the Product Quality Risk and Evidence Traceability System.

The system supports:

- Common ISO IEC 25010 Product Quality model overview
- Common Sankey Trace Tree
- Project based quality scope tailoring
- Project card or list overview
- Project specific dashboard
- Project specific Sankey traceability
- Quality requirement traceability
- Evidence checking
- Quality risk monitoring
- ADAS quality aspect classification

## 1.2 Scope

The system shall provide two top level views:

```text
Common
Project
```

The system shall not expose Create Project and Quality Scope Tailoring as permanent top level menu items.

Create Project shall be invoked from the Project View using the plus button.

Quality Scope Tailoring shall appear during Create Project and when editing an existing project quality scope.

## 1.3 Definitions

| Term | Definition |
|---|---|
| Common View | Top level view that shows the complete original ISO IEC 25010 model and common trace structure |
| Project View | Top level view that shows project cards or project list |
| Create Project | Intermediate workflow invoked by clicking plus from Project View |
| Project Quality Scope | Project specific tailored subset of ISO IEC 25010 quality characteristics and subcharacteristics |
| Quality Scope Tailoring | Workflow for deciding applicability and rationale of quality attributes |
| Common Sankey Trace Tree | Generic Sankey trace structure based on the full common model |
| Project Sankey Trace View | Project specific Sankey trace view generated from the tailored project quality scope |
| Quality Aspect | Domain classification such as QM, FuSA, CS, SOTIF or AI Safety |

## 2. Overall System Description

## 2.1 Top Level Navigation

### SYSREQ NAV 001

The system shall provide only two top level navigation entries:

```text
Common
Project
```

### SYSREQ NAV 002

The system shall not provide Create Project as a permanent top level navigation entry.

### SYSREQ NAV 003

The system shall not provide Quality Scope Tailoring as a permanent top level navigation entry.

### SYSREQ NAV 004

Create Project shall be invoked only from the Project View through a plus button.

### SYSREQ NAV 005

Quality Scope Tailoring shall be accessible only during Create Project or through editing an existing project quality scope.

## 2.2 View Structure

The system shall use the following view hierarchy:

```text
Common
→ Common Quality Overview
→ Common ISO IEC 25010 Model
→ Common Sankey Trace Tree

Project
→ Project Overview
→ Project Cards or Project List
→ Plus Button
→ Create Project Workflow
→ Project Detail
→ Project Dashboard
→ Project Quality Scope Editing
→ Project Sankey Trace View
```

## 3. Common View Requirements

### SYSREQ COM 001

The system shall provide a Common View.

### SYSREQ COM 002

The Common View shall display the original complete ISO IEC 25010 Product Quality model.

### SYSREQ COM 003

The Common View shall include all quality characteristics:

- Functional suitability
- Performance efficiency
- Compatibility
- Interaction capability
- Reliability
- Security
- Maintainability
- Flexibility
- Safety

### SYSREQ COM 004

The Common View shall include all quality subcharacteristics under their original parent quality characteristics.

### SYSREQ COM 005

The Common View shall not be affected by project quality scope tailoring.

### SYSREQ COM 006

The Common View shall show common information, including:

- Standard model structure
- Quality characteristic descriptions
- Quality subcharacteristic descriptions
- Common trace chain structure
- Product line recommendation context
- ADAS quality aspect mapping context where applicable

### SYSREQ COM 007

When a quality characteristic is selected in Common View, the system shall show only the subcharacteristics under that selected quality characteristic.

### SYSREQ COM 008

The Common View shall include a Common Sankey Trace Tree.

### SYSREQ COM 009

The Common Sankey Trace Tree shall show the generic trace structure:

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

### SYSREQ COM 010

The Common Sankey Trace Tree shall be based on the complete common model, not on any selected project.

### SYSREQ COM 011

The Common Sankey Trace Tree shall be used as a reference explanation of the traceability structure.

## 4. Project Overview Requirements

### SYSREQ POV 001

The system shall provide a Project View.

### SYSREQ POV 002

The Project View shall initially display a project overview.

### SYSREQ POV 003

The project overview shall display projects as cards or as a list.

### SYSREQ POV 004

Each project card or list item shall show at least:

- Project name
- Product line
- Project phase
- System boundary summary
- Selected quality scope count
- Open risk count
- Evidence gap count
- Assessment readiness

### SYSREQ POV 005

The Project View shall provide a plus button for creating a new project.

### SYSREQ POV 006

The plus button shall be visually available on the Project View.

### SYSREQ POV 007

Clicking the plus button shall open the Create Project workflow.

### SYSREQ POV 008

Clicking a project card or list item shall open the project detail view.

### SYSREQ POV 009

The project overview shall not directly show the Create Project workflow unless the plus button has been clicked.

### SYSREQ POV 010

The project overview shall not show Quality Scope Tailoring by default.

## 5. Create Project Requirements

### SYSREQ CPR 001

The system shall provide Create Project as an intermediate workflow.

### SYSREQ CPR 002

Create Project shall be opened only from the Project View by clicking the plus button.

### SYSREQ CPR 003

Create Project shall support project basic information input.

Fields shall include:

- Project ID
- Project name
- Product line
- Product type
- Project phase
- System boundary
- Assessment target

### SYSREQ CPR 004

Create Project shall support product line selection.

Supported product lines shall include:

- Arene Tools
- ADAS
- Woven City
- Cloud and AI

### SYSREQ CPR 005

After product line selection, the system shall load recommended project quality scope.

### SYSREQ CPR 006

Create Project shall show quality aspect context.

For ADAS, quality aspects shall include:

- QM
- FuSA
- CS
- SOTIF
- AI Safety

### SYSREQ CPR 007

Create Project shall include Quality Scope Tailoring before project confirmation.

### SYSREQ CPR 008

After confirmation, the project shall be added to the Project View as a card or list item.

### SYSREQ CPR 009

After confirmation, the system shall open or allow opening the project detail view.

### SYSREQ CPR 010

Create Project shall support cancellation without creating a project.

## 6. Quality Scope Tailoring Requirements

### SYSREQ TLR 001

The system shall support Quality Scope Tailoring.

### SYSREQ TLR 002

Quality Scope Tailoring shall be shown during Create Project.

### SYSREQ TLR 003

Quality Scope Tailoring shall also be accessible when editing an existing project quality scope.

### SYSREQ TLR 004

Quality Scope Tailoring shall also be accessible after selecting a specific quality attribute or subattribute when the user chooses to edit its applicability.

### SYSREQ TLR 005

Quality Scope Tailoring shall not be shown as a default permanent top level page.

### SYSREQ TLR 006

Quality Scope Tailoring shall allow users to edit applicability decision.

Allowed applicability states shall include:

- Applicable
- Partially applicable
- Not applicable
- Deferred
- Covered by platform
- Covered by supplier
- Out of project scope

### SYSREQ TLR 007

Quality Scope Tailoring shall allow users to edit applicability rationale.

### SYSREQ TLR 008

Quality Scope Tailoring shall show recommended applicability.

### SYSREQ TLR 009

Quality Scope Tailoring shall show recommendation reason or not applicable reason.

### SYSREQ TLR 010

Quality Scope Tailoring shall mark manually modified items.

### SYSREQ TLR 011

Quality Scope Tailoring shall support filtering by quality aspect.

### SYSREQ TLR 012

Quality Scope Tailoring shall support filtering by applicability state.

### SYSREQ TLR 013

Quality Scope Tailoring shall support showing or hiding excluded items.

### SYSREQ TLR 014

Excluded items shall include:

- Not applicable
- Covered by platform
- Covered by supplier
- Out of project scope

### SYSREQ TLR 015

Project specific trace view shall read its data from the confirmed Project Quality Scope.

## 7. Project Detail Requirements

### SYSREQ PDET 001

Clicking a project card or list item shall open project detail.

### SYSREQ PDET 002

Project detail shall first show a project dashboard.

### SYSREQ PDET 003

Project detail shall not directly open the Create Project workflow.

### SYSREQ PDET 004

Project detail shall show:

- Project name
- Product line
- Project phase
- System boundary
- Quality scope coverage
- Quality aspect distribution
- Evidence summary
- Risk summary
- Assessment readiness

### SYSREQ PDET 005

Project detail shall provide an action to edit project quality scope.

### SYSREQ PDET 006

Project detail shall provide an action to open Project Sankey Trace View.

### SYSREQ PDET 007

Project detail shall allow navigation back to Project Overview.

## 8. Project Sankey Trace View Requirements

### SYSREQ PST 001

The system shall provide a Project Sankey Trace View.

### SYSREQ PST 002

The Project Sankey Trace View shall be opened from project detail.

### SYSREQ PST 003

The Project Sankey Trace View shall use only the project tailored quality scope by default.

### SYSREQ PST 004

The Project Sankey Trace View shall hide excluded quality attributes and subattributes by default.

### SYSREQ PST 005

The Project Sankey Trace View may show excluded items only when the user explicitly enables this behavior through project quality scope editing or related display option.

### SYSREQ PST 006

The Project Sankey Trace View shall show the following trace chain:

```text
Quality Characteristic
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

### SYSREQ PST 007

Risk Status shall be shown after Test Result.

### SYSREQ PST 008

The Project Sankey Trace View shall support filtering by:

- Quality characteristic
- Quality aspect
- Risk level
- Evidence status
- Search text

### SYSREQ PST 009

The Project Sankey Trace View shall support selecting any node.

### SYSREQ PST 010

When a node is selected, the system shall highlight the exact structured trace chain.

### SYSREQ PST 011

The system shall not highlight unrelated test cases through shared architecture or software nodes.

### SYSREQ PST 012

The Project Sankey Trace View shall include a detail panel.

### SYSREQ PST 013

The detail panel shall show:

- Node ID
- Node type
- Node source
- Node description
- Related quality aspects
- Evidence status
- Risk level
- Risk status
- Incoming relations
- Outgoing relations
- Structured trace chain

### SYSREQ PST 014

The structured trace chain shall include:

- Quality Requirement
- Sub Quality Requirement
- Architecture Element
- Software Module
- Test Case
- Test Result
- Risk Status

## 9. Project Dashboard Requirements

### SYSREQ PDB 001

The project dashboard shall show quality scope coverage.

### SYSREQ PDB 002

The project dashboard shall show selected quality characteristics.

### SYSREQ PDB 003

The project dashboard shall show selected quality subcharacteristics.

### SYSREQ PDB 004

The project dashboard shall show excluded quality items.

### SYSREQ PDB 005

The project dashboard shall show open risks.

### SYSREQ PDB 006

The project dashboard shall show evidence gaps.

### SYSREQ PDB 007

The project dashboard shall show assessment readiness.

### SYSREQ PDB 008

The project dashboard shall show quality aspect distribution.

### SYSREQ PDB 009

Quality aspect distribution shall include:

- QM
- FuSA
- CS
- SOTIF
- AI Safety

### SYSREQ PDB 010

The project dashboard shall support navigation to project quality scope editing.

### SYSREQ PDB 011

The project dashboard shall support navigation to Project Sankey Trace View.

## 10. Quality Aspect Mapping Requirements

### SYSREQ DQA 001

The system shall support domain quality aspect classification.

### SYSREQ DQA 002

The system shall support at least the following quality aspects:

- QM
- FuSA
- CS
- SOTIF
- AI Safety

### SYSREQ DQA 003

AI Safety shall represent safety and artificial intelligence concerns in the ISO PAS 8800 context.

### SYSREQ DQA 004

A quality subcharacteristic may map to multiple quality aspects.

### SYSREQ DQA 005

A quality requirement may map to multiple quality aspects.

### SYSREQ DQA 006

The system shall support quality aspect tags in Project Dashboard, Quality Scope Tailoring and Project Sankey Trace View.

### SYSREQ DQA 007

The system shall support filtering by quality aspect.

## 11. Data Requirements

### SYSREQ DATA 001

The Common ISO IEC 25010 model shall be stored separately from Project Quality Scope.

### SYSREQ DATA 002

Project Quality Scope shall reference common model items and shall not modify the common model.

### SYSREQ DATA 003

Each project shall maintain its own Project Quality Scope.

### SYSREQ DATA 004

Each Project Quality Scope item shall include:

- Quality characteristic
- Quality subcharacteristic
- Recommended applicability
- Final applicability
- Applicability rationale
- Quality aspects
- Manual override flag

### SYSREQ DATA 005

Each project shall maintain dashboard data derived from Project Quality Scope, test evidence and risk status.

### SYSREQ DATA 006

The prototype may store project data in memory in a single index.html.

### SYSREQ DATA 007

Later versions shall separate data into external JSON files or backend persistence.

### SYSREQ DATA 008

In V6.2 and later, all project data shall be persisted in a PostgreSQL database accessed via a REST API.

### SYSREQ DATA 009

In V6.2 and later, the Common Quality Model shall be seeded from reference JSON files into the database at startup and shall remain read-only at runtime.

### SYSREQ DATA 010

In V6.2 and later, the Sankey graph data shall be fetched once per project view via a dedicated full-data endpoint and processed client-side; subsequent filtering and highlighting shall not require additional server requests.

## 12. Single HTML Prototype Requirement

### SYSREQ IMPL 001

For the current prototype, the deliverable shall be a single index.html file.

### SYSREQ IMPL 002

The index.html file shall include:

- Common View
- Project View
- Create Project workflow
- Quality Scope Tailoring
- Project Dashboard
- Common Sankey Trace Tree
- Project Sankey Trace View
- Sample project data
- Product line recommendation data
- ADAS quality aspect mapping data

### SYSREQ IMPL 003

The prototype may use CDN libraries for D3, d3-sankey and other front end libraries.

### SYSREQ IMPL 004

The prototype shall be directly openable in a browser.

## 12a. V6.2 Client-Server Implementation Requirements

### SYSREQ V62 001

The V6.2 system shall consist of a frontend single-page application and a backend REST API served from the same origin via a reverse proxy.

### SYSREQ V62 002

The frontend shall be built as a Vite-based ES Module project and deployed as static files served by Nginx.

### SYSREQ V62 003

The backend shall be implemented in Python using FastAPI and shall expose all data operations through the REST API defined in `16_REST_API_Specification.md`.

### SYSREQ V62 004

All API endpoints shall be prefixed with `/api/v1/`.

### SYSREQ V62 005

The system shall use PostgreSQL as the sole persistence layer. No data shall be stored in browser localStorage in V6.2.

### SYSREQ V62 006

Database schema migrations shall be managed by Alembic and applied automatically at backend startup.

### SYSREQ V62 007

The full system shall be deployable on an internal private server using Docker Compose with a single `docker compose up` command after `.env` configuration.

### SYSREQ V62 008

The Create Project wizard shall not persist any data until the user confirms in Step 5. Project creation shall be a single atomic API call (`POST /api/v1/projects`) that creates the project and its default Project Quality Scope in one transaction.

### SYSREQ V62 009

The frontend shall fetch the Common Quality Model from `GET /api/v1/common/model` once on page load and cache it in memory. No ISO IEC 25010 data shall be embedded as JavaScript constants in the frontend.

### SYSREQ V62 010

The Project Sankey Trace View shall fetch all project data once via `GET /api/v1/projects/:id/full`. All filtering, node selection, and trace chain highlighting shall be performed client-side on the cached data without additional server requests.

### SYSREQ V62 011

The system shall provide `GET /api/v1/health` returning `{"status": "ok"}` for container health checks.

### SYSREQ V62 012

The system shall provide `POST /api/v1/admin/seed-demo` to populate sample ADAS projects for demonstration purposes. This endpoint shall be idempotent.

## 13. Non Functional Requirements

### NFR 001 Usability

The system shall allow users to navigate using the simple structure:

```text
Common
Project
```

### NFR 002 Understandability

Create Project and Quality Scope Tailoring shall appear only in the context where they are needed.

### NFR 003 Maintainability

Common model data and project scope data shall be logically separated. In V6.2, this separation is enforced at the database level: common model tables are read-only at runtime and project scope tables reference them by ID.

### NFR 004 Visual Clarity

The Sankey trace view shall use thin trace links and exact highlight logic.

### NFR 005 Scalability

The project overview shall support multiple project cards or list items.

### NFR 006 Deployability

The prototype (V5.9.x) shall be delivered as a single browser openable index.html file. V6.2 and later shall be deployable via Docker Compose on an internal server.

### NFR 007 API Response Time

The V6.2 backend shall respond to all CRUD endpoints within 500ms at the 95th percentile under normal internal network conditions.

### NFR 008 Data Durability

In V6.2, project data shall survive application restarts. PostgreSQL data shall be stored in a named Docker volume.

## 14. Acceptance Criteria

The system shall be accepted if:

1. The top level navigation only shows Common and Project.
2. Common shows the original complete ISO IEC 25010 quality model.
3. Common includes a Common Sankey Trace Tree.
4. Project shows project cards or project list.
5. Project provides a plus button to create project.
6. Create Project appears only after clicking the plus button.
7. Create Project includes project information and quality scope tailoring.
8. Quality Scope Tailoring is not a permanent top level view.
9. Project card click opens project detail.
10. Project detail first shows dashboard.
11. Project detail allows editing quality scope.
12. Project detail allows opening Project Sankey Trace View.
13. Project Sankey Trace View uses project tailored scope by default.
14. Risk Status appears after Test Result.
15. QM, FuSA, CS, SOTIF and AI Safety are supported and visible.
16. Project trace selection uses exact structured trace chain highlighting.
