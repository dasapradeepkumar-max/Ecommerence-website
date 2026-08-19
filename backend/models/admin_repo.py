from flask import current_app

from .database import get_connection


def dashboard_stats():
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) AS total_users FROM users")
        users = cur.fetchone()["total_users"]
        cur.execute("SELECT COUNT(*) AS total_orders FROM orders")
        orders = cur.fetchone()["total_orders"]
        cur.execute("SELECT COALESCE(SUM(total_amount),0) AS revenue FROM orders WHERE status <> 'Cancelled'")
        revenue = float(cur.fetchone()["revenue"])
        cur.execute("SELECT COUNT(*) AS low_stock FROM products WHERE stock < 10")
        low_stock = cur.fetchone()["low_stock"]
        cur.close()
        return {
            "total_users": users,
            "total_orders": orders,
            "revenue": revenue,
            "low_stock": low_stock,
        }


def list_admin_products():
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT p.*, c.name AS category_name
            FROM products p
            JOIN categories c ON c.id = p.category_id
            ORDER BY p.id DESC
            """
        )
        rows = cur.fetchall()
        cur.close()
        return rows


def create_product(category_id, name, slug, short_description, specifications, price, discount_percent, stock):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO products (category_id, name, slug, short_description, specifications, price, discount_percent, stock)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (category_id, name, slug, short_description, specifications, price, discount_percent, stock),
        )
        product_id = cur.lastrowid
        conn.commit()
        cur.close()
        return product_id


def update_product(product_id, category_id, name, slug, short_description, specifications, price, discount_percent, stock):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE products
            SET category_id = %s, name = %s, slug = %s, short_description = %s,
                specifications = %s, price = %s, discount_percent = %s, stock = %s
            WHERE id = %s
            """,
            (category_id, name, slug, short_description, specifications, price, discount_percent, stock, product_id),
        )
        conn.commit()
        cur.close()


def delete_product(product_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        cur.close()


def add_product_image(product_id, image_url, is_primary=0):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        if is_primary:
            cur.execute("UPDATE product_images SET is_primary = 0 WHERE product_id = %s", (product_id,))
        cur.execute(
            "INSERT INTO product_images (product_id, image_url, is_primary) VALUES (%s, %s, %s)",
            (product_id, image_url, is_primary),
        )
        conn.commit()
        cur.close()


def list_users():
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, full_name, email, phone, created_at, is_profile_complete FROM users ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        return rows


def list_orders():
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT o.*, u.full_name, u.email, u.phone
            FROM orders o
            JOIN users u ON u.id = o.user_id
            ORDER BY o.created_at DESC
            """
        )
        rows = cur.fetchall()
        cur.close()
        return rows


def update_order_status(order_id, status):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))
        conn.commit()
        cur.close()


def list_reviews():
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT r.*, p.name AS product_name, u.full_name
            FROM reviews r
            JOIN products p ON p.id = r.product_id
            JOIN users u ON u.id = r.user_id
            ORDER BY r.created_at DESC
            """
        )
        rows = cur.fetchall()
        cur.close()
        return rows


def delete_review_admin(review_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
        conn.commit()
        cur.close()


def list_coupons():
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM coupons ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        return rows


def upsert_coupon(coupon_id, code, discount_type, discount_value, min_order_amount, max_discount, is_active):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        if coupon_id:
            cur.execute(
                """
                UPDATE coupons
                SET code = %s, discount_type = %s, discount_value = %s,
                    min_order_amount = %s, max_discount = %s, is_active = %s
                WHERE id = %s
                """,
                (code, discount_type, discount_value, min_order_amount, max_discount, is_active, coupon_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO coupons (code, discount_type, discount_value, min_order_amount, max_discount, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (code, discount_type, discount_value, min_order_amount, max_discount, is_active),
            )
        conn.commit()
        cur.close()


def list_categories():
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM categories ORDER BY name")
        rows = cur.fetchall()
        cur.close()
        return rows


def upsert_category(category_id, name, slug, description):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        if category_id:
            cur.execute(
                "UPDATE categories SET name = %s, slug = %s, description = %s WHERE id = %s",
                (name, slug, description, category_id),
            )
        else:
            cur.execute(
                "INSERT INTO categories (name, slug, description) VALUES (%s, %s, %s)",
                (name, slug, description),
            )
        conn.commit()
        cur.close()
