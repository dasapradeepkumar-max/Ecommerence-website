import os
import sys
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from backend.models.database import Database
from backend.models.order import Order
from backend.models.user import User
from backend.models.cart import Cart


class TestOrderProcess(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True

        # Setup test user and address
        with self.app.app_context():
            user, _ = User.create_or_get("testorder@example.com")
            user_id = user["id"]
            Cart.get_or_create_cart(user_id)
            self.user_id = user_id

            # Save test address
            addresses = User.get_addresses(user_id)
            if not addresses:
                self.address_id = User.save_address(
                    user_id=user_id,
                    full_name="Order Tester",
                    phone="9876543210",
                    address_line="123 Tech Lane",
                    city="Bangalore",
                    state="Karnataka",
                    pincode="560001",
                    is_default=1
                )
            else:
                self.address_id = addresses[0]["id"]

    def test_complete_order_process(self):
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = self.user_id

            # 1. Add item to cart
            prod = Database.query_one("SELECT id, price FROM products WHERE is_active = 1 AND stock >= 5 ORDER BY id ASC LIMIT 1")
            self.assertIsNotNone(prod, "Product with stock should exist")
            product_id = prod["id"]

            Cart.add_item(self.user_id, product_id, quantity=2)

            # Verify cart summary
            cart_summary = Cart.get_cart_details(self.user_id)
            self.assertEqual(len(cart_summary["items"]), 1)

            # 2. Process checkout with UPI payment
            payload_upi = {
                "address_id": self.address_id,
                "payment_method": "UPI",
                "upi_id": "testuser@upi"
            }
            res_upi = client.post("/api/checkout/process", json=payload_upi)
            data_upi = res_upi.get_json()
            self.assertEqual(res_upi.status_code, 200)
            self.assertTrue(data_upi["success"], f"Order placement failed: {data_upi.get('message')}")
            order_number_upi = data_upi["order_number"]

            # 3. Retrieve order from Database and verify all 5 fields
            order_db = Order.get_order_by_id(data_upi["order_id"], self.user_id)
            self.assertIsNotNone(order_db)
            self.assertEqual(order_db["order_number"], order_number_upi)
            self.assertEqual(order_db["payment_method"], "UPI")
            self.assertEqual(order_db["status"], "Ordered")
            self.assertIsNotNone(order_db.get("shipping_date"))
            self.assertIsNotNone(order_db.get("delivery_date"))

            # 4. Check Order Confirmation Page
            conf_resp = client.get(f"/order-confirmation/{order_number_upi}")
            self.assertEqual(conf_resp.status_code, 200)
            conf_html = conf_resp.get_data(as_text=True)
            self.assertIn("Order Booking Successful", conf_html)
            self.assertIn("UPI", conf_html)
            self.assertIn(order_db["shipping_date"], conf_html)
            self.assertIn(order_db["delivery_date"], conf_html)

            # 5. Add product again & Process checkout with Cash on Delivery (COD)
            Cart.add_item(self.user_id, product_id, quantity=1)
            payload_cod = {
                "address_id": self.address_id,
                "payment_method": "COD"
            }
            res_cod = client.post("/api/checkout/process", json=payload_cod)
            data_cod = res_cod.get_json()
            self.assertEqual(res_cod.status_code, 200)
            self.assertTrue(data_cod["success"])
            order_id_cod = data_cod["order_id"]

            order_cod_db = Order.get_order_by_id(order_id_cod, self.user_id)
            self.assertEqual(order_cod_db["payment_method"], "COD")
            self.assertEqual(order_cod_db["status"], "Ordered")

            # 6. Test order status update progression (Ordered -> Shipped -> Out for Delivery -> Delivered)
            upd_res = Order.update_order_status(order_id_cod, "Shipped")
            self.assertTrue(upd_res["success"])
            updated_ord = Order.get_order_by_id(order_id_cod, self.user_id)
            self.assertEqual(updated_ord["status"], "Shipped")
            self.assertEqual(updated_ord["timeline_index"], 1)

            upd_res2 = Order.update_order_status(order_id_cod, "Out for Delivery")
            self.assertTrue(upd_res2["success"])
            updated_ord2 = Order.get_order_by_id(order_id_cod, self.user_id)
            self.assertEqual(updated_ord2["status"], "Out for Delivery")
            self.assertEqual(updated_ord2["timeline_index"], 2)

            upd_res3 = Order.update_order_status(order_id_cod, "Delivered")
            self.assertTrue(upd_res3["success"])
            updated_ord3 = Order.get_order_by_id(order_id_cod, self.user_id)
            self.assertEqual(updated_ord3["status"], "Delivered")
            self.assertEqual(updated_ord3["timeline_index"], 3)

            # 7. Check My Orders page
            orders_resp = client.get("/my-orders")
            self.assertEqual(orders_resp.status_code, 200)
            orders_html = orders_resp.get_data(as_text=True)
            self.assertIn("My Orders", orders_html)
            self.assertIn("COD", orders_html)
            self.assertIn("Delivered", orders_html)


if __name__ == "__main__":
    unittest.main()
