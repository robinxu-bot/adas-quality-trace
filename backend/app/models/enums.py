import enum


class QualityAspect(str, enum.Enum):
    QM = "QM"
    FuSA = "FuSA"
    CS = "CS"
    SOTIF = "SOTIF"
    AI_Safety = "AI Safety"


class ProductLine(str, enum.Enum):
    AreneTools = "AreneTools"
    ADAS = "ADAS"
    WovenCity = "WovenCity"
    CloudAI = "CloudAI"


class ProjectPhase(str, enum.Enum):
    Concept = "Concept"
    Development = "Development"
    Validation = "Validation"
    Production = "Production"


class ApplicabilityValue(str, enum.Enum):
    Applicable = "Applicable"
    PartiallyApplicable = "Partially applicable"
    NotApplicable = "Not applicable"
    Deferred = "Deferred"
    CoveredByPlatform = "Covered by platform"
    CoveredBySupplier = "Covered by supplier"
    OutOfProjectScope = "Out of project scope"


class RiskLevel(str, enum.Enum):
    Critical = "Critical"
    High = "High"
    Medium = "Medium"
    Low = "Low"


class RiskItemStatus(str, enum.Enum):
    Open = "Open"
    Mitigated = "Mitigated"
    Accepted = "Accepted"
    Closed = "Closed"


class TestResultValue(str, enum.Enum):
    Pass = "Pass"
    Fail = "Fail"
    Blocked = "Blocked"
    NotRun = "Not run"


class EvidenceStatus(str, enum.Enum):
    Complete = "Complete"
    Partial = "Partial"
    Missing = "Missing"
    Failed = "Failed"


class ReviewStatus(str, enum.Enum):
    Draft = "Draft"
    Reviewed = "Reviewed"
    Approved = "Approved"


class FindingStatus(str, enum.Enum):
    Open = "Open"
    InProgress = "In Progress"
    Resolved = "Resolved"
    Closed = "Closed"


class ActionStatus(str, enum.Enum):
    Open = "Open"
    InProgress = "In Progress"
    Closed = "Closed"
