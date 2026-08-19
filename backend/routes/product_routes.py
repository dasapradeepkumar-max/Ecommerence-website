from flask import Blueprint, render_template, request, jsonify
from backend.models.product import Product
from backend.models.review import Review
from backend.models.cart import Cart

product_bp = Blueprint("product", __name__)


@product_bp.route("/")
def home_page():
    categories = Product.get_categories()
    featured_products = Product.get_featured(limit=6)
    trending_products = Product.get_trending(limit=6)
    recommended_products = Product.get_all(sort_by="rating", limit=6)
    
    return render_template(
        "home.html",
        categories=categories,
        featured_products=featured_products,
        trending_products=trending_products,
        recommended_products=recommended_products
    )


@product_bp.route("/products")
def products_page():
    category_id = request.args.get("category")
    search_q = request.args.get("q")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    min_rating = request.args.get("rating")
    sort_by = request.args.get("sort", "popular")

    categories = Product.get_categories()
    products = Product.get_all(
        category_id=category_id,
        search=search_q,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort_by=sort_by
    )

    selected_category = None
    if category_id:
        for c in categories:
            if str(c["id"]) == str(category_id):
                selected_category = c
                break

    return render_template(
        "products.html",
        products=products,
        categories=categories,
        selected_category=selected_category,
        search_q=search_q,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort_by=sort_by
    )


@product_bp.route("/category/<slug>")
def category_products_page(slug):
    cat = Product.get_category_by_slug(slug)
    if not cat:
        return render_template("products.html", products=[], categories=Product.get_categories())
    
    return products_page_with_cat_id(cat["id"])


def products_page_with_cat_id(cat_id):
    categories = Product.get_categories()
    products = Product.get_all(category_id=cat_id)
    selected_category = next((c for c in categories if c["id"] == cat_id), None)
    
    return render_template(
        "products.html",
        products=products,
        categories=categories,
        selected_category=selected_category,
        search_q="",
        min_price="",
        max_price="",
        min_rating="",
        sort_by="popular"
    )


@product_bp.route("/product/<identifier>")
def product_detail_page(identifier):
    if identifier.isdigit():
        product = Product.get_by_id(int(identifier))
    else:
        product = Product.get_by_slug(identifier)

    if not product:
        return render_template("404.html"), 404

    reviews = Review.get_by_product(product["id"])
    related_products = Product.get_all(category_id=product["category_id"], limit=4)
    related_products = [p for p in related_products if p["id"] != product["id"]]

    return render_template(
        "product_detail.html",
        product=product,
        reviews=reviews,
        related_products=related_products
    )


@product_bp.route("/api/products/search")
def api_search_products():
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    results = Product.get_all(search=query, limit=8)
    formatted = []
    for r in results:
        formatted.append({
            "id": r["id"],
            "name": r["name"],
            "price": float(r["price"]),
            "discounted_price": r["discounted_price"],
            "image": r["primary_image"],
            "category": r["category_name"]
        })
    return jsonify(formatted)
