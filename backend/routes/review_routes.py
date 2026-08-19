from flask import Blueprint, request, jsonify, session, url_for, render_template, redirect, flash
from backend.models.review import Review
from backend.models.user import User

review_bp = Blueprint("review", __name__)


@review_bp.route("/profile", methods=["GET", "POST"])
def user_profile_page():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please login to access your profile.", "info")
        return redirect(url_for("auth.login_page"))

    user = User.get_by_id(user_id)
    addresses = User.get_addresses(user_id)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        User.update_profile(user_id=user_id, full_name=full_name, phone=phone, email=email)
        session["full_name"] = full_name
        flash("Profile updated successfully!", "success")
        return redirect(url_for("review.user_profile_page"))

    return render_template("profile.html", user=user, addresses=addresses)


@review_bp.route("/api/address/add", methods=["POST"])
def api_add_address():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip()
    address_line = data.get("address_line", "").strip()
    city = data.get("city", "").strip()
    state = data.get("state", "").strip()
    pincode = data.get("pincode", "").strip()
    is_default = 1 if data.get("is_default") else 0

    if not full_name or not address_line or not city or not state or not pincode:
        return jsonify({"success": False, "message": "Please fill in all address fields."}), 400

    addr_id = User.save_address(user_id, full_name, phone, address_line, city, state, pincode, is_default)
    return jsonify({"success": True, "message": "Address saved successfully.", "address_id": addr_id})


@review_bp.route("/api/reviews/submit", methods=["POST"])
def api_submit_review():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Please login to write a review.", "redirect_url": url_for("auth.login_page")}), 401

    data = request.get_json() or {}
    product_id = data.get("product_id")
    rating = int(data.get("rating", 5))
    review_text = data.get("review_text", "").strip()

    if not product_id:
        return jsonify({"success": False, "message": "Product ID required."}), 400

    Review.save_review(user_id, int(product_id), rating, review_text)
    return jsonify({"success": True, "message": "Thank you! Your review has been published."})


@review_bp.route("/api/reviews/delete", methods=["POST"])
def api_delete_review():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    review_id = data.get("review_id")

    Review.delete_review(int(review_id), user_id)
    return jsonify({"success": True, "message": "Review deleted."})
