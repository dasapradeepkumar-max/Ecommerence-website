import unittest
from app import create_app
from backend.models.user import User
from backend.models.admin import Admin

class AdminUsersTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def test_new_user_creation_visible_to_admin(self):
        # 1. Register a new user
        test_email = "newtestuser99@example.com"
        user, is_new = User.create_or_get(test_email)
        self.assertIsNotNone(user)

        # 2. Check Admin.get_all_users()
        users = Admin.get_all_users()
        emails = [u["email"] for u in users if u.get("email")]
        self.assertIn(test_email, emails)

        # 3. Test Admin dashboard route rendering
        with self.client.session_transaction() as sess:
            sess["is_admin"] = True
            sess["admin_name"] = "TechTrend Administrator"
            sess["admin_email"] = "admin@techtrend.com"

        response = self.client.get("/admin/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Registered Customers", response.data)
        self.assertIn(test_email.encode('utf-8'), response.data)

    def test_admin_api_users_endpoint(self):
        with self.client.session_transaction() as sess:
            sess["is_admin"] = True

        response = self.client.get("/admin/api/users")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertGreaterEqual(json_data["total_count"], 1)

if __name__ == '__main__':
    unittest.main()
