"""User guidance separates synthetic speech from evidence of harmful requests.

No classifier, thresholds or risk coefficients are trained or changed here.
MiniLM flags use its supplied validation thresholds. Generic keyword mentions
and synthetic speech alone never authorize HOLD.
"""
import re

REQUEST = re.compile(
    r"\b(?:send|share|give|tell|read|provide|reveal|enter)\b.{0,65}?"
    r"\b(?:otp|one.time password|password|pin|cvv|verification code|security code)\b",
    re.IGNORECASE,
)
BYPASS = re.compile(
    r"\b(?:disable|bypass|skip|ignore|turn off)\b.{0,45}?"
    r"\b(?:verification|security|two.factor|2fa|bank warning)\b", re.IGNORECASE
)
NEGATION = re.compile(r"\b(?:never|not|don['’]t|do not|avoid|mustn['’]t)\b", re.IGNORECASE)


def positive_request(text, pattern):
    for clause in re.split(r"[.!?;\n]|\bbut\b|\bhowever\b", text):
        for match in pattern.finditer(clause):
            # Scope negation to this request, never the whole transcript.
            before = clause[max(0, match.start() - 35):match.start()]
            if not NEGATION.search(before):
                return True
    return False


def guidance(transcript, acoustic, linguistic):
    synthetic = acoustic.get("predicted_class") == "spoof"
    usable = bool(transcript.strip()) and linguistic.get("available") is True
    if not usable:
        return {"action": "ASSESSMENT_PENDING", "assessment": "INSUFFICIENT_EVIDENCE",
                "message": "Possible AI voice; more speech is needed to assess scam indicators."
                if synthetic else "More speech is needed to assess scam indicators.",
                "harm_indicators": [], "scam_probability": None}
    active = set(linguistic.get("triggered_labels", []))
    indicators = []
    if positive_request(transcript, REQUEST):
        indicators.append("REQUEST_FOR_SECRET_CREDENTIAL")
    if positive_request(transcript, BYPASS):
        indicators.append("REQUEST_TO_BYPASS_SECURITY")
    if "financial_request" in active and active & {"coercion", "secrecy", "verification_bypass"}:
        indicators.append("FINANCIAL_REQUEST_WITH_PRESSURE_OR_BYPASS")
    # Multilingual model flags need corroborating pressure/bypass, not an isolated mention.
    if "credential_request" in active and active & {"coercion", "secrecy", "verification_bypass"}:
        indicators.append("CREDENTIAL_REQUEST_WITH_PRESSURE_OR_BYPASS")
    if indicators:
        return {"action": "SECONDARY_VERIFICATION", "assessment": "SCAM_INDICATORS_PRESENT",
                "message": "Suspicious request detected. Verify through a trusted channel.",
                "harm_indicators": indicators, "scam_probability": None}
    return {"action": "AI_NOTICE" if synthetic else "NO_ALERT",
            "assessment": "NO_SCAM_INDICATORS_DETECTED",
            "message": "AI voice indicator detected; no scam indicators detected."
            if synthetic else "No scam indicators detected in the available speech.",
            "harm_indicators": [], "scam_probability": None}
