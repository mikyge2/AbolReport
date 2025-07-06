import requests
import unittest
import json
import os
from datetime import datetime, timedelta

class FactoryPortalAPITest(unittest.TestCase):
    def setUp(self):
        # Get the backend URL from the frontend .env file
        self.base_url = "https://b1d9bdb3-2272-4590-afff-52f9d383a2f6.preview.emergentagent.com/api"
        self.token = None
        self.user_info = None
        
        # Test user credentials - using demo credentials from the frontend
        self.test_username = "admin"
        self.test_password = "admin123"
        
        # Create a directory for downloaded files if it doesn't exist
        self.download_dir = "/tmp/factory_portal_test_downloads"
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def test_01_backend_connectivity(self):
        """Test if the backend is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/factories")
            self.assertEqual(response.status_code, 200)
            print("✅ Backend is running and accessible")
        except Exception as e:
            self.fail(f"❌ Backend connectivity test failed: {str(e)}")

    def test_02_get_factories(self):
        """Test factories endpoint"""
        try:
            response = requests.get(f"{self.base_url}/factories")
            self.assertEqual(response.status_code, 200)
            factories = response.json()
            
            # Verify the expected factories are present
            expected_factories = ["amen_water", "mintu_plast", "mintu_export", "wakene_food"]
            for factory_id in expected_factories:
                self.assertIn(factory_id, factories)
                
            print(f"✅ Factories endpoint returned {len(factories)} factories")
            for factory_id, factory_data in factories.items():
                print(f"  - {factory_data['name']} ({len(factory_data['products'])} products, SKU: {factory_data['sku_unit']})")
        except Exception as e:
            self.fail(f"❌ Get factories test failed: {str(e)}")

    def test_03_login_user(self):
        """Test user login endpoint with demo credentials"""
        data = {
            "username": self.test_username,
            "password": self.test_password
        }
        
        try:
            response = requests.post(f"{self.base_url}/login", json=data)
            self.assertEqual(response.status_code, 200)
            login_data = response.json()
            self.assertIn("access_token", login_data)
            self.assertIn("user_info", login_data)
            self.assertEqual(login_data["user_info"]["username"], self.test_username)
            
            # Save token for subsequent tests
            self.token = login_data["access_token"]
            self.user_info = login_data["user_info"]
            print(f"✅ User login successful: {self.test_username}")
        except Exception as e:
            self.fail(f"❌ User login test failed: {str(e)}")

    def test_04_dashboard_summary_unauthorized(self):
        """Test dashboard summary endpoint without authentication"""
        try:
            response = requests.get(f"{self.base_url}/dashboard-summary")
            self.assertEqual(response.status_code, 401)
            print("✅ Dashboard summary correctly requires authentication")
        except Exception as e:
            self.fail(f"❌ Dashboard summary unauthorized test failed: {str(e)}")

    def test_05_dashboard_summary_authorized(self):
        """Test dashboard summary endpoint with authentication"""
        if not self.token:
            self.skipTest("Token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(f"{self.base_url}/dashboard-summary", headers=headers)
            self.assertEqual(response.status_code, 200)
            summary = response.json()
            
            # Verify the expected fields are present
            expected_fields = ["total_production", "total_sales", "total_downtime", "total_stock", "factory_summaries"]
            for field in expected_fields:
                self.assertIn(field, summary)
                
            print("✅ Dashboard summary endpoint returned data successfully")
            print(f"  - Total Production: {summary['total_production']}")
            print(f"  - Total Sales: {summary['total_sales']}")
            print(f"  - Total Downtime: {summary['total_downtime']} hours")
            print(f"  - Total Stock: {summary['total_stock']}")
            print(f"  - Factory Summaries: {len(summary['factory_summaries'])} factories")
        except Exception as e:
            self.fail(f"❌ Dashboard summary authorized test failed: {str(e)}")

    def test_06_get_daily_logs(self):
        """Test getting daily logs"""
        if not self.token:
            self.skipTest("Token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(f"{self.base_url}/daily-logs", headers=headers)
            self.assertEqual(response.status_code, 200)
            logs = response.json()
            self.assertIsInstance(logs, list)
            print(f"✅ Retrieved {len(logs)} daily logs")
        except Exception as e:
            self.fail(f"❌ Get daily logs test failed: {str(e)}")

    def test_07_create_daily_log(self):
        """Test creating a daily log"""
        if not self.token:
            self.skipTest("Token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create a daily log for Amen Water
        today = datetime.utcnow()
        # Use yesterday to avoid conflict with existing logs
        yesterday = today - timedelta(days=1)
        
        data = {
            "factory_id": "amen_water",
            "date": yesterday.isoformat(),
            "production_data": {
                "360ml": 100,
                "600ml": 200,
                "1000ml": 150,
                "2000ml": 50
            },
            "sales_data": {
                "360ml": {"amount": 80, "unit_price": 10},
                "600ml": {"amount": 150, "unit_price": 15},
                "1000ml": {"amount": 120, "unit_price": 20},
                "2000ml": {"amount": 30, "unit_price": 30}
            },
            "downtime_hours": 2.5,
            "downtime_reason": "Maintenance",
            "stock_data": {
                "360ml": 500,
                "600ml": 400,
                "1000ml": 300,
                "2000ml": 200
            }
        }
        
        try:
            response = requests.post(f"{self.base_url}/daily-logs", json=data, headers=headers)
            self.assertEqual(response.status_code, 200)
            log_data = response.json()
            self.assertEqual(log_data["factory_id"], "amen_water")
            self.assertEqual(log_data["downtime_hours"], 2.5)
            self.assertEqual(log_data["downtime_reason"], "Maintenance")
            print("✅ Daily log created successfully")
        except Exception as e:
            print(f"❌ Create daily log test failed: {str(e)}")
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
            self.fail(f"❌ Create daily log test failed: {str(e)}")

    def test_08_get_current_user(self):
        """Test getting current user info"""
        if not self.token:
            self.skipTest("Token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(f"{self.base_url}/me", headers=headers)
            self.assertEqual(response.status_code, 200)
            user_data = response.json()
            self.assertEqual(user_data["username"], self.test_username)
            print("✅ Current user info retrieved successfully")
        except Exception as e:
            self.fail(f"❌ Get current user test failed: {str(e)}")

if __name__ == "__main__":
    # Run the tests in order
    unittest.main(argv=['first-arg-is-ignored'], exit=False)