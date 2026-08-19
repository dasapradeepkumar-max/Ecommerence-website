import re

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{9,14}$")
PINCODE_REGEX = re.compile(r"^\d{6}$")


def normalize_identifier(raw: str) -> tuple[str | None, str | None]:
    text = (raw or "").strip()
    if not text:
        return None, None

    if "@" in text:
        email = text.lower()
        if EMAIL_REGEX.match(email):
            return email, "email"
        return None, None

    phone = re.sub(r"[^\d+]", "", text)
    if PHONE_REGEX.match(phone):
        return phone, "phone"

    return None, None


def is_valid_pincode(value: str) -> bool:
    return bool(PINCODE_REGEX.match((value or "").strip()))
