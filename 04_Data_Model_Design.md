# 04 Data Model Design

# Product Quality Risk and Evidence Traceability System

## 1. Purpose

This document defines the data model for the Product Quality Risk and Evidence Traceability System.

The data model supports:

- Common ISO IEC 25010 Product Quality model
- Product line recommendation rules
- Project creation
- Project specific quality scope tailoring
- Applicability decisions and rationales
- ADAS quality aspect mapping
- Quality requirement traceability
- Test evidence management
- Risk management
- Project overview dashboard

## 2. Core Data Design Principle

The system shall separate the common quality model from project specific quality data.

```text
Common ISO IEC 25010 Model
→ Product Line Recommendation Rules
→ Project Quality Scope
→ Project Quality Requirements
→ Test Evidence
→ Risk Items
```

The Common ISO IEC 25010 model shall not be modified by project tailoring.

Each project shall create and maintain its own Project Quality Scope.

## 3. Main Data Objects

The system data model includes the following major objects:

```text
CommonQualityModel
QualityCharacteristic
QualitySubcharacteristic
ProductLineProfile
RecommendationRule
Project
ProjectQualityScope
ApplicabilityDecision
QualityAspectMapping
QualityGoal
QualityRequirement
SubQualityRequirement
ArchitectureElement
SoftwareModule
TestCase
TestResult
RiskItem
EvidenceItem
AssessmentFinding
ActionItem
```

## 4. CommonQualityModel

The CommonQualityModel stores the full ISO IEC 25010 Product Quality model.

Key fields:

| Field | Description |
|---|---|
| modelId | Unique model ID |
| modelName | Model name |
| standardReference | Standard reference |
| version | Model version |
| rootName | Root node name |
| characteristics | List of quality characteristics |

## 5. ProjectQualityScope

ProjectQualityScope stores the tailored quality model for a project.

Each record links a project to one ISO IEC 25010 quality subcharacteristic and stores the project specific applicability decision.

Key fields:

| Field | Description |
|---|---|
| scopeItemId | Unique scope item ID |
| projectId | Project ID |
| qualityCharacteristicId | Quality characteristic ID |
| qualitySubcharacteristicId | Quality subcharacteristic ID |
| applicability | Applicability decision |
| applicabilityRationale | Rationale for decision |
| recommendedApplicability | System recommended applicability |
| recommendationReason | System recommendation reason |
| defaultQualityAspects | Recommended quality aspects |
| selectedQualityAspects | Project selected quality aspects |
| manualOverride | Whether user manually changed the recommendation |
| decisionOwner | Owner of tailoring decision |
| decisionDate | Decision date |
| reviewStatus | Draft, Reviewed, Approved |

## 6. Applicability States

Recommended states:

```text
Applicable
Partially applicable
Not applicable
Deferred
Covered by platform
Covered by supplier
Out of project scope
```

## 7. Quality Aspects

The system shall support:

```text
QM
FuSA
CS
SOTIF
AI Safety
```

AI Safety refers to the ISO PAS 8800 context for safety and artificial intelligence in road vehicles.

## 8. Trace Relationship Model

Recommended explicit trace relationships:

```text
QualitySubcharacteristic → QualityGoal
QualityGoal → QualityRequirement
QualityRequirement → SubQualityRequirement
SubQualityRequirement → ArchitectureElement
ArchitectureElement → SoftwareModule
SoftwareModule → TestCase
TestCase → TestResult
TestResult → RiskItem
```

The visualization shall use these structured relationships instead of generic graph connectivity.

## 9. Project View Filtering Rules

### Rule 1

Common View always displays the complete ISO IEC 25010 model.

### Rule 2

Project View displays only these applicability states by default:

```text
Applicable
Partially applicable
Deferred
```

### Rule 3

Project View hides these applicability states by default:

```text
Not applicable
Covered by platform
Covered by supplier
Out of project scope
```

### Rule 4

Users may enable Show Excluded Items to inspect excluded items and rationales.

### Rule 5

If all subcharacteristics under a quality characteristic are excluded, the characteristic is hidden in the default project trace view.

### Rule 6

If only part of the subcharacteristics under a characteristic are applicable, the characteristic is shown with only selected subcharacteristics.

## 10. Dashboard Calculation Rules

### Evidence Status Summary

```text
All related test results passed → Evidence complete
Some related test results not executed → Evidence partial
No related test case → Evidence missing
Any related test result failed → Evidence failed
```

### Risk Level Suggestion

```text
Safety or AI Safety related missing evidence → High risk
CS related failed evidence → High risk
FuSA related failed evidence → High or Critical risk
QM related partial evidence → Medium risk
Complete evidence with passed tests → Low risk
```

### Assessment Readiness

```text
No high or critical open risk and no missing critical evidence → Ready
Some medium open risk or partial evidence → Conditionally ready
Any high or critical open risk or failed key evidence → Not ready
```

## 11. Data Objects Detail

### ProductLineProfile

Defines product line context and recommendation behavior.

Fields:

- productLineId
- productLineName
- description
- typicalSystemBoundary
- recommendationRules

### RecommendationRule

Defines whether a quality subcharacteristic is recommended for a product line.

Fields:

- ruleId
- productLineId
- qualityCharacteristicId
- qualitySubcharacteristicId
- recommendedApplicability
- recommendationReason
- notApplicableReason
- defaultQualityAspects
- editable

### Project

Represents one project workspace.

Fields:

- projectId
- projectName
- productLineId
- productType
- systemBoundary
- projectPhase
- customer
- assessmentTarget
- createdAt
- updatedAt

### QualityRequirement

Represents a concrete engineering quality requirement.

Fields:

- qualityRequirementId
- projectId
- qualityGoalId
- requirementText
- qualityAspects
- scenario
- riskLevel
- evidenceStatus
- owner
- assessmentStatus

### SubQualityRequirement

Refines a quality requirement into verifiable criteria.

Fields:

- subQualityRequirementId
- qualityRequirementId
- acceptanceCriterion
- verificationCondition
- inputCondition
- expectedOutput
- measuredValue
- passFailCriterion

### TestCase

Verifies one or more sub quality requirements.

Fields:

- testCaseId
- projectId
- relatedSubQualityRequirementIds
- testObjective
- testMethod
- inputData
- precondition
- expectedResult
- passFailCriterion
- evidenceLink

### TestResult

Records execution result of a test case.

Fields:

- testResultId
- testCaseId
- executionStatus
- actualResult
- measuredValue
- executionDate
- tester
- evidenceFile
- deviation
- conclusion

### RiskItem

Records a quality risk.

Fields:

- riskId
- projectId
- title
- description
- relatedQualityCharacteristicId
- relatedQualitySubcharacteristicId
- relatedQualityRequirementId
- relatedTestResultId
- qualityAspects
- riskLevel
- riskStatus
- riskReason
- impact
- mitigationAction
- owner
- dueDate
- targetMilestone
