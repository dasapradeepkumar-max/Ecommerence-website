from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from backend.services.otp_service import OTPService
from backend.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET"])
def login_page():
    if session.get("user_id"):
        return redirect(url_for("product.home_page"))
    return render_template("login.html")


@auth_bp.route("/api/auth/send-otp", methods=["POST"])
def send_otp_api():
    data = request.get_json() or {}
    identifier = data.get("identifier", "").strip()

    if not identifier:
        return jsonify({"success": False, "message": "Phone number or email address is required."}), 400

    result = OTPService.generate_and_send_otp(identifier)
    return jsonify(result)


@auth_bp.route("/api/auth/verify-otp", methods=["POST"])
def verify_otp_api():
    data = request.get_json() or {}
    identifier = data.get("identifier", "").strip()
    otp = data.get("otp", "").strip()

    if not identifier or not otp:
        return jsonify({"success": False, "message": "Identifier and OTP code are required."}), 400

    verify_res = OTPService.verify_otp(identifier, otp)
    if not verify_res.get("success"):
        return jsonify(verify_res), 400

    # User creation / fetch
    ip_addr = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", request.user_agent.string if request.user_agent else None)
    user, is_new = User.create_or_get(identifier, ip_address=ip_addr, user_agent=user_agent)
    session["user_id"] = user["id"]
    session["user_identifier"] = identifier
    session["full_name"] = user.get("full_name") or "User"

    next_url = url_for("auth.create_profile_page") if not user.get("is_profile_complete") else url_for("product.home_page")

    return jsonify({
        "success": True,
        "message": "Login successful!",
        "is_new": is_new,
        "is_profile_complete": bool(user.get("is_profile_complete")),
        "redirect_url": next_url
    })


@auth_bp.route("/create-profile", methods=["GET", "POST"])
def create_profile_page():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login_page"))

    user = User.get_by_id(user_id)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        pincode = request.form.get("pincode", "").strip()

        if not full_name or not address or not city or not state or not pincode:
            flash("Please fill in all mandatory fields.", "error")
            return render_template("create_profile.html", user=user)

        User.update_profile(
            user_id=user_id,
            full_name=full_name,
            phone=phone or user.get("phone"),
            email=email or user.get("email"),
            address=address,
            city=city,
            state=state,
            pincode=pincode
        )

        session["full_name"] = full_name
        flash("Profile setup complete! Welcome to TechTrend.", "success")
        return redirect(url_for("product.home_page"))

    return render_template("create_profile.html", user=user)


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("product.home_page"))
