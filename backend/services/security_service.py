import hashlib
import hmac
import secrets


def generate_otp(length=6):
    return str(secrets.randbelow(10**length)).zfill(length)


def hash_otp(otp):
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}:{otp}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_otp_hash(otp, stored_hash):
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False

    computed = hashlib.sha256(f"{salt}:{otp}".encode("utf-8")).hexdigest()
    return hmac.compare_digest(computed, digest)
