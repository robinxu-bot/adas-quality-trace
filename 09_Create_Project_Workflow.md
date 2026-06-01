# 09 Create Project Workflow

# Updated Create Project Workflow

## 1. Purpose

This document defines the updated Create Project workflow.

Create Project is an intermediate workflow and shall not be shown as a top level tab.

## 2. Trigger

Create Project shall be triggered by clicking the plus button in Project View.

```text
Project View
→ Plus Button
→ Create Project
```

## 3. Workflow Steps

Create Project shall include:

```text
Step 1 Project Basic Information
Step 2 Product Line Selection
Step 3 Quality Aspect Context
Step 4 Quality Scope Tailoring
Step 5 Confirmation
```

## 4. Step 1 Project Basic Information

Fields:

- Project ID
- Project Name
- Product Type
- Project Phase
- System Boundary
- Assessment Target

## 5. Step 2 Product Line Selection

Product line options:

- Arene Tools
- ADAS
- Woven City
- Cloud and AI

Selecting a product line loads:

- Product line description
- Recommendation profile
- Default quality scope
- Default quality aspects
- Default applicability rationale

## 6. Step 3 Quality Aspect Context

For ADAS projects, supported quality aspects are:

- QM
- FuSA
- CS
- SOTIF
- AI Safety

AI Safety refers to safety and artificial intelligence concern in ISO PAS 8800 context.

## 7. Step 4 Quality Scope Tailoring

Quality Scope Tailoring is part of Create Project.

The tailoring table shall include:

- Quality Characteristic
- Quality Subcharacteristic
- Recommended Applicability
- User Applicability
- Recommendation Reason
- Applicability Rationale
- Quality Aspects
- Manual Override

Allowed applicability values:

- Applicable
- Partially applicable
- Not applicable
- Deferred
- Covered by platform
- Covered by supplier
- Out of project scope

## 8. Step 5 Confirmation

The confirmation step shall show:

- Project basic information
- Product line
- Selected quality characteristics
- Selected quality subcharacteristics
- Excluded quality subcharacteristics
- Quality aspect distribution
- Manual override count
- Missing rationale warnings

## 9. Output

After confirmation:

1. A new project is created.
2. The new project is displayed as a project card or list item in Project View.
3. The Project Quality Scope is stored for that project.
4. The project detail dashboard becomes available.
5. Project Sankey Trace View can be generated from the tailored Project Quality Scope.

## 10. Edit Existing Project Quality Scope

For an existing project, Quality Scope Tailoring can be opened from:

- Project detail
- Selected quality attribute detail
- Selected quality subattribute detail

After editing, the Project Sankey Trace View shall refresh based on the updated Project Quality Scope.

## 11. Acceptance Criteria

1. Create Project appears only after clicking plus.
2. Create Project includes Quality Scope Tailoring.
3. Cancel does not create a project.
4. Save creates a project card.
5. Project card click opens project detail.
6. Project Sankey uses the saved project quality scope.
