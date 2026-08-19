import hashlib
import hmac
import secrets


def generate_otp(length: int = 6) -> str:
    max_val = 10**length
    return str(secrets.randbelow(max_val)).zfill(length)


def hash_otp(otp: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}:{otp}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_otp_hash(otp: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    calculated = hashlib.sha256(f"{salt}:{otp}".encode("utf-8")).hexdigest()
    return hmac.compare_digest(calculated, digest)
