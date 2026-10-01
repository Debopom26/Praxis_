from enum import StrEnum


class ModuleStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    LOW_QUALITY = "LOW_QUALITY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class ArtifactState(StrEnum):
    NOT_LOADED = "NOT_LOADED"
    UNVALIDATED = "UNVALIDATED"
    VALIDATED = "VALIDATED"


class SpeakerState(StrEnum):
    MATCH = "MATCH"
    UNCERTAIN = "UNCERTAIN"
    MISMATCH = "MISMATCH"
    UNAVAILABLE = "UNAVAILABLE"


class ImplementationState(StrEnum):
    DESIGNED = "DESIGNED"
    IMPLEMENTED = "IMPLEMENTED"
    VALIDATED = "VALIDATED"
    DEMO_READY = "DEMO_READY"


class PolicyAction(StrEnum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    SECONDARY_VERIFICATION = "SECONDARY_VERIFICATION"
    ESCALATE = "ESCALATE"
    HOLD = "HOLD"


class RuleFlag(StrEnum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class LinguisticLabel(StrEnum):
    URGENCY = "urgency"
    SECRECY = "secrecy"
    AUTHORITY_PRESSURE = "authority_pressure"
    FINANCIAL_REQUEST = "financial_request"
    CREDENTIAL_REQUEST = "credential_request"
    VERIFICATION_BYPASS = "verification_bypass"
    COERCION = "coercion"
    EMOTIONAL_PRESSURE = "emotional_pressure"
