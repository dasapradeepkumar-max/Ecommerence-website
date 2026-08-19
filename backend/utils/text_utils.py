import re


def slugify(value):
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", (value or "").strip().lower())
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")
