from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from .db import get_conn
from .otp_delivery import send_otp
from .security import generate_otp, hash_otp, verify_otp_hash
from .validators import is_valid_pincode, normalize_identifier

auth_bp = Blueprint("auth", __name__)


def _db_not_ready_response():
    flash("Database is not configured. Update your .env MySQL settings and restart the app.", "error")
    return redirect(url_for("auth.index"))


def _get_user_by_identifier(cursor, identifier: str):
    cursor.execute("SELECT * FROM users WHERE email = %s OR phone = %s", (identifier, identifier))
    return cursor.fetchone()


def _create_user(cursor, identifier: str, channel: str):
    if channel == "email":
        cursor.execute("INSERT INTO users (email) VALUES (%s)", (identifier,))
    else:
        cursor.execute("INSERT INTO users (phone) VALUES (%s)", (identifier,))
    return cursor.lastrowid


def _require_login():
    if not session.get("user_id"):
        flash("Please login first.", "error")
        return False
    return True


@auth_bp.get("/")
def index():
    if not current_app.config.get("DB_READY", True):
        return render_template("login.html", db_error=current_app.config.get("DB_INIT_ERROR", ""))

    user_id = session.get("user_id")
    if not user_id:
        return render_template("login.html")

    if not session.get("profile_complete"):
        return redirect(url_for("auth.create_profile"))

    return redirect(url_for("auth.home"))


@auth_bp.post("/request-otp")
def request_otp():
    if not current_app.config.get("DB_READY", True):
        return _db_not_ready_response()

    raw_identifier = request.form.get("identifier", "")
    mode = request.form.get("mode", "login")
    identifier, channel = normalize_identifier(raw_identifier)

    if identifier is None:
        flash("Enter a valid email or phone number.", "error")
        return redirect(url_for("auth.index"))

    if mode not in {"login", "register"}:
        mode = "login"

    otp = generate_otp(6)
    otp_hash = hash_otp(otp)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=current_app.config["OTP_EXPIRY_MINUTES"])

    with get_conn(current_app.config["MYSQL_DATABASE"]) as conn:
        cursor = conn.cursor(dictionary=True)
        user = _get_user_by_identifier(cursor, identifier)

        if mode == "register" and user:
            flash("Account already exists. Please login.", "error")
            cursor.close()
            return redirect(url_for("auth.index"))

        if mode == "login" and not user:
            mode = "register"

        cursor.execute(
            """
            INSERT INTO otp_codes (identifier, otp_hash, purpose, expires_at)
            VALUES (%s, %s, %s, %s)
            """,
            (identifier, otp_hash, mode, expires_at.replace(tzinfo=None)),
        )
        conn.commit()
        cursor.close()

    sent, message = send_otp(identifier, channel, otp)
    if not sent:
        flash(message, "error")
        return redirect(url_for("auth.index"))

    session["pending_identifier"] = identifier
    session["pending_channel"] = channel
    session["pending_mode"] = mode
    flash(message, "success")
    return redirect(url_for("auth.verify_otp"))


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if not current_app.config.get("DB_READY", True):
        return _db_not_ready_response()

    identifier = session.get("pending_identifier")
    mode = session.get("pending_mode", "login")
    channel = session.get("pending_channel")

    if not identifier:
        flash("Session expired. Request OTP again.", "error")
        return redirect(url_for("auth.index"))

    if request.method == "GET":
        return render_template("verify_otp.html", identifier=identifier)

    entered_otp = request.form.get("otp", "").strip()
    if len(entered_otp) != 6 or not entered_otp.isdigit():
        flash("Enter a valid 6-digit OTP.", "error")
        return redirect(url_for("auth.verify_otp"))

    now = datetime.utcnow()

    with get_conn(current_app.config["MYSQL_DATABASE"]) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM otp_codes
            WHERE identifier = %s AND purpose = %s AND consumed_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (identifier, mode),
        )
        otp_row = cursor.fetchone()

        if not otp_row:
            cursor.close()
            flash("No OTP found. Please request a new one.", "error")
            return redirect(url_for("auth.index"))

        if otp_row["expires_at"] < now:
            cursor.close()
            flash("OTP expired. Request a new OTP.", "error")
            return redirect(url_for("auth.index"))

        if otp_row["attempts"] >= current_app.config["OTP_MAX_ATTEMPTS"]:
            cursor.close()
            flash("Maximum OTP attempts reached. Request a new OTP.", "error")
            return redirect(url_for("auth.index"))

        if not verify_otp_hash(entered_otp, otp_row["otp_hash"]):
            cursor.execute("UPDATE otp_codes SET attempts = attempts + 1 WHERE id = %s", (otp_row["id"],))
            conn.commit()
            cursor.close()
            flash("Invalid OTP. Try again.", "error")
            return redirect(url_for("auth.verify_otp"))

        cursor.execute("UPDATE otp_codes SET consumed_at = UTC_TIMESTAMP() WHERE id = %s", (otp_row["id"],))
        user = _get_user_by_identifier(cursor, identifier)
        if not user:
            user_id = _create_user(cursor, identifier, channel)
            profile_complete = False
        else:
            user_id = user["id"]
            profile_complete = bool(user["is_profile_complete"])

        cursor.execute("UPDATE users SET last_login = UTC_TIMESTAMP() WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()

    session.pop("pending_identifier", None)
    session.pop("pending_mode", None)
    session.pop("pending_channel", None)
    session["user_id"] = user_id
    session["profile_complete"] = profile_complete

    flash("Login Successfully", "success")
    if profile_complete:
        return redirect(url_for("auth.home"))
    return redirect(url_for("auth.create_profile"))


@auth_bp.route("/create-profile", methods=["GET", "POST"])
def create_profile():
    if not current_app.config.get("DB_READY", True):
        return _db_not_ready_response()

    if not _require_login():
        return redirect(url_for("auth.index"))

    if session.get("profile_complete"):
        return redirect(url_for("auth.home"))

    if request.method == "GET":
        return render_template("create_profile.html")

    name = request.form.get("name", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    state = request.form.get("state", "").strip()
    pincode = request.form.get("pincode", "").strip()

    if not all([name, address, city, state, pincode]):
        flash("All profile fields are required.", "error")
        return redirect(url_for("auth.create_profile"))

    if not is_valid_pincode(pincode):
        flash("Pincode must be 6 digits.", "error")
        return redirect(url_for("auth.create_profile"))

    with get_conn(current_app.config["MYSQL_DATABASE"]) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO profiles (user_id, name, address, city, state, pincode)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                address = VALUES(address),
                city = VALUES(city),
                state = VALUES(state),
                pincode = VALUES(pincode)
            """,
            (session["user_id"], name, address, city, state, pincode),
        )
        cursor.execute(
            "UPDATE users SET is_profile_complete = 1, last_login = UTC_TIMESTAMP() WHERE id = %s",
            (session["user_id"],),
        )
        conn.commit()
        cursor.close()

    session["profile_complete"] = True
    flash("Profile saved successfully.", "success")
    return redirect(url_for("auth.home"))


@auth_bp.get("/home")
def home():
    if not current_app.config.get("DB_READY", True):
        return _db_not_ready_response()

    if not _require_login():
        return redirect(url_for("auth.index"))

    if not session.get("profile_complete"):
        return redirect(url_for("auth.create_profile"))

    with get_conn(current_app.config["MYSQL_DATABASE"]) as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT p.*, u.email, u.phone
            FROM profiles p
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = %s
            """,
            (session["user_id"],),
        )
        profile = cursor.fetchone()
        cursor.close()

    return render_template("home.html", profile=profile)


@auth_bp.get("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.index"))
