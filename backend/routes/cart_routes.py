from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from backend.models.cart import Cart

cart_bp = Blueprint("cart", __name__)


def _get_current_user_id():
    return session.get("user_id")


@cart_bp.route("/cart")
def cart_page():
    user_id = _get_current_user_id()
    coupon_code = request.args.get("coupon") or session.get("applied_coupon")
    
    if not user_id:
        return render_template("cart.html", cart=None, is_logged_in=False)
    
    cart_details = Cart.get_cart_details(user_id, coupon_code=coupon_code)
    if cart_details["coupon_code"]:
        session["applied_coupon"] = cart_details["coupon_code"]
    elif coupon_code and not cart_details["coupon_code"]:
        session.pop("applied_coupon", None)

    return render_template("cart.html", cart=cart_details, is_logged_in=True)


@cart_bp.route("/api/cart")
def api_get_cart():
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({"items": [], "total_items_count": 0, "subtotal": 0, "final_total": 0})
    
    coupon_code = session.get("applied_coupon")
    cart_details = Cart.get_cart_details(user_id, coupon_code=coupon_code)
    return jsonify(cart_details)


@cart_bp.route("/api/cart/add", methods=["POST"])
def api_add_to_cart():
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Please login to add items to your cart.", "redirect_url": url_for("auth.login_page")}), 401

    data = request.get_json() or {}
    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))

    if not product_id:
        return jsonify({"success": False, "message": "Product ID required."}), 400

    res = Cart.add_item(user_id, int(product_id), quantity)
    if res["success"]:
        cart_details = Cart.get_cart_details(user_id, session.get("applied_coupon"))
        res["total_items_count"] = cart_details["total_items_count"]
    return jsonify(res)


@cart_bp.route("/api/cart/update", methods=["POST"])
def api_update_cart_item():
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    item_id = data.get("item_id")
    quantity = int(data.get("quantity", 1))

    res = Cart.update_item_quantity(user_id, int(item_id), quantity)
    cart_details = Cart.get_cart_details(user_id, session.get("applied_coupon"))
    res["cart"] = cart_details
    return jsonify(res)


@cart_bp.route("/api/cart/remove", methods=["POST"])
def api_remove_cart_item():
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    item_id = data.get("item_id")

    res = Cart.remove_item(user_id, int(item_id))
    cart_details = Cart.get_cart_details(user_id, session.get("applied_coupon"))
    res["cart"] = cart_details
    return jsonify(res)


@cart_bp.route("/api/cart/apply-coupon", methods=["POST"])
def api_apply_coupon():
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "Please login to apply coupon."}), 401

    data = request.get_json() or {}
    coupon_code = data.get("coupon_code", "").strip().upper()

    if not coupon_code:
        session.pop("applied_coupon", None)
        cart_details = Cart.get_cart_details(user_id)
        return jsonify({"success": True, "message": "Coupon removed.", "cart": cart_details})

    cart_details = Cart.get_cart_details(user_id, coupon_code=coupon_code)
    if cart_details["coupon_code"]:
        session["applied_coupon"] = cart_details["coupon_code"]
        return jsonify({"success": True, "message": f"Coupon '{cart_details['coupon_code']}' applied successfully!", "cart": cart_details})
    else:
        return jsonify({"success": False, "message": "Invalid or expired coupon code, or minimum order amount not met."}), 400
