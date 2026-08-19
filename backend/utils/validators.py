import re

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{9,14}$")
PINCODE_REGEX = re.compile(r"^\d{6}$")


def normalize_identifier(raw_value):
    value = (raw_value or "").strip()
    if not value:
        return None, None

    if "@" in value:
        email = value.lower()
        if EMAIL_REGEX.match(email):
            return email, "email"
        return None, None

    phone = re.sub(r"[^\d+]", "", value)
    if PHONE_REGEX.match(phone):
        return phone, "phone"

    return None, None


def valid_pincode(value):
    return bool(PINCODE_REGEX.match((value or "").strip()))


def valid_otp(value):
    text = (value or "").strip()
    return len(text) == 6 and text.isdigit()
