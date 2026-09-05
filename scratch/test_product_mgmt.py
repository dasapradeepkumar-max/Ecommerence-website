import io
import json
import unittest
from app import create_app
from backend.models.database import Database

class TestProductManagement(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_full_product_lifecycle(self):
        # 1. Admin login simulation
        with self.client.session_transaction() as sess:
            sess['is_admin'] = True
            sess['admin_name'] = 'Test Admin'
            sess['admin_email'] = 'admin@techtrend.com'

        # Fetch existing categories to get a valid category_id
        categories = Database.query_all("SELECT * FROM categories LIMIT 1")
        self.assertGreater(len(categories), 0, "Categories table should have seed data.")
        category_id = categories[0]['id']

        # 2. Add product test (₹10,000 original price with 20% discount)
        new_product_payload = {
            "category_id": category_id,
            "name": "Test Flagship Pro Phone",
            "slug": "test-flagship-pro-phone",
            "short_description": "Powerful smartphone for testing",
            "description": "Full description of test flagship phone with OLED display.",
            "specifications": "RAM: 12GB\nStorage: 256GB\nBattery: 5000mAh",
            "price": 10000.0,
            "discount_percent": 20.0,
            "stock": 15,
            "is_active": 1,
            "is_featured": 1,
            "is_trending": 1,
            "image_urls": ["https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80"]
        }

        res = self.client.post('/admin/api/products/save', data=json.dumps(new_product_payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        save_data = res.get_json()
        self.assertTrue(save_data['success'])
        product_id = save_data['product_id']
        print(f"\n[Test] Product created successfully with ID: {product_id}")

        # 3. Test image file upload
        test_img_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01Haf\x00\x00\x00\x00IEND\xaeB`\x82"
        data = {
            'image': (io.BytesIO(test_img_bytes), 'test_phone.png')
        }
        upload_res = self.client.post('/admin/api/products/upload-image', data=data, content_type='multipart/form-data')
        self.assertEqual(upload_res.status_code, 200)
        upload_data = upload_res.get_json()
        self.assertTrue(upload_data['success'])
        self.assertIn('/static/images/uploads/', upload_data['image_url'])
        print(f"[Test] Image upload verified: {upload_data['image_url']}")

        # 4. Fetch admin products list with search, filter, and pagination
        list_res = self.client.get(f'/admin/api/products?search=Flagship&category_id={category_id}&status=active&sort_by=newest&page=1&limit=10')
        self.assertEqual(list_res.status_code, 200)
        list_data = list_res.get_json()
        self.assertTrue(list_data['success'])
        self.assertGreaterEqual(list_data['total'], 1)
        
        found_prod = next((p for p in list_data['products'] if p['id'] == product_id), None)
        self.assertIsNotNone(found_prod)
        # Verify calculated final price (10000 - 20% = 8000)
        self.assertEqual(found_prod['discounted_price'], 8000.0)
        print(f"[Test] Calculated final price verified: RS 10,000 - 20% = RS {found_prod['discounted_price']}")

        # 5. Fetch single product detail
        detail_res = self.client.get(f'/admin/api/products/{product_id}')
        self.assertEqual(detail_res.status_code, 200)
        detail_data = detail_res.get_json()
        self.assertTrue(detail_data['success'])
        self.assertEqual(detail_data['product']['name'], "Test Flagship Pro Phone")

        # 6. Customer site integration check
        customer_search_res = self.client.get('/api/products/search?q=Flagship')
        self.assertEqual(customer_search_res.status_code, 200)
        customer_search_data = customer_search_res.get_json()
        self.assertTrue(any(p['id'] == product_id for p in customer_search_data), "Customer search must include new product.")
        print("[Test] Customer website search integration verified!")

        # 7. Edit product details
        update_payload = dict(new_product_payload)
        update_payload['product_id'] = product_id
        update_payload['name'] = "Test Flagship Ultra Phone"
        update_payload['price'] = 12000.0
        update_payload['discount_percent'] = 25.0 # 12000 - 25% = 9000
        
        update_res = self.client.post('/admin/api/products/save', data=json.dumps(update_payload), content_type='application/json')
        self.assertEqual(update_res.status_code, 200)
        self.assertTrue(update_res.get_json()['success'])
        print("[Test] Product update verified!")

        # 8. Deactivate product and clean up
        delete_res = self.client.post('/admin/api/products/delete', data=json.dumps({"product_id": product_id, "permanent": True}), content_type='application/json')
        self.assertEqual(delete_res.status_code, 200)
        self.assertTrue(delete_res.get_json()['success'])
        print("[Test] Permanent cleanup completed cleanly.")

if __name__ == "__main__":
    unittest.main()
