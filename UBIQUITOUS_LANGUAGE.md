# Ubiquitous Language

> PQRETS — Product Quality Risk and Evidence Traceability System
> Domain: Automotive / ADAS quality engineering (ISO IEC 25010)

---

## Quality Model

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Common Quality Model** | The unmodified, full ISO IEC 25010 product quality model shared across all projects | ISO model, base model |
| **Quality Characteristic** | One of the 9 top-level categories in the Common Quality Model (e.g. Performance Efficiency, Safety) | Quality attribute, quality category |
| **Quality Subcharacteristic** | A refinement of a Quality Characteristic; the unit at which scope decisions are made (e.g. Time Behaviour) | Quality attribute, subattribute, subcharacteristic |
| **Quality Goal** | A project-specific, measurable statement of intent derived from a Quality Subcharacteristic | Quality objective |
| **Quality Requirement** | A concrete, verifiable engineering requirement derived from a Quality Goal | Requirement, functional requirement |
| **Sub-Quality Requirement** | A decomposition of a Quality Requirement into a single verifiable acceptance criterion | Sub-requirement, sub-req |

---

## Project Scope

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Project Quality Scope** | The project-specific tailored subset of the Common Quality Model, consisting of Applicability Decisions for each Quality Subcharacteristic | Project scope, quality scope, tailored scope |
| **Applicability Decision** | A single record that assigns an Applicability State and rationale to one Quality Subcharacteristic within a project | Scope item, scope decision |
| **Applicability State** | One of seven values describing how a Quality Subcharacteristic applies to a project: Applicable, Partially applicable, Not applicable, Deferred, Covered by platform, Covered by supplier, Out of project scope | Applicability, status |
| **Quality Scope Tailoring** | The workflow in which a user reviews recommendations and sets Applicability Decisions for each Quality Subcharacteristic | Tailoring, scope editing, scope customization |
| **Manual Override** | A flag on an Applicability Decision indicating that the user explicitly changed the Product Line recommendation | Override flag |
| **Product Line** | A recommendation profile used to generate default Applicability Decisions for a new project; one of: AreneTools, ADAS, WovenCity, CloudAI | Product type (product type is a separate free-text field) |
| **Product Line Recommendation** | The default Applicability State and Quality Aspects suggested for a Quality Subcharacteristic based on the selected Product Line | Recommendation, default scope |

---

## Quality Aspects

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Quality Aspect** | An automotive domain classification applied to Quality Subcharacteristics and Requirements; one of: QM, FuSA, CS, SOTIF, AI Safety | Domain aspect, safety aspect |
| **QM** | Quality Management — general product quality and engineering quality | Quality management |
| **FuSA** | Functional Safety — ISO 26262 context | Functional safety, ASIL |
| **CS** | Cybersecurity — ISO SAE 21434 context | Cybersecurity, security |
| **SOTIF** | Safety of the Intended Functionality — ISO 21448 context | Intended functionality safety |
| **AI Safety** | Safety and Artificial Intelligence — ISO PAS 8800 context | AI safety, artificial intelligence safety |

---

## Traceability Chain

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Trace Chain** | The directed path from Quality Subcharacteristic through to Risk Status, comprising 11 layers | Traceability chain, trace path |
| **Architecture Element** | A named component of the system architecture that implements one or more Quality Requirements | Component, system element, architectural element |
| **Software Module** | A named software unit belonging to an Architecture Element that is verified by Test Cases | Module, software component |
| **Test Case** | A defined verification procedure linked to a Software Module and optionally to a Sub-Quality Requirement | Test, verification case |
| **Test Result** | The recorded outcome of executing a Test Case; one active result per Test Case | Test execution, test outcome |
| **Risk Item** | A recorded quality risk associated with a project, carrying severity, likelihood, and a computed Risk Level | Risk, quality risk |
| **Evidence Item** | A reference to an artifact (report, review record, analysis) that supports a Quality Requirement or Test Result | Evidence, artifact |
| **Assessment Finding** | A recorded gap, non-conformance, or observation identified during quality assessment | Finding, issue, non-conformance |
| **Action Item** | A tracked corrective or improvement action linked to an Assessment Finding or Risk Item | Action, task, corrective action |

---

## Risk and Readiness

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Risk Level** | A computed classification of a Risk Item's severity; one of: Critical, High, Medium, Low | Risk rating, risk score |
| **Evidence Status** | A computed summary of test coverage for a Quality Requirement; one of: Complete, Partial, Missing, Failed | Evidence completeness |
| **Assessment Readiness** | A project-level computed status indicating readiness for formal assessment; one of: Ready, Conditionally ready, Not ready | Readiness, gate readiness |

---

## Views and Workflows

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Common View** | The top-level view displaying the unmodified Common Quality Model and the Common Sankey Trace Tree | ISO view, model view |
| **Project View** | The top-level view displaying project cards and providing access to project detail | Project list, project overview |
| **Project Detail** | The view shown after clicking a project card; first displays the Project Dashboard | Project workspace, project page |
| **Project Dashboard** | The summary panel within Project Detail showing scope coverage, risk counts, evidence gaps, and Assessment Readiness | Dashboard, summary |
| **Common Sankey Trace Tree** | The Sankey diagram in the Common View showing the generic 11-layer trace structure based on the full Common Quality Model | Common Sankey, generic Sankey |
| **Project Sankey Trace View** | The Sankey diagram in Project Detail showing only the tailored Project Quality Scope with real trace data | Project Sankey, trace view, Sankey trace |
| **Create Project** | The 5-step wizard workflow triggered by the plus button in Project View that collects basic information, selects a Product Line, sets Quality Aspects, performs Quality Scope Tailoring, and confirms project creation | New project workflow, project wizard |

---

## Actors

| Term | Definition | Aliases to avoid |
|---|---|---|
| **Product Assessor** | A user role responsible for maintaining and verifying the complete trace chain for a project | Assessor |
| **Product Assessment Manager** | A user role responsible for cross-project quality risk visibility and assessment readiness | Assessment manager, manager |
| **Project Manager** | A user role responsible for tracking open risks and delivery readiness within a project | PM |

---

## Relationships

- A **Project Quality Scope** belongs to exactly one **Project** and references items from the **Common Quality Model** without modifying it.
- An **Applicability Decision** belongs to exactly one **Project Quality Scope** and targets exactly one **Quality Subcharacteristic**.
- A **Quality Goal** belongs to one **Applicability Decision**; one **Applicability Decision** may have zero or more **Quality Goals**.
- A **Quality Requirement** belongs to one **Quality Goal** and may link to one **Architecture Element**.
- A **Sub-Quality Requirement** refines one **Quality Requirement** and may link to one **Architecture Element** for the trace path.
- A **Test Case** belongs to one **Software Module** and may optionally link to one **Sub-Quality Requirement** for explicit trace.
- A **Test Result** is the current execution outcome of exactly one **Test Case** (one-to-one).
- A **Risk Item** belongs to one **Project** and may reference a **Quality Subcharacteristic**, a **Quality Requirement**, or a **Test Result**.
- A **Software Module** belongs to exactly one **Architecture Element**.
- The **Project Sankey Trace View** renders only the **Project Quality Scope** — it never shows items with Applicability State = Not applicable, Covered by platform, Covered by supplier, or Out of project scope, unless the user explicitly enables "Show Excluded Items".

---

## Example Dialogue

> **Dev:** "When a user creates a project and picks the ADAS **Product Line**, do we immediately create the **Project Quality Scope**?"

> **Domain expert:** "Not immediately — the wizard shows the **Product Line Recommendations** in Step 4 so the user can do **Quality Scope Tailoring** first. The **Project Quality Scope** is only written to the database when the user confirms in Step 5."

> **Dev:** "So if the user changes an **Applicability State** from Applicable to Covered by platform, does that disappear from the **Project Sankey Trace View**?"

> **Domain expert:** "Yes, by default. 'Covered by platform' is an excluded state. The node won't appear in the **Trace Chain** unless the user enables Show Excluded Items. The **Applicability Decision** is still stored — it just isn't visualised."

> **Dev:** "And if a **Quality Requirement** has no **Test Case** linked yet, what is the **Evidence Status**?"

> **Domain expert:** "Missing. No **Test Case** means no **Test Result**, so the **Quality Requirement** has a gap. That gap counts toward the **Evidence Gap** count in the **Project Dashboard** and affects **Assessment Readiness**."

> **Dev:** "One more: is a **Risk Item** always linked to a **Test Result**?"

> **Domain expert:** "No — a **Risk Item** can exist independently at the project level, or it can reference a **Quality Subcharacteristic**, a **Quality Requirement**, or a **Test Result**. The link is optional; it exists to provide traceability context, not to enforce a workflow."

---

## Flagged Ambiguities

- **"Quality attribute"** was used in early documents to mean both **Quality Characteristic** and **Quality Subcharacteristic**. These are distinct levels of the ISO model. Use the specific term.
- **"Scope"** alone is ambiguous — it can mean **Project Quality Scope** (the full set of decisions) or **System Boundary** (a project metadata field). Always qualify it.
- **"Product type"** and **"Product line"** are distinct: **Product Line** is an enum (AreneTools, ADAS, WovenCity, CloudAI) that drives recommendations; **Product Type** is a free-text field describing the specific product (e.g. "ADAS ECU"). Do not use them interchangeably.
- **"Risk status"** appears as both a Sankey layer label (the rightmost node type in the trace chain) and a field on **Risk Item** (Open / Mitigated / Accepted / Closed). When referring to the Sankey layer use **Risk Status node**; when referring to the field use **risk item status**.
- **"Evidence"** alone is overloaded — it can mean **Evidence Status** (a computed enum), **Evidence Item** (a managed record), or `evidence_link` (a URL field on Test Result). Use the full term.
