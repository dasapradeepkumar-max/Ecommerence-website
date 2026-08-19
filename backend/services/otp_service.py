import random
import hashlib
from datetime import datetime, timedelta
from backend.models.database import Database
from config.settings import Settings


class OTPService:

    @staticmethod
    def _hash_otp(otp: str) -> str:
        return hashlib.sha256(otp.encode("utf-8")).hexdigest()

    @classmethod
    def generate_and_send_otp(cls, identifier: str, purpose: str = "login") -> dict:
        """Generate 6-digit OTP, record in DB, and log/send."""
        identifier = identifier.strip().lower()

        # Check resend count in last 1 hour
        one_hour_ago = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        resend_count = Database.query_one(
            "SELECT COUNT(*) as count FROM otp_codes WHERE identifier = %s AND created_at >= %s",
            (identifier, one_hour_ago)
        )
        if resend_count and resend_count.get("count", 0) >= Settings.OTP_RESEND_LIMIT:
            return {
                "success": False,
                "message": f"Too many OTP requests. Please wait before requesting another OTP."
            }

        # Generate 6-digit OTP
        raw_otp = f"{random.randint(100000, 999999)}"
        otp_hash = cls._hash_otp(raw_otp)
        expires_at = (datetime.now() + timedelta(minutes=Settings.OTP_EXPIRY_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")

        # Save to database
        Database.execute(
            """
            INSERT INTO otp_codes (identifier, purpose, otp_hash, attempts, expires_at, created_at)
            VALUES (%s, %s, %s, 0, %s, CURRENT_TIMESTAMP)
            """,
            (identifier, purpose, otp_hash, expires_at)
        )

        # Log OTP to console in development mode
        if Settings.ALLOW_CONSOLE_OTP:
            print("\n" + "=" * 50)
            print(f" [TECHTREND OTP] Destination: {identifier}")
            print(f" [TECHTREND OTP] Code: {raw_otp}")
            print(f" [TECHTREND OTP] Expires: {expires_at}")
            print("=" * 50 + "\n")

        return {
            "success": True,
            "message": f"6-digit OTP sent to {identifier}.",
            "otp_debug": raw_otp if Settings.ALLOW_CONSOLE_OTP else None
        }

    @classmethod
    def verify_otp(cls, identifier: str, raw_otp: str) -> dict:
        """Verify candidate 6-digit OTP."""
        identifier = identifier.strip().lower()
        candidate_hash = cls._hash_otp(raw_otp.strip())
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Fetch latest active OTP for identifier
        record = Database.query_one(
            """
            SELECT * FROM otp_codes 
            WHERE identifier = %s AND consumed_at IS NULL 
            ORDER BY id DESC LIMIT 1
            """,
            (identifier,)
        )

        if not record:
            return {"success": False, "message": "No active OTP found. Please request a new code."}

        # Check expiry
        expires_at = str(record.get("expires_at"))
        if expires_at < now_str:
            return {"success": False, "message": "OTP has expired. Please request a new code."}

        # Check attempts
        attempts = record.get("attempts", 0)
        if attempts >= Settings.OTP_MAX_ATTEMPTS:
            return {"success": False, "message": "Maximum verification attempts exceeded. Request a new OTP."}

        # Validate hash match
        if record.get("otp_hash") != candidate_hash:
            # Increment attempts
            Database.execute(
                "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = %s",
                (record["id"],)
            )
            remaining = Settings.OTP_MAX_ATTEMPTS - (attempts + 1)
            return {"success": False, "message": f"Invalid OTP code. {remaining} attempt(s) remaining."}

        # Mark OTP as consumed
        Database.execute(
            "UPDATE otp_codes SET consumed_at = %s WHERE id = %s",
            (now_str, record["id"])
        )

        return {"success": True, "message": "OTP verified successfully."}
