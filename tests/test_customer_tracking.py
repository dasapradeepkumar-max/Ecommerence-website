import time
import unittest
from app import create_app
from backend.models.user import User
from backend.models.admin import Admin
from backend.models.order import Order
from backend.models.product import Product
from backend.models.database import Database

class CustomerTrackingTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def test_customer_user_id_and_login_activity(self):
        ts = int(time.time() * 1000)
        test_email = f"customertest_{ts}@example.com"
        
        # 1. Register new user
        user1, is_new = User.create_or_get(test_email, ip_address="127.0.0.1", user_agent="PyTest-Agent")
        self.assertTrue(is_new)
        self.assertIsNotNone(user1.get("user_code"))
        self.assertTrue(user1["user_code"].startswith("USR-"))
        self.assertEqual(user1.get("login_count"), 1)
        
        user_id = user1["id"]
        initial_user_code = user1["user_code"]

        # 2. Check login history log
        history1 = User.get_login_history(user_id)
        self.assertEqual(len(history1), 1)

        # 3. Login again (second time)
        user2, is_new_again = User.create_or_get(test_email, ip_address="127.0.0.1", user_agent="PyTest-Agent")
        self.assertFalse(is_new_again)
        self.assertEqual(user2["id"], user_id)
        self.assertEqual(user2["user_code"], initial_user_code)
        self.assertEqual(user2.get("login_count"), 2)

        # 4. Check updated login history log
        history2 = User.get_login_history(user_id)
        self.assertEqual(len(history2), 2)
        self.assertIsNotNone(history2[0]["login_at"])

    def test_customer_order_linkage_and_detail_api(self):
        ts = int(time.time() * 1000)
        test_email = f"customer_order_{ts}@example.com"
        test_phone = f"9{ts % 1000000000:09d}"

        user, _ = User.create_or_get(test_email)
        user_id = user["id"]

        # Update profile with valid address
        User.update_profile(
            user_id=user_id,
            full_name="Alice Test",
            phone=test_phone,
            email=test_email,
            address="123 Tech Lane",
            city="TechCity",
            state="TechState",
            pincode="560001"
        )

        addresses = User.get_addresses(user_id)
        self.assertTrue(len(addresses) > 0)
        addr_id = addresses[0]["id"]

        # Add product to cart & place order
        prod = Database.query_one("SELECT id FROM products WHERE is_active = 1 AND stock >= 5 LIMIT 1")
        if prod:
            prod_id = prod["id"]
            Database.execute("INSERT INTO cart_items (cart_id, product_id, quantity) VALUES ((SELECT id FROM cart WHERE user_id = %s), %s, 1)", (user_id, prod_id))
            
            order_res = Order.create_order(user_id, addr_id, "UPI")
            self.assertTrue(order_res["success"])

        # Check Customer Detail via User model
        detail = User.get_customer_detail(user_id)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["user"]["user_code"], user["user_code"])
        self.assertGreaterEqual(detail["total_orders"], 1)

        # Test Admin Customer Detail API Endpoint
        with self.client.session_transaction() as sess:
            sess["is_admin"] = True
            sess["admin_name"] = "Admin Test"
            sess["admin_email"] = "admin@techtrend.com"

        api_res = self.client.get(f"/admin/api/customers/{user_id}")
        self.assertEqual(api_res.status_code, 200)
        data = api_res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["customer"]["user"]["user_code"], user["user_code"])
        self.assertEqual(len(data["customer"]["orders"]), detail["total_orders"])

if __name__ == '__main__':
    unittest.main()
