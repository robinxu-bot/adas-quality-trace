# 01 System Concept and Scope

# Product Quality Risk and Evidence Traceability System

## 1. Purpose

The system provides a common ISO IEC 25010 based product quality model and enables each project to define, tailor, maintain and monitor its project specific quality scope, evidence chain and quality risk status.

The system shall answer these questions:

- Which quality characteristics and subcharacteristics are applicable to this project
- Why are some quality items not applicable
- Which quality requirements are derived from selected quality subcharacteristics
- How are these quality requirements verified
- Which test cases and test results support each quality requirement
- Which quality risks remain open
- Which risks may affect project milestones or assessment readiness

## 2. System Positioning

The system combines four layers:

1. Common Quality Model

   - Complete ISO IEC 25010 Product Quality model
   - Product Quality
   - Quality Characteristics
   - Quality Subcharacteristics
2. Project Specific Quality Scope

   - Project level tailoring
   - Applicability decision
   - Applicability rationale
   - Recommended and manually adjusted scope
3. Domain Quality Aspect Classification

   - QM
   - FuSA
   - CS
   - SOTIF
   - AI Safety
4. Risk and Evidence Traceability

   - Quality Requirement
   - Sub Quality Requirement
   - Architecture Element
   - Software Module
   - Test Case
   - Test Result
   - Risk Status

## 3. Common View and Project View

### 3.1 Common Quality Overview

The Common Quality Overview displays the complete ISO IEC 25010/25012 Product Quality model.

It is used for:

- Viewing the complete common quality model
- Reviewing product line recommendation rules
- Reviewing ADAS domain quality aspect mapping
- Understanding the relationship between ISO IEC 25010 and domain specific quality aspects

The Common View shall not be modified by project tailoring.

### 3.2 Project Quality Workspace

The Project Quality Workspace is used to create and maintain project specific quality data.

It is used for:

- Creating a new project
- Selecting a product line
- Loading recommended quality scope
- Tailoring applicable quality characteristics and subcharacteristics
- Maintaining applicability decisions and rationales
- Maintaining quality requirements
- Maintaining test evidence
- Maintaining quality risks
- Viewing project quality dashboard
- Viewing project specific traceability graph

The Project View shall only show the quality characteristics and subcharacteristics selected for the project, except when the user explicitly chooses to show excluded items.

## 4. Project Creation Concept

Project creation shall follow this workflow:

1. Create Project
2. Enter project basic information
3. Select product line
4. Load recommended quality scope
5. Review recommended applicable and not applicable quality items
6. Manually tailor quality characteristics and subcharacteristics
7. Provide or edit applicability rationale
8. Confirm project quality scope
9. Generate project specific quality workspace
10. Enter project overview dashboard

## 5. Project Quality Scope Tailoring

For each quality characteristic and subcharacteristic, the system shall support an applicability decision.

Recommended applicability states:

- Applicable
- Partially applicable
- Not applicable
- Deferred
- Covered by platform
- Covered by supplier
- Out of project scope

The system shall provide recommended applicability and rationale based on:

- Product line
- Product type
- System boundary
- Project phase
- Safety relevance
- Cybersecurity relevance
- SOTIF relevance
- AI Safety relevance
- Customer requirement scope
- Regulatory scope

Users shall be able to manually edit the applicability state and rationale.

## 6. Quality Aspect Classification

The system shall support at least the following quality aspects:

| Short Name | Full Name                            | Reference Context                               |
| ---------- | ------------------------------------ | ----------------------------------------------- |
| QM         | Quality Management                   | Product quality and general engineering quality |
| FuSA       | Functional Safety                    | ISO 26262 context                               |
| CS         | Cybersecurity                        | ISO SAE 21434 context                           |
| SOTIF      | Safety of the Intended Functionality | ISO 21448 context                               |
| AI Safety  | Safety and Artificial Intelligence   | ISO PAS 8800 context                            |

A quality subcharacteristic may be mapped to multiple quality aspects.

Example mappings for ADAS:

| ISO IEC 25010 Item                              | ADAS Quality Aspect Mapping |
| ----------------------------------------------- | --------------------------- |
| Safety / Risk identification                    | FuSA, SOTIF, AI Safety      |
| Safety / Fail safe                              | FuSA                        |
| Security / Integrity                            | CS, FuSA                    |
| Performance efficiency / Time behaviour         | QM, FuSA, SOTIF, AI Safety  |
| Functional suitability / Functional correctness | QM, FuSA, SOTIF, AI Safety  |
| Interaction capability / User error protection  | QM, FuSA, SOTIF             |

## 7. Product Lines

Initial product lines:

- Arene Tools
- ADAS
- Woven City
- Cloud and AI

Product lines are not ISO IEC 25010 categories. They are recommendation profiles for tailoring.

## 8. Project Overview Dashboard

After project creation, the system shall provide a project overview dashboard showing:

- Project name
- Product line
- Project phase
- System boundary
- Selected quality characteristics
- Selected quality subcharacteristics
- Excluded quality subcharacteristics
- Quality aspect distribution
- Open risks
- High risks
- Missing evidence
- Failed tests
- Overdue actions
- Assessment readiness status

Assessment readiness may be shown as Ready, Conditionally ready or Not ready.

## 9. Project Specific Traceability View

The project specific traceability view shall visualize only the quality scope selected for the project.

Default chain:

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

When a user selects a quality requirement, the system shall highlight only the exact related trace chain.

The system shall not use generic graph connectivity to determine related test cases, because shared architecture or software nodes may otherwise cause unrelated test cases to be displayed or highlighted.

## 10. Initial Prototype Boundary

The initial prototype shall support:

- Common ISO IEC 25010 quality model viewing
- Project creation mock workflow
- Project quality scope tailoring
- Applicability rationale maintenance
- Quality aspect mapping
- Project overview dashboard
- Project specific traceability visualization

The initial prototype shall not require:

- User login
- Backend database
- Multi user collaboration
- Workflow approval
- Real file attachment storage
- Excel import
- PDF export
- ALM integration
- Test tool integration

## 11. Core Concept Statement

The system shall provide a common ISO IEC 25010/25012 product quality model overview and support project level quality scope tailoring. When creating a project, users shall receive recommended applicable and not applicable quality characteristics and subcharacteristics based on product line and domain context, review recommendation rationales, manually adjust the tailoring result, and confirm the project specific quality scope. After project creation, the system shall only display the tailored quality scope in the project workspace and shall support end to end traceability from quality requirements to test evidence and quality risks. For ADAS projects, the system shall support quality aspect mapping to QM, FuSA, CS, SOTIF and AI Safety.
