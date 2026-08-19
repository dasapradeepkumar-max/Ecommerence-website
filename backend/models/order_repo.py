import random
import string

from flask import current_app

from .cart_repo import get_cart
from .database import get_connection


def list_user_addresses(user_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM addresses WHERE user_id = %s ORDER BY is_default DESC, id DESC", (user_id,))
        rows = cur.fetchall()
        cur.close()
        return rows


def add_address(user_id, address_line, city, state, pincode, is_default=False):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        if is_default:
            cur.execute("UPDATE addresses SET is_default = 0 WHERE user_id = %s", (user_id,))
        cur.execute(
            """
            INSERT INTO addresses (user_id, address_line, city, state, pincode, is_default)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, address_line, city, state, pincode, 1 if is_default else 0),
        )
        conn.commit()
        address_id = cur.lastrowid
        cur.close()
        return address_id


def get_coupon_by_code(code):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM coupons WHERE code = %s AND is_active = 1", (code.upper(),))
        coupon = cur.fetchone()
        cur.close()
        return coupon


def _next_order_number():
    token = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"ORD-{token}"


def create_order(user_id, address_id, payment_method, cart_totals):
    cart_items = get_cart(user_id)
    if not cart_items:
        return None

    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)

        order_number = _next_order_number()
        cur.execute(
            """
            INSERT INTO orders
            (order_number, user_id, address_id, subtotal, coupon_discount, delivery_fee, total_amount, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Ordered')
            """,
            (
                order_number,
                user_id,
                address_id,
                cart_totals["subtotal"],
                cart_totals["coupon_discount"],
                cart_totals["delivery_fee"],
                cart_totals["final_total"],
            ),
        )
        order_id = cur.lastrowid

        for item in cart_items:
            price = float(item["price"])
            discount_percent = float(item["discount_percent"] or 0)
            unit_price = round(price * (1 - discount_percent / 100), 2)
            cur.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
                """,
                (order_id, item["product_id"], item["quantity"], unit_price),
            )
            cur.execute("UPDATE products SET stock = GREATEST(stock - %s, 0) WHERE id = %s", (item["quantity"], item["product_id"]))

        transaction_ref = "TXN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        cur.execute(
            """
            INSERT INTO payments (order_id, payment_method, payment_status, transaction_ref)
            VALUES (%s, %s, 'SUCCESS', %s)
            """,
            (order_id, payment_method, transaction_ref),
        )

        cur.execute("DELETE ci FROM cart_items ci JOIN cart c ON c.id = ci.cart_id WHERE c.user_id = %s", (user_id,))

        conn.commit()
        cur.close()

    return order_id


def get_order(order_id, user_id=None):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)

        if user_id:
            cur.execute(
                """
                SELECT o.*, a.address_line, a.city, a.state, a.pincode
                FROM orders o
                JOIN addresses a ON a.id = o.address_id
                WHERE o.id = %s AND o.user_id = %s
                """,
                (order_id, user_id),
            )
        else:
            cur.execute(
                """
                SELECT o.*, a.address_line, a.city, a.state, a.pincode
                FROM orders o
                JOIN addresses a ON a.id = o.address_id
                WHERE o.id = %s
                """,
                (order_id,),
            )

        order = cur.fetchone()
        if not order:
            cur.close()
            return None

        cur.execute(
            """
            SELECT oi.*, p.name, p.slug, pi.image_url
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
            WHERE oi.order_id = %s
            """,
            (order_id,),
        )
        items = cur.fetchall()

        cur.execute("SELECT * FROM payments WHERE order_id = %s ORDER BY id DESC LIMIT 1", (order_id,))
        payment = cur.fetchone()

        cur.close()
        return {"order": order, "items": items, "payment": payment}


def list_orders_for_user(user_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT o.*, p.payment_method, p.payment_status
            FROM orders o
            LEFT JOIN payments p ON p.order_id = o.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
            """,
            (user_id,),
        )
        orders = cur.fetchall()
        cur.close()
        return orders


def cancel_order(order_id, user_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT status FROM orders WHERE id = %s AND user_id = %s", (order_id, user_id))
        row = cur.fetchone()
        if not row or row["status"] not in {"Ordered", "Confirmed"}:
            cur.close()
            return False

        cur.execute("UPDATE orders SET status = 'Cancelled' WHERE id = %s", (order_id,))
        conn.commit()
        cur.close()
        return True


def reorder(order_id, user_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM cart WHERE user_id = %s", (user_id,))
        cart = cur.fetchone()
        if cart:
            cart_id = cart["id"]
        else:
            cur.execute("INSERT INTO cart (user_id) VALUES (%s)", (user_id,))
            cart_id = cur.lastrowid

        cur.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        items = cur.fetchall()
        for item in items:
            cur.execute(
                """
                INSERT INTO cart_items (cart_id, product_id, quantity)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
                """,
                (cart_id, item["product_id"], item["quantity"]),
            )

        conn.commit()
        cur.close()
        return True


def user_can_review_product(user_id, product_id):
    with get_connection(current_app.config["MYSQL_DATABASE"]) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*)
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.user_id = %s AND oi.product_id = %s AND o.status = 'Delivered'
            """,
            (user_id, product_id),
        )
        count = cur.fetchone()[0]
        cur.close()
        return count > 0
