import smtplib
from email.message import EmailMessage

from flask import current_app
from twilio.rest import Client


def _send_email(receiver_email, otp):
    cfg = current_app.config
    if not all([cfg["SMTP_HOST"], cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"], cfg["EMAIL_FROM"]]):
        return False

    message = EmailMessage()
    message["Subject"] = "Your E-Commerce OTP"
    message["From"] = cfg["EMAIL_FROM"]
    message["To"] = receiver_email
    message.set_content(
        f"Your OTP is {otp}. It will expire in {cfg['OTP_EXPIRY_MINUTES']} minutes. Do not share this OTP."
    )

    with smtplib.SMTP_SSL(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=20) as smtp:
        smtp.login(cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"])
        smtp.send_message(message)

    return True


def _send_sms(receiver_phone, otp):
    cfg = current_app.config
    if not all([cfg["TWILIO_ACCOUNT_SID"], cfg["TWILIO_AUTH_TOKEN"], cfg["TWILIO_PHONE_NUMBER"]]):
        return False

    client = Client(cfg["TWILIO_ACCOUNT_SID"], cfg["TWILIO_AUTH_TOKEN"])
    client.messages.create(
        body=f"Your OTP is {otp}. It expires in {cfg['OTP_EXPIRY_MINUTES']} minutes.",
        from_=cfg["TWILIO_PHONE_NUMBER"],
        to=receiver_phone,
    )
    return True


def send_otp(identifier, channel, otp):
    try:
        if channel == "email" and _send_email(identifier, otp):
            return True, "OTP sent to your email"
        if channel == "phone" and _send_sms(identifier, otp):
            return True, "OTP sent to your phone"
    except Exception:
        return False, "Unable to send OTP right now"

    if current_app.config["ALLOW_CONSOLE_OTP"]:
        print(f"[DEV OTP] {identifier} => {otp}")
        return True, "OTP sent in dev mode. Check server logs"

    return False, "OTP provider is not configured"
