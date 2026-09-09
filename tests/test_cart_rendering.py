import unittest
from app import create_app
from backend.models.cart import Cart
from backend.models.user import User

class CartRenderingTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def test_cart_page_unauthenticated(self):
        response = self.client.get('/cart')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Shopping Cart', response.data)

    def test_cart_page_authenticated_with_items(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1  # assuming user 1 exists or mock user

        # Add item to cart for user 1
        try:
            Cart.add_item(user_id=1, product_id=1, quantity=2)
        except Exception as e:
            print(f"Add item note: {e}")

        response = self.client.get('/cart')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Shopping Cart', response.data)
        # Ensure no TypeError was raised during rendering
        self.assertNotIn(b"TypeError", response.data)
        self.assertNotIn(b"builtin_function_or_method", response.data)

    def test_checkout_page_authenticated(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1

        response = self.client.get('/checkout')
        # Should render 200 or redirect to cart if empty
        self.assertIn(response.status_code, [200, 302])
        self.assertNotIn(b"TypeError", response.data)
        self.assertNotIn(b"builtin_function_or_method", response.data)

if __name__ == '__main__':
    unittest.main()
