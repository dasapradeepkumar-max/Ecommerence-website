from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..models import auth_repo, cart_repo, order_repo, product_repo
from ..services.pricing_service import apply_coupon, delivery_fee, discounted_price
from ..utils.decorators import login_required, profile_required
from ..utils.validators import valid_pincode

shop_bp = Blueprint("shop", __name__)


@shop_bp.get("/home")
@login_required
@profile_required
def home():
    user, addresses = auth_repo.get_user_profile(session["user_id"])
    categories = product_repo.list_categories()
    featured, trending, recommended = product_repo.get_featured_sections()
    return render_template(
        "home.html",
        user=user,
        addresses=addresses,
        categories=categories,
        featured=featured,
        trending=trending,
        recommended=recommended,
        discounted_price=discounted_price,
    )


@shop_bp.get("/products")
@login_required
@profile_required
def products():
    filters = {
        "search": request.args.get("search", "").strip(),
        "category": request.args.get("category", "").strip(),
        "min_price": request.args.get("min_price", "").strip(),
        "max_price": request.args.get("max_price", "").strip(),
        "rating": request.args.get("rating", "").strip(),
        "sort": request.args.get("sort", "latest").strip(),
    }
    categories = product_repo.list_categories()
    product_list = product_repo.list_products(filters)
    return render_template(
        "products.html",
        products=product_list,
        categories=categories,
        filters=filters,
        discounted_price=discounted_price,
    )


@shop_bp.get("/products/<slug>")
@login_required
@profile_required
def product_detail(slug):
    data = product_repo.get_product_by_slug(slug)
    if not data:
        flash("Product not found", "error")
        return redirect(url_for("shop.products"))
    return render_template("product_detail.html", data=data, discounted_price=discounted_price)


@shop_bp.post("/cart/add")
@login_required
@profile_required
def add_to_cart():
    product_id = int(request.form.get("product_id", "0"))
    quantity = max(int(request.form.get("quantity", "1")), 1)
    cart_repo.add_to_cart(session["user_id"], product_id, quantity)
    flash("Product added to cart", "success")
    next_url = request.form.get("next") or url_for("shop.cart")
    return redirect(next_url)


@shop_bp.get("/cart")
@login_required
@profile_required
def cart():
    items = cart_repo.get_cart(session["user_id"])
    coupon_code = session.get("coupon_code")
    coupon = order_repo.get_coupon_by_code(coupon_code) if coupon_code else None

    subtotal = sum(discounted_price(item["price"], item["discount_percent"]) * item["quantity"] for item in items)
    coupon_discount = apply_coupon(subtotal, coupon)
    delivery = delivery_fee(subtotal - coupon_discount)
    final_total = round(subtotal - coupon_discount + delivery, 2)

    return render_template(
        "cart.html",
        items=items,
        coupon_code=coupon_code,
        totals={
            "subtotal": round(subtotal, 2),
            "coupon_discount": round(coupon_discount, 2),
            "delivery_fee": round(delivery, 2),
            "final_total": final_total,
        },
        discounted_price=discounted_price,
    )


@shop_bp.post("/cart/update")
@login_required
@profile_required
def update_cart():
    item_id = int(request.form.get("item_id", "0"))
    quantity = int(request.form.get("quantity", "1"))
    cart_repo.update_cart_item(session["user_id"], item_id, quantity)
    return redirect(url_for("shop.cart"))


@shop_bp.post("/cart/coupon")
@login_required
@profile_required
def apply_cart_coupon():
    code = request.form.get("coupon_code", "").strip().upper()
    if not code:
        session.pop("coupon_code", None)
        flash("Coupon removed", "success")
        return redirect(url_for("shop.cart"))

    coupon = order_repo.get_coupon_by_code(code)
    if not coupon:
        flash("Invalid coupon", "error")
        return redirect(url_for("shop.cart"))

    session["coupon_code"] = code
    flash("Coupon applied", "success")
    return redirect(url_for("shop.cart"))


@shop_bp.get("/wishlist")
@login_required
@profile_required
def wishlist():
    items = cart_repo.get_wishlist(session["user_id"])
    return render_template("wishlist.html", items=items, discounted_price=discounted_price)


@shop_bp.post("/wishlist/add")
@login_required
@profile_required
def wishlist_add():
    product_id = int(request.form.get("product_id", "0"))
    cart_repo.add_to_wishlist(session["user_id"], product_id)
    flash("Added to wishlist", "success")
    return redirect(request.form.get("next") or url_for("shop.wishlist"))


@shop_bp.post("/wishlist/remove")
@login_required
@profile_required
def wishlist_remove():
    product_id = int(request.form.get("product_id", "0"))
    cart_repo.remove_from_wishlist(session["user_id"], product_id)
    flash("Removed from wishlist", "success")
    return redirect(request.form.get("next") or url_for("shop.wishlist"))


@shop_bp.route("/checkout", methods=["GET", "POST"])
@login_required
@profile_required
def checkout():
    user_id = session["user_id"]
    items = cart_repo.get_cart(user_id)
    if not items:
        flash("Your cart is empty", "error")
        return redirect(url_for("shop.products"))

    addresses = order_repo.list_user_addresses(user_id)

    subtotal = sum(discounted_price(item["price"], item["discount_percent"]) * item["quantity"] for item in items)
    coupon = order_repo.get_coupon_by_code(session.get("coupon_code", "")) if session.get("coupon_code") else None
    coupon_discount = apply_coupon(subtotal, coupon)
    delivery = delivery_fee(subtotal - coupon_discount)
    totals = {
        "subtotal": round(subtotal, 2),
        "coupon_discount": round(coupon_discount, 2),
        "delivery_fee": round(delivery, 2),
        "final_total": round(subtotal - coupon_discount + delivery, 2),
    }

    if request.method == "GET":
        return render_template(
            "checkout.html",
            items=items,
            addresses=addresses,
            totals=totals,
            discounted_price=discounted_price,
        )

    address_id = request.form.get("address_id", "")
    payment_method = request.form.get("payment_method", "COD")

    if request.form.get("new_address") == "1":
        address_line = request.form.get("address_line", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        pincode = request.form.get("pincode", "").strip()
        if not all([address_line, city, state, pincode]) or not valid_pincode(pincode):
            flash("Please provide a valid delivery address", "error")
            return redirect(url_for("shop.checkout"))
        address_id = order_repo.add_address(user_id, address_line, city, state, pincode, is_default=True)
    else:
        if not address_id:
            flash("Select a delivery address", "error")
            return redirect(url_for("shop.checkout"))
        address_id = int(address_id)

    order_id = order_repo.create_order(user_id, address_id, payment_method, totals)
    if not order_id:
        flash("Unable to create order", "error")
        return redirect(url_for("shop.cart"))

    session.pop("coupon_code", None)
    return redirect(url_for("shop.order_confirmation", order_id=order_id))


@shop_bp.get("/orders/<int:order_id>/confirmation")
@login_required
@profile_required
def order_confirmation(order_id):
    data = order_repo.get_order(order_id, session["user_id"])
    if not data:
        flash("Order not found", "error")
        return redirect(url_for("shop.orders"))

    eta = (datetime.utcnow() + timedelta(days=5)).strftime("%d %b %Y")
    return render_template("order_confirmation.html", data=data, eta=eta)


@shop_bp.get("/orders")
@login_required
@profile_required
def orders():
    orders_list = order_repo.list_orders_for_user(session["user_id"])
    return render_template("orders.html", orders=orders_list)


@shop_bp.get("/orders/<int:order_id>")
@login_required
@profile_required
def order_detail(order_id):
    data = order_repo.get_order(order_id, session["user_id"])
    if not data:
        flash("Order not found", "error")
        return redirect(url_for("shop.orders"))
    return render_template("order_detail.html", data=data)


@shop_bp.post("/orders/<int:order_id>/cancel")
@login_required
@profile_required
def cancel_order(order_id):
    if order_repo.cancel_order(order_id, session["user_id"]):
        flash("Order cancelled", "success")
    else:
        flash("Order cannot be cancelled now", "error")
    return redirect(url_for("shop.order_detail", order_id=order_id))


@shop_bp.post("/orders/<int:order_id>/reorder")
@login_required
@profile_required
def reorder(order_id):
    order_repo.reorder(order_id, session["user_id"])
    flash("Items moved to cart", "success")
    return redirect(url_for("shop.cart"))


@shop_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        if not full_name:
            flash("Full name cannot be empty", "error")
            return redirect(url_for("shop.profile"))

        user, addresses = auth_repo.get_user_profile(user_id)
        selected_address = addresses[0] if addresses else None
        if selected_address:
            auth_repo.save_profile(
                user_id,
                full_name,
                selected_address["address_line"],
                selected_address["city"],
                selected_address["state"],
                selected_address["pincode"],
            )
        else:
            auth_repo.save_profile(user_id, full_name, "", "", "", "000000")
        flash("Profile updated", "success")
        return redirect(url_for("shop.profile"))

    user, addresses = auth_repo.get_user_profile(user_id)
    return render_template("profile.html", user=user, addresses=addresses)


@shop_bp.post("/products/<slug>/review")
@login_required
@profile_required
def add_review(slug):
    data = product_repo.get_product_by_slug(slug)
    if not data:
        flash("Product not found", "error")
        return redirect(url_for("shop.products"))

    product_id = data["product"]["id"]
    if not order_repo.user_can_review_product(session["user_id"], product_id):
        flash("You can review only delivered products you purchased", "error")
        return redirect(url_for("shop.product_detail", slug=slug))

    rating = max(1, min(int(request.form.get("rating", "5")), 5))
    review_text = request.form.get("review_text", "").strip()
    product_repo.upsert_review(session["user_id"], product_id, rating, review_text)
    flash("Review saved", "success")
    return redirect(url_for("shop.product_detail", slug=slug))


@shop_bp.post("/reviews/<int:review_id>/delete")
@login_required
@profile_required
def delete_review(review_id):
    slug = request.form.get("slug", "")
    if product_repo.delete_review(review_id, session["user_id"]):
        flash("Review deleted", "success")
    else:
        flash("Unable to delete review", "error")
    return redirect(url_for("shop.product_detail", slug=slug))
