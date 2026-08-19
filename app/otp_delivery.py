import smtplib
from email.message import EmailMessage

from flask import current_app
from twilio.rest import Client


def _send_email_otp(receiver_email: str, otp: str) -> bool:
    cfg = current_app.config
    if not all([cfg["SMTP_HOST"], cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"], cfg["EMAIL_FROM"]]):
        return False

    msg = EmailMessage()
    msg["Subject"] = "Your E-Commerce Login OTP"
    msg["From"] = cfg["EMAIL_FROM"]
    msg["To"] = receiver_email
    msg.set_content(f"Your OTP for login is {otp}. It expires in {cfg['OTP_EXPIRY_MINUTES']} minutes.")

    with smtplib.SMTP_SSL(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=20) as server:
        server.login(cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"])
        server.send_message(msg)
    return True


def _send_sms_otp(receiver_phone: str, otp: str) -> bool:
    cfg = current_app.config
    if not all([cfg["TWILIO_ACCOUNT_SID"], cfg["TWILIO_AUTH_TOKEN"], cfg["TWILIO_PHONE_NUMBER"]]):
        return False

    client = Client(cfg["TWILIO_ACCOUNT_SID"], cfg["TWILIO_AUTH_TOKEN"])
    client.messages.create(
        body=f"Your OTP for login is {otp}. Expires in {cfg['OTP_EXPIRY_MINUTES']} minutes.",
        from_=cfg["TWILIO_PHONE_NUMBER"],
        to=receiver_phone,
    )
    return True


def send_otp(identifier: str, channel: str, otp: str) -> tuple[bool, str]:
    try:
        if channel == "email":
            if _send_email_otp(identifier, otp):
                return True, "OTP sent to your email."
        elif channel == "phone":
            if _send_sms_otp(identifier, otp):
                return True, "OTP sent to your phone number."
    except Exception:
        return False, "Could not send OTP. Please try again."

    if current_app.config["ALLOW_CONSOLE_OTP"]:
        print(f"[DEV OTP] Identifier: {identifier}, OTP: {otp}")
        return True, "OTP sent (development mode). Check server logs."

    return False, "OTP service is not configured."
