from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from backend.models.admin import Admin
from backend.models.product import Product
from backend.models.order import Order
from backend.models.database import Database

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _is_admin():
    return session.get("is_admin") is True


@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if _is_admin():
        return redirect(url_for("admin.admin_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        admin_user = Admin.verify_login(email, password)
        if admin_user:
            session["is_admin"] = True
            session["admin_name"] = admin_user["name"]
            session["admin_email"] = admin_user["email"]
            flash(f"Welcome back, {admin_user['name']}!", "success")
            return redirect(url_for("admin.admin_dashboard"))
        else:
            flash("Invalid administrator credentials.", "error")

    return render_template("admin/login.html")


@admin_bp.route("/dashboard")
def admin_dashboard():
    if not _is_admin():
        flash("Admin authentication required.", "warning")
        return redirect(url_for("admin.admin_login"))

    kpis = Admin.get_kpis()
    low_stock = Admin.get_low_stock_products()
    products = Product.get_all(limit=200)
    categories = Product.get_categories()
    orders = Admin.get_all_orders()
    coupons = Admin.get_coupons()

    return render_template(
        "admin/dashboard.html",
        kpis=kpis,
        low_stock=low_stock,
        products=products,
        categories=categories,
        orders=orders,
        coupons=coupons,
        statuses=Order.STATUS_TIMELINE
    )


@admin_bp.route("/api/products/save", methods=["POST"])
def api_save_product():
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    product_id = data.get("product_id")
    category_id = int(data.get("category_id"))
    name = data.get("name", "").strip()
    slug = data.get("slug", "").strip() or name.lower().replace(" ", "-")
    short_description = data.get("short_description", "").strip()
    description = data.get("description", "").strip()
    specifications = data.get("specifications", "").strip()
    price = float(data.get("price", 0))
    discount_percent = float(data.get("discount_percent", 0))
    stock = int(data.get("stock", 0))
    is_featured = 1 if data.get("is_featured") else 0
    is_trending = 1 if data.get("is_trending") else 0
    image_urls = data.get("image_urls", [])

    if not name or not price:
        return jsonify({"success": False, "message": "Product name and price are required."}), 400

    pid = Product.save_product(
        category_id=category_id,
        name=name,
        slug=slug,
        short_description=short_description,
        description=description,
        specifications=specifications,
        price=price,
        discount_percent=discount_percent,
        stock=stock,
        is_featured=is_featured,
        is_trending=is_trending,
        image_urls=image_urls,
        product_id=product_id
    )

    return jsonify({"success": True, "message": "Product saved successfully.", "product_id": pid})


@admin_bp.route("/api/products/delete", methods=["POST"])
def api_delete_product():
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    product_id = data.get("product_id")

    Product.delete_product(int(product_id))
    return jsonify({"success": True, "message": "Product deactivated successfully."})


@admin_bp.route("/api/orders/update-status", methods=["POST"])
def api_update_order_status():
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    order_id = data.get("order_id")
    status = data.get("status")

    res = Order.update_order_status(int(order_id), status)
    return jsonify(res)


@admin_bp.route("/api/coupons/save", methods=["POST"])
def api_save_coupon():
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    coupon_id = data.get("coupon_id")
    code = data.get("code", "").strip()
    discount_type = data.get("discount_type", "percent")
    discount_value = float(data.get("discount_value", 0))
    min_order_amount = float(data.get("min_order_amount", 0))
    max_discount = float(data.get("max_discount")) if data.get("max_discount") else None
    is_active = 1 if data.get("is_active", True) else 0

    Admin.save_coupon(code, discount_type, discount_value, min_order_amount, max_discount, is_active, coupon_id)
    return jsonify({"success": True, "message": "Coupon saved."})


@admin_bp.route("/api/coupons/delete", methods=["POST"])
def api_delete_coupon():
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    coupon_id = data.get("coupon_id")

    Admin.delete_coupon(int(coupon_id))
    return jsonify({"success": True, "message": "Coupon deleted."})


@admin_bp.route("/logout")
def admin_logout():
    session.pop("is_admin", None)
    session.pop("admin_name", None)
    session.pop("admin_email", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("admin.admin_login"))
