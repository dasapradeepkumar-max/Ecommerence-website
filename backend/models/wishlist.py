from backend.models.database import Database
from backend.models.cart import Cart


class Wishlist:

    @classmethod
    def get_or_create_wishlist(cls, user_id: int):
        wl = Database.query_one("SELECT * FROM wishlist WHERE user_id = %s", (user_id,))
        if not wl:
            wl_id = Database.execute("INSERT INTO wishlist (user_id) VALUES (%s)", (user_id,))
            return Database.query_one("SELECT * FROM wishlist WHERE id = %s", (wl_id,))
        return wl

    @classmethod
    def get_user_wishlist(cls, user_id: int):
        wl = cls.get_or_create_wishlist(user_id)
        items = Database.query_all(
            """
            SELECT wi.id as item_id, wi.created_at as added_at, p.id as product_id, p.name, p.slug, p.price, p.discount_percent, p.stock, p.avg_rating,
                   (SELECT image_url FROM product_images WHERE product_id = p.id AND is_primary = 1 LIMIT 1) as primary_image
            FROM wishlist_items wi
            JOIN products p ON wi.product_id = p.id
            WHERE wi.wishlist_id = %s AND p.is_active = 1
            ORDER BY wi.id DESC
            """,
            (wl["id"],)
        )
        for item in items:
            if not item.get("primary_image"):
                item["primary_image"] = "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80"
            item["discounted_price"] = round(float(item["price"]) * (1.0 - float(item["discount_percent"]) / 100.0), 2)
        return items

    @classmethod
    def add_item(cls, user_id: int, product_id: int):
        wl = cls.get_or_create_wishlist(user_id)
        existing = Database.query_one(
            "SELECT id FROM wishlist_items WHERE wishlist_id = %s AND product_id = %s",
            (wl["id"], product_id)
        )
        if not existing:
            Database.execute(
                "INSERT INTO wishlist_items (wishlist_id, product_id) VALUES (%s, %s)",
                (wl["id"], product_id)
            )
            return {"success": True, "message": "Product added to your wishlist."}
        return {"success": True, "message": "Product is already in your wishlist."}

    @classmethod
    def remove_item(cls, user_id: int, product_id: int):
        wl = cls.get_or_create_wishlist(user_id)
        Database.execute(
            "DELETE FROM wishlist_items WHERE wishlist_id = %s AND product_id = %s",
            (wl["id"], product_id)
        )
        return {"success": True, "message": "Product removed from wishlist."}

    @classmethod
    def move_to_cart(cls, user_id: int, product_id: int):
        res = Cart.add_item(user_id, product_id, 1)
        if res.get("success"):
            cls.remove_item(user_id, product_id)
        return res
