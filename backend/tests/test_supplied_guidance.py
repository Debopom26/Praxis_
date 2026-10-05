from praxis.supplied.guidance import guidance


def result(text, labels=(), available=True, synthetic=True):
    return guidance(text, {"predicted_class": "spoof" if synthetic else "bonafide"},
                    {"available": available, "triggered_labels": list(labels)})


def test_synthetic_weather_report_does_not_trigger_scam_hold():
    value = result("Today's forecast is warm and sunny.")
    assert value["action"] == "AI_NOTICE"
    assert value["scam_probability"] is None


def test_safety_advice_does_not_become_credential_request():
    assert result("Never share your OTP. Do not provide your password.")["action"] == "AI_NOTICE"


def test_negation_does_not_hide_later_malicious_request():
    assert result("Never share your OTP with strangers. Give me your PIN now.")["action"] == "SECONDARY_VERIFICATION"


def test_human_scam_is_not_ignored():
    assert result("Send your verification code to me.", synthetic=False)["assessment"] == "SCAM_INDICATORS_PRESENT"


def test_missing_linguistic_evidence_is_not_called_safe():
    assert result("", available=False)["assessment"] == "INSUFFICIENT_EVIDENCE"


def test_isolated_authority_or_financial_label_does_not_block():
    assert result("Your monthly invoice is ready.", ["financial_request", "authority_pressure"])["action"] == "AI_NOTICE"


def test_financial_coercion_still_requires_verification():
    assert result("Transfer the money or face consequences.", ["financial_request", "coercion"])["action"] == "SECONDARY_VERIFICATION"
