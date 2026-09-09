import os
import time
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from backend.models.admin import Admin
from backend.models.product import Product
from backend.models.order import Order
from backend.models.database import Database
from config.settings import Settings

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
    users = Admin.get_all_users()

    return render_template(
        "admin/dashboard.html",
        kpis=kpis,
        low_stock=low_stock,
        products=products,
        categories=categories,
        orders=orders,
        coupons=coupons,
        users=users,
        statuses=Order.STATUS_TIMELINE
    )


@admin_bp.route("/api/users", methods=["GET"])
def api_get_users():
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    users = Admin.get_all_users()
    return jsonify({"success": True, "users": users, "total_count": len(users)})



@admin_bp.route("/api/products", methods=["GET"])
def api_get_products():
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    category_id = request.args.get("category_id")
    status = request.args.get("status", "all")
    stock_status = request.args.get("stock_status", "all")
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "newest")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))

    result = Product.get_admin_products(
        category_id=category_id,
        status=status,
        stock_status=stock_status,
        search=search,
        sort_by=sort_by,
        page=page,
        limit=limit
    )

    return jsonify({"success": True, **result})


@admin_bp.route("/api/products/<int:product_id>", methods=["GET"])
def api_get_product_detail(product_id):
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    prod = Product.get_by_id(product_id)
    if not prod:
        return jsonify({"success": False, "message": "Product not found."}), 404

    return jsonify({"success": True, "product": prod})


@admin_bp.route("/api/products/upload-image", methods=["POST"])
def api_upload_product_image():
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if "image" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No selected file."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in Settings.ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"success": False, "message": f"Invalid file extension. Allowed: {', '.join(Settings.ALLOWED_IMAGE_EXTENSIONS)}"}), 400

    # Ensure upload directory exists
    upload_dir = Settings.UPLOAD_FOLDER
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"prod_{int(time.time())}_{secure_filename(file.filename)}"
    filepath = upload_dir / filename
    file.save(str(filepath))

    public_url = f"/static/images/uploads/{filename}"
    return jsonify({"success": True, "image_url": public_url, "message": "Image uploaded successfully."})


@admin_bp.route("/api/products/save", methods=["POST"])
def api_save_product():
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    product_id = data.get("product_id")
    category_id_raw = data.get("category_id")
    name = str(data.get("name", "")).strip()
    slug_raw = str(data.get("slug", "")).strip()
    short_description = str(data.get("short_description", "")).strip()
    description = str(data.get("description", "")).strip()
    specifications = str(data.get("specifications", "")).strip()
    
    # Validations
    if not name:
        return jsonify({"success": False, "message": "Product name is required."}), 400

    if not category_id_raw or not str(category_id_raw).isdigit():
        return jsonify({"success": False, "message": "Valid category selection is required."}), 400
    category_id = int(category_id_raw)

    try:
        price = float(data.get("price", 0))
        if price < 0:
            return jsonify({"success": False, "message": "Original price cannot be negative."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid price value."}), 400

    try:
        discount_percent = float(data.get("discount_percent", 0))
        if discount_percent < 0 or discount_percent > 100:
            return jsonify({"success": False, "message": "Discount percentage must be between 0% and 100%."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid discount percentage."}), 400

    try:
        stock = int(data.get("stock", 0))
        if stock < 0:
            return jsonify({"success": False, "message": "Stock quantity cannot be negative."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid stock quantity."}), 400

    # Auto slug generation & unique slug check
    slug = slug_raw if slug_raw else name.lower().replace(" ", "-").replace("/", "-")
    import re
    slug = re.sub(r'[^a-z0-9\-]', '', slug.lower())
    if not slug:
        slug = f"prod-{int(time.time())}"

    # Ensure slug uniqueness
    base_slug = slug
    counter = 1
    while True:
        existing = Database.query_one("SELECT id FROM products WHERE slug = %s AND (%s IS NULL OR id != %s)", (slug, product_id, product_id))
        if not existing:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    is_featured = 1 if data.get("is_featured") else 0
    is_trending = 1 if data.get("is_trending") else 0
    is_active = 1 if data.get("is_active", True) else 0
    image_urls = data.get("image_urls", [])
    if isinstance(image_urls, str):
        image_urls = [image_urls]

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
        product_id=product_id,
        is_active=is_active
    )

    action_str = "updated" if product_id else "created"
    return jsonify({"success": True, "message": f"Product '{name}' {action_str} successfully.", "product_id": pid})


@admin_bp.route("/api/products/toggle-status", methods=["POST"])
def api_toggle_product_status():
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    product_id = data.get("product_id")
    is_active = data.get("is_active", True)

    if not product_id:
        return jsonify({"success": False, "message": "Missing product ID."}), 400

    Product.toggle_status(int(product_id), is_active)
    status_str = "activated" if is_active else "deactivated"
    return jsonify({"success": True, "message": f"Product status set to {status_str}."})


@admin_bp.route("/api/products/delete", methods=["POST"])
def api_delete_product():
    if not _is_admin():
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    product_id = data.get("product_id")
    permanent = data.get("permanent", False)

    if not product_id:
        return jsonify({"success": False, "message": "Missing product ID."}), 400

    Product.delete_product(int(product_id), permanent=permanent)
    msg = "Product permanently deleted." if permanent else "Product deactivated successfully."
    return jsonify({"success": True, "message": msg})



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
