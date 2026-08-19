from flask import current_app

from .database import get_connection


def _get_or_create_cart(cur, user_id):
    cur.execute("SELECT id FROM cart WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO cart (user_id) VALUES (%s)", (user_id,))
    return cur.lastrowid


def add_to_cart(user_id, product_id, quantity):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cart_id = _get_or_create_cart(cur, user_id)
        cur.execute(
            """
            INSERT INTO cart_items (cart_id, product_id, quantity)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
            """,
            (cart_id, product_id, quantity),
        )
        conn.commit()
        cur.close()


def update_cart_item(user_id, item_id, quantity):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        if quantity <= 0:
            cur.execute(
                """
                DELETE ci FROM cart_items ci
                JOIN cart c ON c.id = ci.cart_id
                WHERE ci.id = %s AND c.user_id = %s
                """,
                (item_id, user_id),
            )
        else:
            cur.execute(
                """
                UPDATE cart_items ci
                JOIN cart c ON c.id = ci.cart_id
                SET ci.quantity = %s
                WHERE ci.id = %s AND c.user_id = %s
                """,
                (quantity, item_id, user_id),
            )
        conn.commit()
        cur.close()


def get_cart(user_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM cart WHERE user_id = %s", (user_id,))
        cart = cur.fetchone()
        if not cart:
            cur.close()
            return []

        cur.execute(
            """
            SELECT
                ci.id,
                ci.quantity,
                p.id AS product_id,
                p.name,
                p.slug,
                p.price,
                p.discount_percent,
                p.stock,
                pi.image_url
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
            WHERE ci.cart_id = %s
            ORDER BY ci.id DESC
            """,
            (cart["id"],),
        )
        items = cur.fetchall()
        cur.close()
        return items


def clear_cart(user_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM cart WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if row:
            cur.execute("DELETE FROM cart_items WHERE cart_id = %s", (row[0],))
        conn.commit()
        cur.close()


def add_to_wishlist(user_id, product_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM wishlist WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        wishlist_id = row[0] if row else None
        if not wishlist_id:
            cur.execute("INSERT INTO wishlist (user_id) VALUES (%s)", (user_id,))
            wishlist_id = cur.lastrowid
        cur.execute(
            "INSERT IGNORE INTO wishlist_items (wishlist_id, product_id) VALUES (%s, %s)",
            (wishlist_id, product_id),
        )
        conn.commit()
        cur.close()


def remove_from_wishlist(user_id, product_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM wishlist WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if row:
            cur.execute("DELETE FROM wishlist_items WHERE wishlist_id = %s AND product_id = %s", (row[0], product_id))
        conn.commit()
        cur.close()


def get_wishlist(user_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM wishlist WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            return []
        cur.execute(
            """
            SELECT p.*, pi.image_url, c.name AS category_name
            FROM wishlist_items wi
            JOIN products p ON p.id = wi.product_id
            JOIN categories c ON c.id = p.category_id
            LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
            WHERE wi.wishlist_id = %s
            ORDER BY wi.id DESC
            """,
            (row["id"],),
        )
        items = cur.fetchall()
        cur.close()
        return items
