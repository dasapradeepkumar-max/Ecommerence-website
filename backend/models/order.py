import random
import time
from datetime import datetime, timedelta
from backend.models.database import Database
from backend.models.cart import Cart
from backend.models.product import Product


class Order:

    STATUS_TIMELINE = ['Ordered', 'Shipped', 'Out for Delivery', 'Delivered', 'Cancelled']

    @classmethod
    def generate_order_number(cls):
        timestamp = int(time.time() * 1000)
        rand_num = random.randint(100, 999)
        return f"ORD-{timestamp}-{rand_num}"

    @classmethod
    def get_estimated_dates(cls):
        now = datetime.now()
        ship_date = now + timedelta(days=1)
        delivery_date = now + timedelta(days=4)
        return ship_date.strftime("%a, %d %b %Y"), delivery_date.strftime("%a, %d %b %Y")

    @classmethod
    def create_order(cls, user_id: int, address_id: int, payment_method: str, coupon_code: str = None):
        cart_summary = Cart.get_cart_details(user_id, coupon_code=coupon_code)
        if not cart_summary["items"]:
            return {"success": False, "message": "Your cart is empty."}

        # Check stock availability for all items
        for item in cart_summary["items"]:
            prod = Product.get_by_id(item["product_id"])
            if not prod or prod["stock"] < item["quantity"]:
                return {
                    "success": False,
                    "message": f"Insufficient stock for {item['name']}. Only {prod['stock']} remaining."
                }

        order_number = cls.generate_order_number()
        shipping_date_str, delivery_date_str = cls.get_estimated_dates()
        
        # Insert into orders table
        order_id = Database.execute(
            """
            INSERT INTO orders (order_number, user_id, address_id, subtotal, coupon_code, coupon_discount, delivery_fee, total_amount, status, shipping_date, delivery_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Ordered', %s, %s)
            """,
            (
                order_number,
                user_id,
                address_id,
                cart_summary["subtotal"],
                cart_summary["coupon_code"],
                cart_summary["coupon_discount"],
                cart_summary["delivery_fee"],
                cart_summary["final_total"],
                shipping_date_str,
                delivery_date_str
            )
        )

        # Insert order items & reduce product stock
        for item in cart_summary["items"]:
            Database.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (order_id, item["product_id"], item["quantity"], item["effective_unit_price"], item["item_total"])
            )
            # Reduce inventory stock
            Database.execute(
                "UPDATE products SET stock = stock - %s WHERE id = %s",
                (item["quantity"], item["product_id"])
            )

        # Insert Payment record
        txn_ref = f"TXN-{random.randint(10000000, 99999999)}"
        Database.execute(
            """
            INSERT INTO payments (order_id, payment_method, payment_status, transaction_ref)
            VALUES (%s, %s, 'SUCCESS', %s)
            """,
            (order_id, payment_method.upper(), txn_ref)
        )

        # Clear cart
        Cart.clear_cart(user_id)

        return {
            "success": True,
            "order_id": order_id,
            "order_number": order_number,
            "total_amount": cart_summary["final_total"],
            "transaction_ref": txn_ref
        }

    @classmethod
    def get_user_orders(cls, user_id: int):
        orders = Database.query_all(
            """
            SELECT o.*, p.payment_method, p.payment_status, p.transaction_ref,
                   a.full_name as address_name, a.phone as address_phone, a.address_line, a.city, a.state, a.pincode
            FROM orders o
            JOIN addresses a ON o.address_id = a.id
            LEFT JOIN payments p ON p.order_id = o.id
            WHERE o.user_id = %s
            ORDER BY o.id DESC
            """,
            (user_id,)
        )

        for ord_obj in orders:
            items = Database.query_all(
                """
                SELECT oi.*, pr.name, pr.slug,
                       (SELECT image_url FROM product_images WHERE product_id = pr.id AND is_primary = 1 LIMIT 1) as primary_image
                FROM order_items oi
                JOIN products pr ON oi.product_id = pr.id
                WHERE oi.order_id = %s
                """,
                (ord_obj["id"],)
            )
            for it in items:
                if not it.get("primary_image"):
                    it["primary_image"] = "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80"
            ord_obj["order_items"] = items
            if not ord_obj.get("shipping_date") or not ord_obj.get("delivery_date"):
                def_s, def_d = cls.get_estimated_dates()
                ord_obj["shipping_date"] = ord_obj.get("shipping_date") or def_s
                ord_obj["delivery_date"] = ord_obj.get("delivery_date") or def_d
            ord_obj["timeline_index"] = cls.STATUS_TIMELINE.index(ord_obj["status"]) if ord_obj["status"] in cls.STATUS_TIMELINE else 0
        return orders

    @classmethod
    def get_order_by_id(cls, order_id: int, user_id: int = None):
        sql = """
            SELECT o.*, p.payment_method, p.payment_status, p.transaction_ref,
                   a.full_name as address_name, a.phone as address_phone, a.address_line, a.city, a.state, a.pincode
            FROM orders o
            JOIN addresses a ON o.address_id = a.id
            LEFT JOIN payments p ON p.order_id = o.id
            WHERE o.id = %s
        """
        params = [order_id]
        if user_id:
            sql += " AND o.user_id = %s"
            params.append(user_id)

        ord_obj = Database.query_one(sql, params)
        if not ord_obj:
            return None

        items = Database.query_all(
            """
            SELECT oi.*, pr.name, pr.slug,
                   (SELECT image_url FROM product_images WHERE product_id = pr.id AND is_primary = 1 LIMIT 1) as primary_image
            FROM order_items oi
            JOIN products pr ON oi.product_id = pr.id
            WHERE oi.order_id = %s
            """,
            (ord_obj["id"],)
        )
        for it in items:
            if not it.get("primary_image"):
                it["primary_image"] = "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80"
        ord_obj["order_items"] = items
        if not ord_obj.get("shipping_date") or not ord_obj.get("delivery_date"):
            def_s, def_d = cls.get_estimated_dates()
            ord_obj["shipping_date"] = ord_obj.get("shipping_date") or def_s
            ord_obj["delivery_date"] = ord_obj.get("delivery_date") or def_d
        ord_obj["timeline_index"] = cls.STATUS_TIMELINE.index(ord_obj["status"]) if ord_obj["status"] in cls.STATUS_TIMELINE else 0
        return ord_obj

    @classmethod
    def cancel_order(cls, order_id: int, user_id: int):
        ord_obj = cls.get_order_by_id(order_id, user_id)
        if not ord_obj:
            return {"success": False, "message": "Order not found."}

        if ord_obj["status"] in ["Shipped", "Out for Delivery", "Delivered", "Cancelled"]:
            return {"success": False, "message": f"Order cannot be cancelled in status '{ord_obj['status']}'."}

        # Restore product inventory stock
        for item in ord_obj["order_items"]:
            Database.execute(
                "UPDATE products SET stock = stock + %s WHERE id = %s",
                (item["quantity"], item["product_id"])
            )

        Database.execute("UPDATE orders SET status = 'Cancelled' WHERE id = %s", (order_id,))
        return {"success": True, "message": "Order cancelled successfully."}

    @classmethod
    def reorder(cls, order_id: int, user_id: int):
        ord_obj = cls.get_order_by_id(order_id, user_id)
        if not ord_obj:
            return {"success": False, "message": "Order not found."}

        added_count = 0
        for item in ord_obj["order_items"]:
            res = Cart.add_item(user_id, item["product_id"], item["quantity"])
            if res.get("success"):
                added_count += 1

        return {"success": True, "message": f"Added {added_count} items from order back into your cart."}

    @classmethod
    def update_order_status(cls, order_id: int, new_status: str):
        if new_status not in cls.STATUS_TIMELINE:
            return {"success": False, "message": "Invalid order status."}

        Database.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))
        return {"success": True, "message": f"Order status updated to {new_status}."}
