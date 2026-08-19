from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from backend.models.wishlist import Wishlist

wishlist_bp = Blueprint("wishlist", __name__)


def _login_required():
    return session.get("user_id")


@wishlist_bp.route("/wishlist")
def wishlist_page():
    user_id = _login_required()
    if not user_id:
        flash("Please login to view your wishlist.", "info")
        return redirect(url_for("auth.login_page"))

    items = Wishlist.get_user_wishlist(user_id)
    return render_template("wishlist.html", wishlist_items=items)


@wishlist_bp.route("/api/wishlist/add", methods=["POST"])
def api_add_wishlist():
    user_id = _login_required()
    if not user_id:
        return jsonify({"success": False, "message": "Please login to add to wishlist.", "redirect_url": url_for("auth.login_page")}), 401

    data = request.get_json() or {}
    product_id = data.get("product_id")

    res = Wishlist.add_item(user_id, int(product_id))
    return jsonify(res)


@wishlist_bp.route("/api/wishlist/remove", methods=["POST"])
def api_remove_wishlist():
    user_id = _login_required()
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    product_id = data.get("product_id")

    res = Wishlist.remove_item(user_id, int(product_id))
    return jsonify(res)


@wishlist_bp.route("/api/wishlist/move-to-cart", methods=["POST"])
def api_move_to_cart():
    user_id = _login_required()
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    product_id = data.get("product_id")

    res = Wishlist.move_to_cart(user_id, int(product_id))
    return jsonify(res)
