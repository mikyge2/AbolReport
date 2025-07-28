import requests
import unittest
import json
import os
from datetime import datetime, timedelta

class FactoryPortalAPITest(unittest.TestCase):
    def setUp(self):
        # Get the backend URL from the frontend .env file
        self.base_url = "https://1bfaaac1-5e84-4d00-b041-a30f1f53362b.preview.emergentagent.com/api"
        self.hq_token = None
        self.hq_user_info = None
        self.factory_token = None
        self.factory_user_info = None
        
        # Test user credentials
        self.hq_username = "admin"
        self.hq_password = "admin123"
        
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

    def test_03_login_headquarters_user(self):
        """Test headquarters user login"""
        data = {
            "username": self.hq_username,
            "password": self.hq_password
        }
        
        try:
            response = requests.post(f"{self.base_url}/login", json=data)
            self.assertEqual(response.status_code, 200)
            login_data = response.json()
            self.assertIn("access_token", login_data)
            self.assertIn("user_info", login_data)
            self.assertEqual(login_data["user_info"]["username"], self.hq_username)
            self.assertEqual(login_data["user_info"]["role"], "headquarters")
            
            # Save token for subsequent tests
            self.hq_token = login_data["access_token"]
            self.hq_user_info = login_data["user_info"]
            print(f"✅ Headquarters user login successful: {self.hq_username}")
        except Exception as e:
            self.fail(f"❌ Headquarters user login test failed: {str(e)}")

    def test_04_create_factory_user(self):
        """Test creating a factory user via user management endpoint"""
        if not self.hq_token:
            self.skipTest("HQ token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        # Create a factory user for testing
        user_data = {
            "username": "wakene_manager",
            "email": "wakene@company.com",
            "password": "wakene123",
            "role": "factory_employer",
            "factory_id": "wakene_food",
            "first_name": "Wakene",
            "last_name": "Manager"
        }
        
        try:
            response = requests.post(f"{self.base_url}/users", json=user_data, headers=headers)
            if response.status_code == 400 and "already registered" in response.text:
                print("ℹ️ Factory user already exists, continuing with tests")
            else:
                self.assertEqual(response.status_code, 200)
                created_user = response.json()
                self.assertEqual(created_user["username"], "wakene_manager")
                self.assertEqual(created_user["role"], "factory_employer")
                self.assertEqual(created_user["factory_id"], "wakene_food")
                self.assertEqual(created_user["first_name"], "Wakene")
                self.assertEqual(created_user["last_name"], "Manager")
                print("✅ Factory user created successfully via user management endpoint")
                
        except Exception as e:
            self.fail(f"❌ Create factory user test failed: {str(e)}")

    def test_05_login_factory_user(self):
        """Test factory user login"""
        data = {
            "username": "wakene_manager",
            "password": "wakene123"
        }
        
        try:
            response = requests.post(f"{self.base_url}/login", json=data)
            self.assertEqual(response.status_code, 200)
            login_data = response.json()
            self.assertIn("access_token", login_data)
            self.assertIn("user_info", login_data)
            self.assertEqual(login_data["user_info"]["username"], "wakene_manager")
            self.assertEqual(login_data["user_info"]["role"], "factory_employer")
            self.assertEqual(login_data["user_info"]["factory_id"], "wakene_food")
            
            # Save token for subsequent tests
            self.factory_token = login_data["access_token"]
            self.factory_user_info = login_data["user_info"]
            print(f"✅ Factory user login successful: wakene_manager")
        except Exception as e:
            self.fail(f"❌ Factory user login test failed: {str(e)}")

    def test_06_dashboard_summary_unauthorized(self):
        """Test dashboard summary endpoint without authentication"""
        try:
            response = requests.get(f"{self.base_url}/dashboard-summary")
            self.assertEqual(response.status_code, 401)
            print("✅ Dashboard summary correctly requires authentication")
        except Exception as e:
            self.fail(f"❌ Dashboard summary unauthorized test failed: {str(e)}")

    def test_07_user_management_endpoints(self):
        """Test user management endpoints with proper authentication"""
        if not self.hq_token:
            self.skipTest("HQ token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        try:
            # Test GET /users endpoint
            response = requests.get(f"{self.base_url}/users", headers=headers)
            self.assertEqual(response.status_code, 200)
            users = response.json()
            self.assertIsInstance(users, list)
            
            # Verify name fields are included
            for user in users:
                self.assertIn("first_name", user)
                self.assertIn("last_name", user)
                self.assertIn("username", user)
                self.assertIn("email", user)
                self.assertIn("role", user)
                
            print(f"✅ GET /users endpoint returned {len(users)} users with name fields")
            
            # Find a user to update (should be our created factory user)
            test_user = None
            for user in users:
                if user["username"] == "wakene_manager":
                    test_user = user
                    break
                    
            if test_user:
                # Test PUT /users/{user_id} endpoint
                update_data = {
                    "first_name": "Updated Wakene",
                    "last_name": "Updated Manager"
                }
                
                response = requests.put(f"{self.base_url}/users/{test_user['id']}", 
                                      json=update_data, headers=headers)
                self.assertEqual(response.status_code, 200)
                updated_user = response.json()
                self.assertEqual(updated_user["first_name"], "Updated Wakene")
                self.assertEqual(updated_user["last_name"], "Updated Manager")
                print("✅ PUT /users/{user_id} endpoint updated name fields successfully")
                
        except Exception as e:
            self.fail(f"❌ User management endpoints test failed: {str(e)}")

    def test_08_user_management_access_control(self):
        """Test that factory users cannot access user management endpoints"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        try:
            # Test GET /users endpoint with factory user
            response = requests.get(f"{self.base_url}/users", headers=headers)
            self.assertEqual(response.status_code, 403)
            print("✅ Factory users correctly denied access to GET /users")
            
            # Test POST /users endpoint with factory user
            user_data = {
                "username": "test_user",
                "email": "test@company.com",
                "password": "test123",
                "role": "factory_employer",
                "factory_id": "amen_water"
            }
            response = requests.post(f"{self.base_url}/users", json=user_data, headers=headers)
            self.assertEqual(response.status_code, 403)
            print("✅ Factory users correctly denied access to POST /users")
            
        except Exception as e:
            self.fail(f"❌ User management access control test failed: {str(e)}")

    def test_09_multi_reason_downtime_logging(self):
        """Test the updated daily-logs endpoint with multiple downtime reasons"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        # Create a daily log with multiple downtime reasons
        today = datetime.utcnow()
        test_date = today - timedelta(days=2)  # Use 2 days ago to avoid conflicts
        
        data = {
            "factory_id": "wakene_food",
            "date": test_date.isoformat(),
            "production_data": {
                "Flour": 500,
                "Fruska (Wheat Bran)": 200,
                "Fruskelo (Wheat Germ)": 100
            },
            "sales_data": {
                "Flour": {"amount": 400, "unit_price": 50},
                "Fruska (Wheat Bran)": {"amount": 150, "unit_price": 30},
                "Fruskelo (Wheat Germ)": {"amount": 80, "unit_price": 40}
            },
            "downtime_hours": 4.0,
            "downtime_reasons": [
                {"reason": "Equipment Maintenance", "hours": 2.5},
                {"reason": "Power Outage", "hours": 1.0},
                {"reason": "Staff Training", "hours": 0.5}
            ],
            "stock_data": {
                "Flour": 1000,
                "Fruska (Wheat Bran)": 500,
                "Fruskelo (Wheat Germ)": 300
            }
        }
        
        try:
            response = requests.post(f"{self.base_url}/daily-logs", json=data, headers=headers)
            if response.status_code == 400 and "already exists" in response.text:
                print("ℹ️ Daily log for this date already exists, testing with different date")
                # Try with a different date
                data["date"] = (test_date - timedelta(days=1)).isoformat()
                response = requests.post(f"{self.base_url}/daily-logs", json=data, headers=headers)
                
            self.assertEqual(response.status_code, 200)
            log_data = response.json()
            
            # Verify the multi-reason downtime structure
            self.assertEqual(log_data["factory_id"], "wakene_food")
            self.assertEqual(log_data["downtime_hours"], 4.0)
            self.assertIn("downtime_reasons", log_data)
            self.assertIsInstance(log_data["downtime_reasons"], list)
            self.assertEqual(len(log_data["downtime_reasons"]), 3)
            
            # Verify each downtime reason has reason and hours
            for reason_obj in log_data["downtime_reasons"]:
                self.assertIn("reason", reason_obj)
                self.assertIn("hours", reason_obj)
                self.assertIsInstance(reason_obj["hours"], (int, float))
                
            # Verify total hours match
            total_reason_hours = sum(r["hours"] for r in log_data["downtime_reasons"])
            self.assertEqual(total_reason_hours, 4.0)
            
            print("✅ Multi-reason downtime logging works correctly")
            print(f"  - Total downtime: {log_data['downtime_hours']} hours")
            print(f"  - Reasons: {len(log_data['downtime_reasons'])}")
            for reason in log_data["downtime_reasons"]:
                print(f"    - {reason['reason']}: {reason['hours']} hours")
                
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Multi-reason downtime logging test failed: {str(e)}")

    def test_10_factory_comparison_today_only(self):
        """Test factory comparison analytics returns today's data only"""
        if not self.hq_token:
            self.skipTest("HQ token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/analytics/factory-comparison", headers=headers)
            self.assertEqual(response.status_code, 200)
            comparison_data = response.json()
            
            # Check if we have data for each factory
            expected_factories = ["amen_water", "mintu_plast", "mintu_export", "wakene_food"]
            for factory_id in expected_factories:
                self.assertIn(factory_id, comparison_data)
                factory_data = comparison_data[factory_id]
                expected_metrics = ["name", "production", "sales", "revenue", "downtime", "efficiency", "sku_unit"]
                for metric in expected_metrics:
                    self.assertIn(metric, factory_data)
                    
            print("✅ Factory comparison endpoint returned today's data successfully")
            print(f"  - Factories compared: {len(comparison_data)}")
            for factory_id, data in comparison_data.items():
                print(f"    - {data['name']}: Production={data['production']}, Sales={data['sales']}, Revenue={data['revenue']}")
                
        except Exception as e:
            self.fail(f"❌ Factory comparison today's data test failed: {str(e)}")

    def test_11_factory_comparison_access_control(self):
        """Test that factory users cannot access factory comparison"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/analytics/factory-comparison", headers=headers)
            self.assertEqual(response.status_code, 403)
            print("✅ Factory comparison correctly restricted to headquarters only")
                
        except Exception as e:
            self.fail(f"❌ Factory comparison access control test failed: {str(e)}")

    def test_12_role_based_daily_logs_access(self):
        """Test role-based access control for daily logs"""
        if not self.factory_token or not self.hq_token:
            self.skipTest("Tokens not available, skipping test")
            
        # Test factory user can only see their own factory data
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/daily-logs", headers=factory_headers)
            self.assertEqual(response.status_code, 200)
            factory_logs = response.json()
            
            # All logs should be for wakene_food factory only
            for log in factory_logs:
                self.assertEqual(log["factory_id"], "wakene_food")
                
            print(f"✅ Factory user sees only their own factory data ({len(factory_logs)} logs)")
            
            # Test headquarters user can see all factory data
            hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
            response = requests.get(f"{self.base_url}/daily-logs", headers=hq_headers)
            self.assertEqual(response.status_code, 200)
            hq_logs = response.json()
            
            # Should see logs from multiple factories (if they exist)
            factory_ids_seen = set(log["factory_id"] for log in hq_logs)
            print(f"✅ Headquarters user sees all factory data ({len(hq_logs)} logs from {len(factory_ids_seen)} factories)")
            
        except Exception as e:
            self.fail(f"❌ Role-based daily logs access test failed: {str(e)}")

    def test_13_authentication_requirements(self):
        """Test that all protected endpoints require valid bearer tokens"""
        protected_endpoints = [
            ("/daily-logs", "GET"),
            ("/daily-logs", "POST"),
            ("/me", "GET"),
            ("/users", "GET"),
            ("/users", "POST"),
            ("/dashboard-summary", "GET"),
            ("/analytics/trends", "GET"),
            ("/analytics/factory-comparison", "GET"),
            ("/export-excel", "GET")
        ]
        
        try:
            for endpoint, method in protected_endpoints:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}")
                elif method == "POST":
                    response = requests.post(f"{self.base_url}{endpoint}", json={})
                    
                self.assertEqual(response.status_code, 401, 
                               f"Endpoint {method} {endpoint} should require authentication")
                
            print("✅ All protected endpoints correctly require authentication")
            
        except Exception as e:
            self.fail(f"❌ Authentication requirements test failed: {str(e)}")

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
            
    def test_09_export_excel(self):
        """Test Excel export functionality"""
        if not self.token:
            self.skipTest("Token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Test full export
            response = requests.get(f"{self.base_url}/export-excel", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Content-Type'], 
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            
            # Save the file
            file_path = os.path.join(self.download_dir, "full_export.xlsx")
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            # Check if file exists and has content
            self.assertTrue(os.path.exists(file_path))
            self.assertTrue(os.path.getsize(file_path) > 0)
            
            print("✅ Excel export functionality works correctly")
            print(f"  - Downloaded file size: {os.path.getsize(file_path)} bytes")
            
            # Test filtered export
            factory_id = "amen_water"
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
            end_date = datetime.utcnow().isoformat()
            
            response = requests.get(
                f"{self.base_url}/export-excel?factory_id={factory_id}&start_date={start_date}&end_date={end_date}", 
                headers=headers
            )
            
            # Check if response is successful (even if no data is found)
            if response.status_code == 200:
                file_path = os.path.join(self.download_dir, "filtered_export.xlsx")
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print("✅ Filtered Excel export works correctly")
            elif response.status_code == 404:
                print("ℹ️ No data found for filtered export (this is acceptable)")
            else:
                self.fail(f"❌ Filtered Excel export failed with status code {response.status_code}")
                
        except Exception as e:
            self.fail(f"❌ Excel export test failed: {str(e)}")
            
    def test_10_analytics_trends(self):
        """Test analytics trends endpoint"""
        if not self.token:
            self.skipTest("Token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(f"{self.base_url}/analytics/trends", headers=headers)
            self.assertEqual(response.status_code, 200)
            trends_data = response.json()
            
            # Verify the expected fields are present
            expected_fields = ["production", "sales", "downtime", "stock", "dates"]
            for field in expected_fields:
                self.assertIn(field, trends_data)
                self.assertIsInstance(trends_data[field], list)
                
            print("✅ Analytics trends endpoint returned data successfully")
            print(f"  - Data points: {len(trends_data['dates'])}")
            
            # Test with factory filter
            factory_id = "amen_water"
            response = requests.get(f"{self.base_url}/analytics/trends?factory_id={factory_id}", headers=headers)
            self.assertEqual(response.status_code, 200)
            print(f"✅ Analytics trends with factory filter works correctly")
            
        except Exception as e:
            self.fail(f"❌ Analytics trends test failed: {str(e)}")
            
    def test_11_factory_comparison(self):
        """Test factory comparison endpoint (headquarters only)"""
        if not self.token:
            self.skipTest("Token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(f"{self.base_url}/analytics/factory-comparison", headers=headers)
            
            # This should work for headquarters users
            if self.user_info["role"] == "headquarters":
                self.assertEqual(response.status_code, 200)
                comparison_data = response.json()
                
                # Check if we have data for each factory
                for factory_id in ["amen_water", "mintu_plast", "mintu_export", "wakene_food"]:
                    self.assertIn(factory_id, comparison_data)
                    factory_data = comparison_data[factory_id]
                    expected_metrics = ["name", "production", "sales", "revenue", "downtime", "efficiency"]
                    for metric in expected_metrics:
                        self.assertIn(metric, factory_data)
                        
                print("✅ Factory comparison endpoint returned data successfully")
                print(f"  - Factories compared: {len(comparison_data)}")
                
            # This should fail for factory users
            elif self.user_info["role"] == "factory_employer":
                self.assertEqual(response.status_code, 403)
                print("✅ Factory comparison correctly restricted for factory users")
                
        except Exception as e:
            self.fail(f"❌ Factory comparison test failed: {str(e)}")

if __name__ == "__main__":
    # Run the tests in order
    unittest.main(argv=['first-arg-is-ignored'], exit=False)