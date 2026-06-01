"""Shared domain constants used across services."""
from app.models.enums import ApplicabilityValue

ASPECTS = ["QM", "FuSA", "CS", "SOTIF", "AI Safety"]

INCLUDED_APPLICABILITY = {
    ApplicabilityValue.Applicable,
    ApplicabilityValue.PartiallyApplicable,
    ApplicabilityValue.Deferred,
}

EXCLUDED_APPLICABILITY = {
    ApplicabilityValue.NotApplicable,
    ApplicabilityValue.CoveredByPlatform,
    ApplicabilityValue.CoveredBySupplier,
    ApplicabilityValue.OutOfProjectScope,
}
