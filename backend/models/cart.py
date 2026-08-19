from backend.models.database import Database
from backend.models.product import Product
from config.settings import Settings


class Cart:

    @classmethod
    def get_or_create_cart(cls, user_id: int):
        cart = Database.query_one("SELECT * FROM cart WHERE user_id = %s", (user_id,))
        if not cart:
            cart_id = Database.execute("INSERT INTO cart (user_id) VALUES (%s)", (user_id,))
            return Database.query_one("SELECT * FROM cart WHERE id = %s", (cart_id,))
        return cart

    @classmethod
    def add_item(cls, user_id: int, product_id: int, quantity: int = 1):
        cart = cls.get_or_create_cart(user_id)
        product = Product.get_by_id(product_id)
        if not product or product["stock"] <= 0:
            return {"success": False, "message": "Product is out of stock."}

        existing_item = Database.query_one(
            "SELECT * FROM cart_items WHERE cart_id = %s AND product_id = %s",
            (cart["id"], product_id)
        )

        if existing_item:
            new_qty = existing_item["quantity"] + quantity
            if new_qty > product["stock"]:
                return {"success": False, "message": f"Only {product['stock']} units available in stock."}
            Database.execute("UPDATE cart_items SET quantity = %s WHERE id = %s", (new_qty, existing_item["id"]))
        else:
            if quantity > product["stock"]:
                return {"success": False, "message": f"Only {product['stock']} units available in stock."}
            Database.execute(
                "INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (%s, %s, %s)",
                (cart["id"], product_id, quantity)
            )

        return {"success": True, "message": f"Added {product['name']} to cart."}

    @classmethod
    def update_item_quantity(cls, user_id: int, item_id: int, quantity: int):
        cart = cls.get_or_create_cart(user_id)
        item = Database.query_one("SELECT * FROM cart_items WHERE id = %s AND cart_id = %s", (item_id, cart["id"]))
        if not item:
            return {"success": False, "message": "Cart item not found."}

        if quantity <= 0:
            Database.execute("DELETE FROM cart_items WHERE id = %s", (item_id,))
            return {"success": True, "message": "Item removed from cart."}

        product = Product.get_by_id(item["product_id"])
        if quantity > product["stock"]:
            return {"success": False, "message": f"Only {product['stock']} units available in stock."}

        Database.execute("UPDATE cart_items SET quantity = %s WHERE id = %s", (quantity, item_id))
        return {"success": True, "message": "Cart updated."}

    @classmethod
    def remove_item(cls, user_id: int, item_id: int):
        cart = cls.get_or_create_cart(user_id)
        Database.execute("DELETE FROM cart_items WHERE id = %s AND cart_id = %s", (item_id, cart["id"]))
        return {"success": True, "message": "Item removed from cart."}

    @classmethod
    def clear_cart(cls, user_id: int):
        cart = cls.get_or_create_cart(user_id)
        Database.execute("DELETE FROM cart_items WHERE cart_id = %s", (cart["id"],))

    @classmethod
    def get_cart_details(cls, user_id: int, coupon_code: str = None):
        cart = cls.get_or_create_cart(user_id)
        raw_items = Database.query_all(
            """
            SELECT ci.id as item_id, ci.quantity, p.id as product_id, p.name, p.price, p.discount_percent, p.stock,
                   (SELECT image_url FROM product_images WHERE product_id = p.id AND is_primary = 1 LIMIT 1) as primary_image
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.cart_id = %s AND p.is_active = 1
            """,
            (cart["id"],)
        )

        items = []
        subtotal = 0.0
        total_items_count = 0

        for item in raw_items:
            unit_price = float(item["price"])
            discount_pct = float(item["discount_percent"])
            effective_unit_price = round(unit_price * (1.0 - discount_pct / 100.0), 2)
            item_total = round(effective_unit_price * item["quantity"], 2)

            subtotal += item_total
            total_items_count += item["quantity"]

            if not item.get("primary_image"):
                item["primary_image"] = "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80"

            items.append({
                "item_id": item["item_id"],
                "product_id": item["product_id"],
                "name": item["name"],
                "price": unit_price,
                "discount_percent": discount_pct,
                "effective_unit_price": effective_unit_price,
                "quantity": item["quantity"],
                "stock": item["stock"],
                "primary_image": item["primary_image"],
                "item_total": item_total
            })

        # Coupon Discount calculation
        coupon_discount = 0.0
        applied_coupon = None

        if coupon_code and subtotal > 0:
            coupon = Database.query_one(
                "SELECT * FROM coupons WHERE UPPER(code) = %s AND is_active = 1",
                (coupon_code.strip().upper(),)
            )
            if coupon:
                min_amt = float(coupon["min_order_amount"])
                if subtotal >= min_amt:
                    disc_type = coupon["discount_type"]
                    disc_val = float(coupon["discount_value"])
                    if disc_type == "percent":
                        raw_disc = subtotal * (disc_val / 100.0)
                        max_d = float(coupon["max_discount"]) if coupon["max_discount"] else raw_disc
                        coupon_discount = min(raw_disc, max_d)
                    else: # flat
                        coupon_discount = disc_val
                    coupon_discount = round(coupon_discount, 2)
                    applied_coupon = coupon["code"]

        # Delivery Fee calculation
        delivery_fee = 0.0 if (subtotal >= Settings.FREE_DELIVERY_MIN_TOTAL or subtotal == 0) else Settings.DEFAULT_DELIVERY_FEE

        final_total = max(0.0, round(subtotal - coupon_discount + delivery_fee, 2))

        return {
            "cart_id": cart["id"],
            "items": items,
            "total_items_count": total_items_count,
            "subtotal": round(subtotal, 2),
            "coupon_code": applied_coupon,
            "coupon_discount": coupon_discount,
            "delivery_fee": delivery_fee,
            "free_delivery_threshold": Settings.FREE_DELIVERY_MIN_TOTAL,
            "final_total": final_total
        }
