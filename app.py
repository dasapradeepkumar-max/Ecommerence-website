import os
from flask import Flask, render_template
from config.settings import Settings
from backend.services.seed_service import init_and_seed_db

def create_app():
    app = Flask(
        __name__,
        template_folder=str(Settings.TEMPLATE_FOLDER),
        static_folder=str(Settings.STATIC_FOLDER)
    )
    app.config.from_object(Settings)

    # Initialize and seed database
    try:
        init_and_seed_db()
    except Exception as e:
        print(f"[App Init Warning] {e}")

    # Register Blueprints
    from backend.routes.auth_routes import auth_bp
    from backend.routes.product_routes import product_bp
    from backend.routes.cart_routes import cart_bp
    from backend.routes.order_routes import order_bp
    from backend.routes.wishlist_routes import wishlist_bp
    from backend.routes.review_routes import review_bp
    from backend.routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
