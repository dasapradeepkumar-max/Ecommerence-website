from datetime import datetime, timedelta, timezone

from flask import current_app

from .database import get_connection


def find_user_by_identifier(identifier):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email = %s OR phone = %s", (identifier, identifier))
        row = cur.fetchone()
        cur.close()
        return row


def create_user(identifier, channel):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        if channel == "email":
            cur.execute("INSERT INTO users (email) VALUES (%s)", (identifier,))
        else:
            cur.execute("INSERT INTO users (phone) VALUES (%s)", (identifier,))
        user_id = cur.lastrowid
        conn.commit()
        cur.close()
        return user_id


def store_otp(identifier, purpose, otp_hash):
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=current_app.config["OTP_EXPIRY_MINUTES"])
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO otp_codes (identifier, purpose, otp_hash, expires_at)
            VALUES (%s, %s, %s, %s)
            """,
            (identifier, purpose, otp_hash, expires_at.replace(tzinfo=None)),
        )
        conn.commit()
        cur.close()


def latest_active_otp(identifier):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT * FROM otp_codes
            WHERE identifier = %s AND consumed_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (identifier,),
        )
        row = cur.fetchone()
        cur.close()
        return row


def count_recent_otp(identifier, minutes=15):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM otp_codes
            WHERE identifier = %s AND created_at >= (UTC_TIMESTAMP() - INTERVAL %s MINUTE)
            """,
            (identifier, minutes),
        )
        count = cur.fetchone()[0]
        cur.close()
        return count


def increment_otp_attempt(otp_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE otp_codes SET attempts = attempts + 1 WHERE id = %s", (otp_id,))
        conn.commit()
        cur.close()


def consume_otp(otp_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE otp_codes SET consumed_at = UTC_TIMESTAMP() WHERE id = %s", (otp_id,))
        conn.commit()
        cur.close()


def touch_last_login(user_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET last_login = UTC_TIMESTAMP() WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()


def save_profile(user_id, full_name, address_line, city, state, pincode):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE users SET full_name = %s, is_profile_complete = 1 WHERE id = %s", (full_name, user_id))
        cur.execute(
            """
            INSERT INTO addresses (user_id, address_line, city, state, pincode, is_default)
            VALUES (%s, %s, %s, %s, %s, 1)
            ON DUPLICATE KEY UPDATE
                address_line = VALUES(address_line),
                city = VALUES(city),
                state = VALUES(state),
                pincode = VALUES(pincode),
                is_default = VALUES(is_default)
            """,
            (user_id, address_line, city, state, pincode),
        )
        cur.execute("UPDATE addresses SET is_default = IF(id = LAST_INSERT_ID(id), 1, 0) WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()


def get_user_profile(user_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.execute("SELECT * FROM addresses WHERE user_id = %s ORDER BY is_default DESC, id DESC", (user_id,))
        addresses = cur.fetchall()
        cur.close()
        return user, addresses
