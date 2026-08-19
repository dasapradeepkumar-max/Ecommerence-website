import werkzeug.security
from backend.models.database import Database


class Admin:

    @classmethod
    def verify_login(cls, email: str, password: str):
        email = email.strip().lower()
        admin = Database.query_one("SELECT * FROM admin WHERE email = %s", (email,))
        if not admin:
            return None

        if werkzeug.security.check_password_hash(admin["password_hash"], password):
            return admin
        return None

    @classmethod
    def get_kpis(cls):
        revenue_res = Database.query_one("SELECT SUM(total_amount) as total FROM orders WHERE status != 'Cancelled'")
        orders_res = Database.query_one("SELECT COUNT(*) as cnt FROM orders")
        users_res = Database.query_one("SELECT COUNT(*) as cnt FROM users")
        products_res = Database.query_one("SELECT COUNT(*) as cnt FROM products WHERE is_active = 1")
        low_stock_res = Database.query_one("SELECT COUNT(*) as cnt FROM products WHERE is_active = 1 AND stock <= 10")

        return {
            "total_revenue": round(float(revenue_res["total"]), 2) if revenue_res and revenue_res.get("total") else 0.0,
            "total_orders": int(orders_res["cnt"]) if orders_res and orders_res.get("cnt") else 0,
            "total_users": int(users_res["cnt"]) if users_res and users_res.get("cnt") else 0,
            "total_products": int(products_res["cnt"]) if products_res and products_res.get("cnt") else 0,
            "low_stock_count": int(low_stock_res["cnt"]) if low_stock_res and low_stock_res.get("cnt") else 0,
        }

    @classmethod
    def get_low_stock_products(cls, threshold=10):
        return Database.query_all(
            """
            SELECT p.*, c.name as category_name 
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            WHERE p.is_active = 1 AND p.stock <= %s 
            ORDER BY p.stock ASC
            """,
            (threshold,)
        )

    @classmethod
    def get_all_orders(cls):
        orders = Database.query_all(
            """
            SELECT o.*, u.full_name as customer_name, u.email as customer_email, u.phone as customer_phone,
                   p.payment_method, p.payment_status, p.transaction_ref
            FROM orders o
            JOIN users u ON o.user_id = u.id
            LEFT JOIN payments p ON p.order_id = o.id
            ORDER BY o.id DESC
            """
        )
        return orders

    @classmethod
    def get_coupons(cls):
        return Database.query_all("SELECT * FROM coupons ORDER BY id DESC")

    @classmethod
    def save_coupon(cls, code, discount_type, discount_value, min_order_amount=0, max_discount=None, is_active=1, coupon_id=None):
        code = code.strip().upper()
        if coupon_id:
            Database.execute(
                """
                UPDATE coupons 
                SET code = %s, discount_type = %s, discount_value = %s, min_order_amount = %s, max_discount = %s, is_active = %s
                WHERE id = %s
                """,
                (code, discount_type, discount_value, min_order_amount, max_discount, is_active, coupon_id)
            )
        else:
            Database.execute(
                """
                INSERT INTO coupons (code, discount_type, discount_value, min_order_amount, max_discount, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (code, discount_type, discount_value, min_order_amount, max_discount, is_active)
            )
        return True

    @classmethod
    def delete_coupon(cls, coupon_id: int):
        Database.execute("DELETE FROM coupons WHERE id = %s", (coupon_id,))
        return True
