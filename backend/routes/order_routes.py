from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from backend.models.cart import Cart
from backend.models.user import User
from backend.models.order import Order
from backend.services.payment_service import PaymentGatewaySandbox

order_bp = Blueprint("order", __name__)


def _login_required():
    return session.get("user_id")


@order_bp.route("/checkout")
def checkout_page():
    user_id = _login_required()
    if not user_id:
        flash("Please login to proceed to checkout.", "info")
        return redirect(url_for("auth.login_page"))

    user = User.get_by_id(user_id)
    if not user.get("is_profile_complete"):
        flash("Please complete your profile before checking out.", "info")
        return redirect(url_for("auth.create_profile_page"))

    cart_summary = Cart.get_cart_details(user_id, coupon_code=session.get("applied_coupon"))
    if not cart_summary["items"]:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart.cart_page"))

    addresses = User.get_addresses(user_id)
    return render_template("checkout.html", cart=cart_summary, addresses=addresses, user=user)


@order_bp.route("/api/checkout/process", methods=["POST"])
def api_process_checkout():
    user_id = _login_required()
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    address_id = data.get("address_id")
    payment_method = data.get("payment_method", "").upper()
    upi_id = data.get("upi_id", "").strip()
    card_number = data.get("card_number", "").strip()
    card_expiry = data.get("card_expiry", "").strip()
    card_cvv = data.get("card_cvv", "").strip()
    new_address = data.get("new_address")

    # Save new address if passed
    if not address_id and new_address:
        address_id = User.save_address(
            user_id=user_id,
            full_name=new_address.get("full_name"),
            phone=new_address.get("phone"),
            address_line=new_address.get("address_line"),
            city=new_address.get("city"),
            state=new_address.get("state"),
            pincode=new_address.get("pincode"),
            is_default=1
        )

    if not address_id:
        return jsonify({"success": False, "message": "Please select or add a valid delivery address."}), 400

    if payment_method not in ["UPI", "CARD", "COD"]:
        return jsonify({"success": False, "message": "Please select a valid payment method."}), 400

    cart_summary = Cart.get_cart_details(user_id, coupon_code=session.get("applied_coupon"))
    amount = cart_summary["final_total"]

    # Payment sandbox simulation
    if payment_method == "UPI":
        pay_res = PaymentGatewaySandbox.process_upi_payment(upi_id, amount)
    elif payment_method == "CARD":
        pay_res = PaymentGatewaySandbox.process_card_payment(card_number, card_expiry, card_cvv, amount)
    else: # COD
        pay_res = PaymentGatewaySandbox.process_cod_payment(amount)

    if not pay_res.get("success"):
        return jsonify(pay_res), 400

    # Create Order
    order_res = Order.create_order(
        user_id=user_id,
        address_id=int(address_id),
        payment_method=payment_method,
        coupon_code=session.get("applied_coupon")
    )

    if order_res.get("success"):
        session.pop("applied_coupon", None)
        order_res["redirect_url"] = url_for("order.order_confirmation_page", order_number=order_res["order_number"])

    return jsonify(order_res)


@order_bp.route("/order-confirmation/<order_number>")
def order_confirmation_page(order_number):
    user_id = _login_required()
    if not user_id:
        return redirect(url_for("auth.login_page"))

    orders = Order.get_user_orders(user_id)
    target_order = next((o for o in orders if o["order_number"] == order_number), None)
    if not target_order:
        flash("Order not found.", "error")
        return redirect(url_for("product.home_page"))

    return render_template("order_confirmation.html", order=target_order)


@order_bp.route("/my-orders")
def my_orders_page():
    user_id = _login_required()
    if not user_id:
        flash("Please login to view your orders.", "info")
        return redirect(url_for("auth.login_page"))

    orders = Order.get_user_orders(user_id)
    return render_template("orders.html", orders=orders)


@order_bp.route("/api/orders/cancel", methods=["POST"])
def api_cancel_order():
    user_id = _login_required()
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    order_id = data.get("order_id")
    if not order_id:
        return jsonify({"success": False, "message": "Order ID required."}), 400

    res = Order.cancel_order(int(order_id), user_id)
    return jsonify(res)


@order_bp.route("/api/orders/reorder", methods=["POST"])
def api_reorder():
    user_id = _login_required()
    if not user_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    order_id = data.get("order_id")

    res = Order.reorder(int(order_id), user_id)
    res["redirect_url"] = url_for("cart.cart_page")
    return jsonify(res)
