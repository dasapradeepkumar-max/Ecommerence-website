from flask import current_app

from .database import get_connection


def list_categories():
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM categories ORDER BY name")
        rows = cur.fetchall()
        cur.close()
        return rows


def list_products(filters):
    query = [
        """
        SELECT
            p.*,
            c.name AS category_name,
            pi.image_url AS primary_image,
            (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id) AS review_count
        FROM products p
        JOIN categories c ON c.id = p.category_id
        LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
        WHERE 1=1
        """
    ]
    params = []

    if filters.get("search"):
        query.append("AND (p.name LIKE %s OR p.short_description LIKE %s)")
        q = f"%{filters['search']}%"
        params.extend([q, q])

    if filters.get("category"):
        query.append("AND c.slug = %s")
        params.append(filters["category"])

    if filters.get("min_price"):
        query.append("AND p.price >= %s")
        params.append(filters["min_price"])

    if filters.get("max_price"):
        query.append("AND p.price <= %s")
        params.append(filters["max_price"])

    if filters.get("rating"):
        query.append("AND p.avg_rating >= %s")
        params.append(filters["rating"])

    sort_map = {
        "latest": "p.created_at DESC",
        "price_low": "p.price ASC",
        "price_high": "p.price DESC",
        "rating": "p.avg_rating DESC",
        "popular": "review_count DESC",
    }
    query.append(f"ORDER BY {sort_map.get(filters.get('sort'), 'p.created_at DESC')}")

    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(" ".join(query), params)
        rows = cur.fetchall()
        cur.close()
        return rows


def get_product_by_slug(slug):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT p.*, c.name AS category_name
            FROM products p
            JOIN categories c ON c.id = p.category_id
            WHERE p.slug = %s
            """,
            (slug,),
        )
        product = cur.fetchone()
        if not product:
            cur.close()
            return None
        cur.execute("SELECT * FROM product_images WHERE product_id = %s ORDER BY is_primary DESC, id", (product["id"],))
        images = cur.fetchall()
        cur.execute(
            """
            SELECT r.*, u.full_name
            FROM reviews r
            JOIN users u ON u.id = r.user_id
            WHERE r.product_id = %s
            ORDER BY r.updated_at DESC
            """,
            (product["id"],),
        )
        reviews = cur.fetchall()
        cur.close()
        return {"product": product, "images": images, "reviews": reviews}


def get_featured_sections():
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT p.*, c.name AS category_name, pi.image_url AS primary_image
            FROM products p
            JOIN categories c ON c.id = p.category_id
            LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
            ORDER BY p.avg_rating DESC, p.created_at DESC
            LIMIT 8
            """
        )
        featured = cur.fetchall()

        cur.execute(
            """
            SELECT p.*, c.name AS category_name, pi.image_url AS primary_image
            FROM products p
            JOIN categories c ON c.id = p.category_id
            LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
            ORDER BY p.created_at DESC
            LIMIT 8
            """
        )
        trending = cur.fetchall()

        cur.execute(
            """
            SELECT p.*, c.name AS category_name, pi.image_url AS primary_image
            FROM products p
            JOIN categories c ON c.id = p.category_id
            LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
            ORDER BY p.discount_percent DESC, p.stock DESC
            LIMIT 8
            """
        )
        recommended = cur.fetchall()
        cur.close()

    return featured, trending, recommended


def upsert_review(user_id, product_id, rating, review_text):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO reviews (user_id, product_id, rating, review_text)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE rating = VALUES(rating), review_text = VALUES(review_text)
            """,
            (user_id, product_id, rating, review_text),
        )
        cur.execute(
            """
            UPDATE products p
            SET avg_rating = (
                SELECT COALESCE(ROUND(AVG(rating), 2), 0)
                FROM reviews r WHERE r.product_id = p.id
            )
            WHERE p.id = %s
            """,
            (product_id,),
        )
        conn.commit()
        cur.close()


def delete_review(review_id, user_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute("SELECT product_id FROM reviews WHERE id = %s AND user_id = %s", (review_id, user_id))
        row = cur.fetchone()
        if not row:
            cur.close()
            return False
        product_id = row[0]
        cur.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
        cur.execute(
            """
            UPDATE products p
            SET avg_rating = (
                SELECT COALESCE(ROUND(AVG(rating), 2), 0)
                FROM reviews r WHERE r.product_id = p.id
            )
            WHERE p.id = %s
            """,
            (product_id,),
        )
        conn.commit()
        cur.close()
        return True
