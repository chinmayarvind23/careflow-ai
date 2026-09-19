from models.referral import ReferralExtraction


def validate_referral(referral: ReferralExtraction) -> ReferralExtraction:
    notes = list(referral.validation_notes)
    missing = set(referral.missing_fields)

    # Phone validation
    if referral.phone:
        digits = "".join(ch for ch in referral.phone if ch.isdigit())
        if len(digits) == 10:
            notes.append("Primary phone passed 10-digit structural validation.")
        else:
            notes.append("Primary phone failed 10-digit structural validation.")
    else:
        missing.add("Primary phone")

    # ZIP validation
    if referral.zip_code:
        if referral.zip_code.isdigit() and len(referral.zip_code) == 5:
            notes.append("ZIP code passed 5-digit structural validation.")
        else:
            notes.append("ZIP code failed 5-digit structural validation.")
    else:
        missing.add("ZIP code")

    # Required-ish fields
    required_fields = {
        "patient_name": referral.patient_name,
        "mrn": referral.mrn,
        "insurance_provider": referral.insurance_provider,
        "services_required": referral.services_required,
    }

    for field_name, value in required_fields.items():
        if value is None or value == [] or value == "":
            missing.add(field_name)

    # Service normalization
    normalized = []
    service_map = {
        "physical therapy": "PT",
        "pt": "PT",
        "occupational therapy": "OT",
        "ot": "OT",
        "speech therapy": "ST",
        "st": "ST",
        "skilled nursing": "Skilled Nursing",
        "sn": "Skilled Nursing",
        "home health aide": "HHA",
        "hha": "HHA",
        "medical social worker": "MSW",
        "msw": "MSW",
    }

    for item in referral.services_required:
        key = item.strip().lower()
        normalized.append(service_map.get(key, item))

    referral.services_required = list(dict.fromkeys(normalized))
    notes.append("Services normalized into canonical intake categories.")

    referral.validation_notes = notes
    referral.missing_fields = sorted(missing)

    return referral