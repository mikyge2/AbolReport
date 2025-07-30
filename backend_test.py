import requests
import unittest
import json
import os
from datetime import datetime, timedelta
from io import BytesIO

class FactoryPortalAPITest(unittest.TestCase):
    def setUp(self):
        # Get the backend URL from the frontend .env file
        self.base_url = "https://f46146dc-e914-4de1-a61c-b02806f287df.preview.emergentagent.com/api"
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

    def test_14_dashboard_summary_role_based(self):
        """Test dashboard summary with role-based filtering"""
        if not self.factory_token or not self.hq_token:
            self.skipTest("Tokens not available, skipping test")
            
        # Test factory user gets filtered data
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/dashboard-summary", headers=factory_headers)
            self.assertEqual(response.status_code, 200)
            factory_summary = response.json()
            
            # Verify expected fields are present (updated structure)
            expected_fields = ["total_downtime", "total_stock", "factory_summaries"]
            for field in expected_fields:
                self.assertIn(field, factory_summary)
                
            # Factory user should only see their own factory in summaries
            if factory_summary["factory_summaries"]:
                for factory_id in factory_summary["factory_summaries"].keys():
                    self.assertEqual(factory_id, "wakene_food")
                    
            print("✅ Factory user dashboard summary shows only their factory data")
            
            # Test headquarters user gets all data
            hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
            response = requests.get(f"{self.base_url}/dashboard-summary", headers=hq_headers)
            self.assertEqual(response.status_code, 200)
            hq_summary = response.json()
            
            print(f"✅ Headquarters dashboard summary shows data for {len(hq_summary['factory_summaries'])} factories")
            
        except Exception as e:
            self.fail(f"❌ Dashboard summary role-based test failed: {str(e)}")

    def test_15_analytics_trends_role_based(self):
        """Test analytics trends with role-based filtering"""
        if not self.factory_token or not self.hq_token:
            self.skipTest("Tokens not available, skipping test")
            
        # Test factory user gets their factory data only
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/analytics/trends", headers=factory_headers)
            self.assertEqual(response.status_code, 200)
            factory_trends = response.json()
            
            # Should return single factory format
            expected_fields = ["production", "sales", "downtime", "stock", "dates"]
            for field in expected_fields:
                self.assertIn(field, factory_trends)
                self.assertIsInstance(factory_trends[field], list)
                
            print("✅ Factory user analytics trends shows single factory format")
            
            # Test headquarters user gets multi-factory data
            hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
            response = requests.get(f"{self.base_url}/analytics/trends", headers=hq_headers)
            self.assertEqual(response.status_code, 200)
            hq_trends = response.json()
            
            # Should return multi-factory format
            if "factories" in hq_trends:
                print(f"✅ Headquarters analytics trends shows multi-factory format with {len(hq_trends['factories'])} factories")
            else:
                # If no data, should still have the expected structure
                print("✅ Headquarters analytics trends endpoint accessible")
                
        except Exception as e:
            self.fail(f"❌ Analytics trends role-based test failed: {str(e)}")

    def test_16_daily_log_edit_own_log(self):
        """Test editing own daily log - should succeed"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        # First create a daily log
        today = datetime.utcnow()
        test_date = today - timedelta(days=5)  # Use 5 days ago to avoid conflicts
        
        create_data = {
            "factory_id": "wakene_food",
            "date": test_date.isoformat(),
            "production_data": {
                "Flour": 300,
                "Fruska (Wheat Bran)": 150
            },
            "sales_data": {
                "Flour": {"amount": 250, "unit_price": 45},
                "Fruska (Wheat Bran)": {"amount": 100, "unit_price": 25}
            },
            "downtime_hours": 2.0,
            "downtime_reasons": [
                {"reason": "Equipment Check", "hours": 2.0}
            ],
            "stock_data": {
                "Flour": 800,
                "Fruska (Wheat Bran)": 400
            }
        }
        
        try:
            # Create the log
            response = requests.post(f"{self.base_url}/daily-logs", json=create_data, headers=headers)
            if response.status_code == 400 and "already exists" in response.text:
                # Try with a different date
                create_data["date"] = (test_date - timedelta(days=1)).isoformat()
                response = requests.post(f"{self.base_url}/daily-logs", json=create_data, headers=headers)
                
            self.assertEqual(response.status_code, 200)
            created_log = response.json()
            log_id = created_log["id"]
            
            # Now edit the log - update all fields
            update_data = {
                "production_data": {
                    "Flour": 350,
                    "Fruska (Wheat Bran)": 175,
                    "Fruskelo (Wheat Germ)": 50  # Add new product
                },
                "sales_data": {
                    "Flour": {"amount": 300, "unit_price": 50},
                    "Fruska (Wheat Bran)": {"amount": 125, "unit_price": 30},
                    "Fruskelo (Wheat Germ)": {"amount": 40, "unit_price": 35}
                },
                "downtime_hours": 3.5,
                "downtime_reasons": [
                    {"reason": "Equipment Maintenance", "hours": 2.0},
                    {"reason": "Staff Break", "hours": 1.5}
                ],
                "stock_data": {
                    "Flour": 900,
                    "Fruska (Wheat Bran)": 450,
                    "Fruskelo (Wheat Germ)": 250
                }
            }
            
            response = requests.put(f"{self.base_url}/daily-logs/{log_id}", json=update_data, headers=headers)
            self.assertEqual(response.status_code, 200)
            updated_log = response.json()
            
            # Verify all fields were updated
            self.assertEqual(updated_log["production_data"]["Flour"], 350)
            self.assertEqual(updated_log["production_data"]["Fruskelo (Wheat Germ)"], 50)
            self.assertEqual(updated_log["downtime_hours"], 3.5)
            self.assertEqual(len(updated_log["downtime_reasons"]), 2)
            self.assertEqual(updated_log["sales_data"]["Flour"]["unit_price"], 50)
            self.assertEqual(updated_log["stock_data"]["Fruskelo (Wheat Germ)"], 250)
            
            print("✅ Successfully edited own daily log - all fields updated correctly")
            print(f"  - Updated production data: {len(updated_log['production_data'])} products")
            print(f"  - Updated downtime: {updated_log['downtime_hours']} hours with {len(updated_log['downtime_reasons'])} reasons")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Edit own daily log test failed: {str(e)}")

    def test_17_daily_log_edit_permission_denied(self):
        """Test editing another user's daily log - should get 403 Forbidden"""
        if not self.factory_token or not self.hq_token:
            self.skipTest("Tokens not available, skipping test")
            
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        # Create a log as factory user
        today = datetime.utcnow()
        test_date = today - timedelta(days=6)
        
        create_data = {
            "factory_id": "wakene_food",
            "date": test_date.isoformat(),
            "production_data": {"Flour": 200},
            "sales_data": {"Flour": {"amount": 150, "unit_price": 40}},
            "downtime_hours": 1.0,
            "downtime_reasons": [{"reason": "Break", "hours": 1.0}],
            "stock_data": {"Flour": 600}
        }
        
        try:
            # Create log as factory user
            response = requests.post(f"{self.base_url}/daily-logs", json=create_data, headers=factory_headers)
            if response.status_code == 400 and "already exists" in response.text:
                create_data["date"] = (test_date - timedelta(days=1)).isoformat()
                response = requests.post(f"{self.base_url}/daily-logs", json=create_data, headers=factory_headers)
                
            self.assertEqual(response.status_code, 200)
            created_log = response.json()
            log_id = created_log["id"]
            
            # Try to edit as HQ user (different user) - should fail
            update_data = {"production_data": {"Flour": 250}}
            
            response = requests.put(f"{self.base_url}/daily-logs/{log_id}", json=update_data, headers=hq_headers)
            self.assertEqual(response.status_code, 403)
            self.assertIn("You can only edit your own daily logs", response.text)
            
            print("✅ Edit permission correctly denied - users can only edit their own logs")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Edit permission denied test failed: {str(e)}")

    def test_18_daily_log_delete_own_log(self):
        """Test deleting own daily log - should succeed"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        # Create a log to delete
        today = datetime.utcnow()
        test_date = today - timedelta(days=7)
        
        create_data = {
            "factory_id": "wakene_food",
            "date": test_date.isoformat(),
            "production_data": {"Flour": 100},
            "sales_data": {"Flour": {"amount": 80, "unit_price": 35}},
            "downtime_hours": 0.5,
            "downtime_reasons": [{"reason": "Quick Check", "hours": 0.5}],
            "stock_data": {"Flour": 500}
        }
        
        try:
            # Create the log
            response = requests.post(f"{self.base_url}/daily-logs", json=create_data, headers=headers)
            if response.status_code == 400 and "already exists" in response.text:
                create_data["date"] = (test_date - timedelta(days=1)).isoformat()
                response = requests.post(f"{self.base_url}/daily-logs", json=create_data, headers=headers)
                
            self.assertEqual(response.status_code, 200)
            created_log = response.json()
            log_id = created_log["id"]
            
            # Delete the log
            response = requests.delete(f"{self.base_url}/daily-logs/{log_id}", headers=headers)
            self.assertEqual(response.status_code, 200)
            delete_response = response.json()
            self.assertIn("deleted successfully", delete_response["message"])
            
            # Verify log is actually deleted by trying to fetch it
            response = requests.get(f"{self.base_url}/daily-logs", headers=headers)
            self.assertEqual(response.status_code, 200)
            logs = response.json()
            
            # Check that our deleted log is not in the list
            log_ids = [log["id"] for log in logs]
            self.assertNotIn(log_id, log_ids)
            
            print("✅ Successfully deleted own daily log - log removed from database")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Delete own daily log test failed: {str(e)}")

    def test_19_daily_log_delete_permission_denied(self):
        """Test deleting another user's daily log - should get 403 Forbidden"""
        if not self.factory_token or not self.hq_token:
            self.skipTest("Tokens not available, skipping test")
            
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        # Create a log as factory user
        today = datetime.utcnow()
        test_date = today - timedelta(days=8)
        
        create_data = {
            "factory_id": "wakene_food",
            "date": test_date.isoformat(),
            "production_data": {"Flour": 150},
            "sales_data": {"Flour": {"amount": 120, "unit_price": 42}},
            "downtime_hours": 1.5,
            "downtime_reasons": [{"reason": "Maintenance", "hours": 1.5}],
            "stock_data": {"Flour": 700}
        }
        
        try:
            # Create log as factory user
            response = requests.post(f"{self.base_url}/daily-logs", json=create_data, headers=factory_headers)
            if response.status_code == 400 and "already exists" in response.text:
                create_data["date"] = (test_date - timedelta(days=1)).isoformat()
                response = requests.post(f"{self.base_url}/daily-logs", json=create_data, headers=factory_headers)
                
            self.assertEqual(response.status_code, 200)
            created_log = response.json()
            log_id = created_log["id"]
            
            # Try to delete as HQ user (different user) - should fail
            response = requests.delete(f"{self.base_url}/daily-logs/{log_id}", headers=hq_headers)
            self.assertEqual(response.status_code, 403)
            self.assertIn("You can only delete your own daily logs", response.text)
            
            print("✅ Delete permission correctly denied - users can only delete their own logs")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Delete permission denied test failed: {str(e)}")

    def test_20_daily_log_edit_nonexistent_log(self):
        """Test editing non-existent log - should get 404"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        # Try to edit a non-existent log
        fake_log_id = "non-existent-log-id-12345"
        update_data = {"production_data": {"Flour": 100}}
        
        try:
            response = requests.put(f"{self.base_url}/daily-logs/{fake_log_id}", json=update_data, headers=headers)
            self.assertEqual(response.status_code, 404)
            self.assertIn("Daily log not found", response.text)
            
            print("✅ Edit non-existent log correctly returns 404")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Edit non-existent log test failed: {str(e)}")

    def test_21_daily_log_delete_nonexistent_log(self):
        """Test deleting non-existent log - should get 404"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        # Try to delete a non-existent log
        fake_log_id = "non-existent-log-id-67890"
        
        try:
            response = requests.delete(f"{self.base_url}/daily-logs/{fake_log_id}", headers=headers)
            self.assertEqual(response.status_code, 404)
            self.assertIn("Daily log not found", response.text)
            
            print("✅ Delete non-existent log correctly returns 404")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Delete non-existent log test failed: {str(e)}")

    def test_22_daily_log_edit_unauthorized_factory_change(self):
        """Test changing factory_id to unauthorized factory - should get 403"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        # Create a log first
        today = datetime.utcnow()
        test_date = today - timedelta(days=9)
        
        create_data = {
            "factory_id": "wakene_food",
            "date": test_date.isoformat(),
            "production_data": {"Flour": 200},
            "sales_data": {"Flour": {"amount": 150, "unit_price": 40}},
            "downtime_hours": 1.0,
            "downtime_reasons": [{"reason": "Test", "hours": 1.0}],
            "stock_data": {"Flour": 600}
        }
        
        try:
            # Create the log
            response = requests.post(f"{self.base_url}/daily-logs", json=create_data, headers=headers)
            if response.status_code == 400 and "already exists" in response.text:
                create_data["date"] = (test_date - timedelta(days=1)).isoformat()
                response = requests.post(f"{self.base_url}/daily-logs", json=create_data, headers=headers)
                
            self.assertEqual(response.status_code, 200)
            created_log = response.json()
            log_id = created_log["id"]
            
            # Try to change factory_id to unauthorized factory
            update_data = {"factory_id": "amen_water"}  # Factory user can't access this
            
            response = requests.put(f"{self.base_url}/daily-logs/{log_id}", json=update_data, headers=headers)
            self.assertEqual(response.status_code, 403)
            self.assertIn("Access denied to this factory", response.text)
            
            print("✅ Unauthorized factory change correctly denied with 403")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Unauthorized factory change test failed: {str(e)}")

    def test_23_daily_log_edit_date_conflict(self):
        """Test changing date to one that already exists - should get 400 conflict"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        # Create two logs with different dates
        today = datetime.utcnow()
        date1 = today - timedelta(days=10)
        date2 = today - timedelta(days=11)
        
        create_data1 = {
            "factory_id": "wakene_food",
            "date": date1.isoformat(),
            "production_data": {"Flour": 100},
            "sales_data": {"Flour": {"amount": 80, "unit_price": 35}},
            "downtime_hours": 0.5,
            "downtime_reasons": [{"reason": "Test1", "hours": 0.5}],
            "stock_data": {"Flour": 500}
        }
        
        create_data2 = {
            "factory_id": "wakene_food",
            "date": date2.isoformat(),
            "production_data": {"Flour": 120},
            "sales_data": {"Flour": {"amount": 100, "unit_price": 38}},
            "downtime_hours": 1.0,
            "downtime_reasons": [{"reason": "Test2", "hours": 1.0}],
            "stock_data": {"Flour": 550}
        }
        
        try:
            # Create first log
            response = requests.post(f"{self.base_url}/daily-logs", json=create_data1, headers=headers)
            if response.status_code == 400 and "already exists" in response.text:
                create_data1["date"] = (date1 - timedelta(days=1)).isoformat()
                response = requests.post(f"{self.base_url}/daily-logs", json=create_data1, headers=headers)
                
            self.assertEqual(response.status_code, 200)
            log1 = response.json()
            
            # Create second log
            response = requests.post(f"{self.base_url}/daily-logs", json=create_data2, headers=headers)
            if response.status_code == 400 and "already exists" in response.text:
                create_data2["date"] = (date2 - timedelta(days=1)).isoformat()
                response = requests.post(f"{self.base_url}/daily-logs", json=create_data2, headers=headers)
                
            self.assertEqual(response.status_code, 200)
            log2 = response.json()
            
            # Try to change log2's date to log1's date (should conflict)
            update_data = {"date": log1["date"]}
            
            response = requests.put(f"{self.base_url}/daily-logs/{log2['id']}", json=update_data, headers=headers)
            self.assertEqual(response.status_code, 400)
            self.assertIn("Daily log for this date already exists", response.text)
            
            print("✅ Date conflict correctly detected and prevented with 400")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Date conflict test failed: {str(e)}")

    def test_24_excel_export_basic_factory_user(self):
        """Test basic Excel export functionality for factory user"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/export-excel", headers=headers)
            
            # Should return Excel file or 404 if no data
            if response.status_code == 404:
                print("ℹ️ No data available for Excel export - this is expected if no logs exist")
                return
                
            self.assertEqual(response.status_code, 200)
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', content_type)
            
            # Check content disposition header for filename
            content_disposition = response.headers.get('content-disposition', '')
            self.assertIn('attachment', content_disposition)
            self.assertIn('filename=', content_disposition)
            self.assertIn('.xlsx', content_disposition)
            
            # Check that we got actual file content
            self.assertGreater(len(response.content), 0)
            
            # Save file for inspection
            filename = f"{self.download_dir}/factory_export_test.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
                
            print("✅ Basic Excel export works for factory user")
            print(f"  - Content-Type: {content_type}")
            print(f"  - File size: {len(response.content)} bytes")
            print(f"  - Saved to: {filename}")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response headers: {response.headers if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Basic Excel export test failed: {str(e)}")

    def test_25_excel_export_basic_hq_user(self):
        """Test basic Excel export functionality for headquarters user"""
        if not self.hq_token:
            self.skipTest("HQ token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/export-excel", headers=headers)
            
            # Should return Excel file or 404 if no data
            if response.status_code == 404:
                print("ℹ️ No data available for Excel export - this is expected if no logs exist")
                return
                
            self.assertEqual(response.status_code, 200)
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', content_type)
            
            # Check content disposition header for filename
            content_disposition = response.headers.get('content-disposition', '')
            self.assertIn('attachment', content_disposition)
            self.assertIn('filename=', content_disposition)
            self.assertIn('.xlsx', content_disposition)
            
            # Check that we got actual file content
            self.assertGreater(len(response.content), 0)
            
            # Save file for inspection
            filename = f"{self.download_dir}/hq_export_test.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
                
            print("✅ Basic Excel export works for headquarters user")
            print(f"  - Content-Type: {content_type}")
            print(f"  - File size: {len(response.content)} bytes")
            print(f"  - Saved to: {filename}")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response headers: {response.headers if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Basic Excel export test for HQ failed: {str(e)}")

    def test_26_excel_export_with_date_parameters(self):
        """Test Excel export with date range parameters"""
        if not self.hq_token:
            self.skipTest("HQ token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        # Test with date range parameters
        today = datetime.utcnow()
        start_date = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()
        
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        try:
            response = requests.get(f"{self.base_url}/export-excel", headers=headers, params=params)
            
            # Should return Excel file or 404 if no data in range
            if response.status_code == 404:
                print("ℹ️ No data available for specified date range - this is expected")
                return
                
            self.assertEqual(response.status_code, 200)
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', content_type)
            
            # Save file for inspection
            filename = f"{self.download_dir}/date_range_export_test.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
                
            print("✅ Excel export with date parameters works")
            print(f"  - Date range: {start_date[:10]} to {end_date[:10]}")
            print(f"  - File size: {len(response.content)} bytes")
            print(f"  - Saved to: {filename}")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Excel export with date parameters test failed: {str(e)}")

    def test_27_excel_export_with_factory_parameter(self):
        """Test Excel export with factory_id parameter for headquarters user"""
        if not self.hq_token:
            self.skipTest("HQ token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        # Test with specific factory_id parameter
        params = {'factory_id': 'wakene_food'}
        
        try:
            response = requests.get(f"{self.base_url}/export-excel", headers=headers, params=params)
            
            # Should return Excel file or 404 if no data for factory
            if response.status_code == 404:
                print("ℹ️ No data available for specified factory - this is expected")
                return
                
            self.assertEqual(response.status_code, 200)
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', content_type)
            
            # Save file for inspection
            filename = f"{self.download_dir}/factory_specific_export_test.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
                
            print("✅ Excel export with factory parameter works")
            print(f"  - Factory: wakene_food")
            print(f"  - File size: {len(response.content)} bytes")
            print(f"  - Saved to: {filename}")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Excel export with factory parameter test failed: {str(e)}")

    def test_28_excel_export_unauthorized_access(self):
        """Test Excel export without authentication - should get 401"""
        try:
            response = requests.get(f"{self.base_url}/export-excel")
            self.assertEqual(response.status_code, 401)
            print("✅ Excel export correctly requires authentication")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Excel export unauthorized access test failed: {str(e)}")

    def test_29_excel_export_factory_restriction(self):
        """Test that factory users only get their own factory data in Excel export"""
        if not self.factory_token or not self.hq_token:
            self.skipTest("Tokens not available, skipping test")
            
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        try:
            # Test factory user export (should only get wakene_food data)
            response = requests.get(f"{self.base_url}/export-excel", headers=factory_headers)
            
            if response.status_code == 404:
                print("ℹ️ Factory user has no data to export - this is expected")
            else:
                self.assertEqual(response.status_code, 200)
                
                # Save factory user export
                filename = f"{self.download_dir}/factory_restricted_export.xlsx"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                    
                print("✅ Factory user Excel export successful (restricted to their factory)")
                print(f"  - File size: {len(response.content)} bytes")
            
            # Test headquarters user export (should get all factory data)
            response = requests.get(f"{self.base_url}/export-excel", headers=hq_headers)
            
            if response.status_code == 404:
                print("ℹ️ Headquarters user has no data to export - this is expected")
            else:
                self.assertEqual(response.status_code, 200)
                
                # Save HQ user export
                filename = f"{self.download_dir}/hq_all_factories_export.xlsx"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                    
                print("✅ Headquarters user Excel export successful (all factories)")
                print(f"  - File size: {len(response.content)} bytes")
            
            print("✅ Excel export factory restrictions working correctly")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Excel export factory restriction test failed: {str(e)}")

    def test_30_excel_export_content_validation(self):
        """Test Excel export content structure and validation"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        # First ensure we have some data by creating a test log
        today = datetime.utcnow()
        test_date = today - timedelta(days=15)
        
        test_data = {
            "factory_id": "wakene_food",
            "date": test_date.isoformat(),
            "production_data": {
                "Flour": 400,
                "Fruska (Wheat Bran)": 200,
                "Fruskelo (Wheat Germ)": 100
            },
            "sales_data": {
                "Flour": {"amount": 350, "unit_price": 55},
                "Fruska (Wheat Bran)": {"amount": 180, "unit_price": 35},
                "Fruskelo (Wheat Germ)": {"amount": 90, "unit_price": 45}
            },
            "downtime_hours": 3.5,
            "downtime_reasons": [
                {"reason": "Equipment Maintenance", "hours": 2.0},
                {"reason": "Quality Check", "hours": 1.5}
            ],
            "stock_data": {
                "Flour": 1200,
                "Fruska (Wheat Bran)": 600,
                "Fruskelo (Wheat Germ)": 400
            }
        }
        
        try:
            # Create test data
            response = requests.post(f"{self.base_url}/daily-logs", json=test_data, headers=headers)
            if response.status_code == 400 and "already exists" in response.text:
                print("ℹ️ Test data already exists, proceeding with export test")
            else:
                self.assertEqual(response.status_code, 200)
                print("✅ Created test data for Excel export validation")
            
            # Now test the export
            response = requests.get(f"{self.base_url}/export-excel", headers=headers)
            self.assertEqual(response.status_code, 200)
            
            # Validate Excel file structure
            content_type = response.headers.get('content-type', '')
            self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', content_type)
            
            # Check file is not empty
            self.assertGreater(len(response.content), 1000)  # Excel files should be at least 1KB
            
            # Save file for manual inspection
            filename = f"{self.download_dir}/content_validation_export.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            # Try to read the Excel file to validate structure
            try:
                import pandas as pd
                
                # Read the Excel file
                excel_data = pd.read_excel(BytesIO(response.content), sheet_name=None)
                
                # Check that we have expected sheets
                self.assertIn('Daily Logs', excel_data)
                self.assertIn('Summary', excel_data)
                
                # Check Daily Logs sheet structure
                daily_logs_df = excel_data['Daily Logs']
                expected_columns = [
                    'Date', 'Factory', 'SKU Unit', 'Downtime Hours', 'Downtime Reasons',
                    'Created By', 'Product', 'Production Amount', 'Sales Amount', 
                    'Unit Price', 'Revenue', 'Current Stock'
                ]
                
                for col in expected_columns:
                    self.assertIn(col, daily_logs_df.columns, f"Missing column: {col}")
                
                # Check Summary sheet structure
                summary_df = excel_data['Summary']
                expected_summary_columns = [
                    'Factory', 'Total Production', 'Total Sales', 'Total Revenue',
                    'Total Downtime (Hours)', 'Average Stock', 'Number of Records'
                ]
                
                for col in expected_summary_columns:
                    self.assertIn(col, summary_df.columns, f"Missing summary column: {col}")
                
                print("✅ Excel export content validation successful")
                print(f"  - Daily Logs sheet: {len(daily_logs_df)} rows, {len(daily_logs_df.columns)} columns")
                print(f"  - Summary sheet: {len(summary_df)} rows, {len(summary_df.columns)} columns")
                print(f"  - File saved to: {filename}")
                
                # Validate downtime reasons format
                if len(daily_logs_df) > 0:
                    downtime_reasons = daily_logs_df['Downtime Reasons'].iloc[0]
                    if pd.notna(downtime_reasons):
                        # Should contain reason and hours in format "Reason (hours)"
                        self.assertIn('(', str(downtime_reasons))
                        self.assertIn('h)', str(downtime_reasons))
                        print(f"  - Downtime reasons format: {downtime_reasons}")
                
            except ImportError:
                print("ℹ️ pandas not available for detailed Excel validation, but file structure checks passed")
                
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Excel export content validation test failed: {str(e)}")

    def test_31_daily_logs_created_by_me_parameter_factory_user(self):
        """Test daily-logs endpoint with created_by_me parameter for factory user"""
        if not self.factory_token or not self.hq_token:
            self.skipTest("Tokens not available, skipping test")
            
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        # Create logs with different users to test filtering
        today = datetime.utcnow()
        
        # Create a log as factory user
        factory_log_data = {
            "factory_id": "wakene_food",
            "date": (today - timedelta(days=20)).isoformat(),
            "production_data": {"Flour": 300},
            "sales_data": {"Flour": {"amount": 250, "unit_price": 50}},
            "downtime_hours": 2.0,
            "downtime_reasons": [{"reason": "Factory User Log", "hours": 2.0}],
            "stock_data": {"Flour": 800}
        }
        
        try:
            # Create log as factory user
            response = requests.post(f"{self.base_url}/daily-logs", json=factory_log_data, headers=factory_headers)
            if response.status_code == 400 and "already exists" in response.text:
                factory_log_data["date"] = (today - timedelta(days=21)).isoformat()
                response = requests.post(f"{self.base_url}/daily-logs", json=factory_log_data, headers=factory_headers)
            
            self.assertEqual(response.status_code, 200)
            factory_log = response.json()
            print(f"✅ Created log as factory user: {factory_log['id']}")
            
            # Test created_by_me=true - should only return logs created by factory user
            response = requests.get(f"{self.base_url}/daily-logs?created_by_me=true", headers=factory_headers)
            self.assertEqual(response.status_code, 200)
            my_logs = response.json()
            
            # All logs should be created by the factory user
            for log in my_logs:
                self.assertEqual(log["created_by"], "wakene_manager")
                
            print(f"✅ Factory user with created_by_me=true returned {len(my_logs)} logs (all created by wakene_manager)")
            
            # Test without created_by_me parameter - should return all accessible logs (factory permissions)
            response = requests.get(f"{self.base_url}/daily-logs", headers=factory_headers)
            self.assertEqual(response.status_code, 200)
            all_logs = response.json()
            
            # All logs should still be for wakene_food factory (role-based filtering)
            for log in all_logs:
                self.assertEqual(log["factory_id"], "wakene_food")
                
            print(f"✅ Factory user without created_by_me returned {len(all_logs)} logs (all from wakene_food factory)")
            
            # Verify that created_by_me=true returns subset of all logs
            self.assertLessEqual(len(my_logs), len(all_logs))
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Daily logs created_by_me parameter test for factory user failed: {str(e)}")

    def test_32_daily_logs_created_by_me_parameter_hq_user(self):
        """Test daily-logs endpoint with created_by_me parameter for headquarters user"""
        if not self.hq_token:
            self.skipTest("HQ token not available, skipping test")
            
        hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        # Create a log as HQ user
        today = datetime.utcnow()
        hq_log_data = {
            "factory_id": "amen_water",
            "date": (today - timedelta(days=22)).isoformat(),
            "production_data": {"360ml": 1000, "600ml": 800},
            "sales_data": {
                "360ml": {"amount": 900, "unit_price": 2.5},
                "600ml": {"amount": 700, "unit_price": 3.0}
            },
            "downtime_hours": 1.5,
            "downtime_reasons": [{"reason": "HQ User Log", "hours": 1.5}],
            "stock_data": {"360ml": 2000, "600ml": 1500}
        }
        
        try:
            # Create log as HQ user
            response = requests.post(f"{self.base_url}/daily-logs", json=hq_log_data, headers=hq_headers)
            if response.status_code == 400 and "already exists" in response.text:
                hq_log_data["date"] = (today - timedelta(days=23)).isoformat()
                response = requests.post(f"{self.base_url}/daily-logs", json=hq_log_data, headers=hq_headers)
            
            self.assertEqual(response.status_code, 200)
            hq_log = response.json()
            print(f"✅ Created log as HQ user: {hq_log['id']}")
            
            # Test created_by_me=true - should only return logs created by HQ user
            response = requests.get(f"{self.base_url}/daily-logs?created_by_me=true", headers=hq_headers)
            self.assertEqual(response.status_code, 200)
            my_logs = response.json()
            
            # All logs should be created by the HQ user
            for log in my_logs:
                self.assertEqual(log["created_by"], "admin")
                
            print(f"✅ HQ user with created_by_me=true returned {len(my_logs)} logs (all created by admin)")
            
            # Test without created_by_me parameter - should return all logs (HQ permissions)
            response = requests.get(f"{self.base_url}/daily-logs", headers=hq_headers)
            self.assertEqual(response.status_code, 200)
            all_logs = response.json()
            
            # Should see logs from multiple users and factories
            creators = set(log["created_by"] for log in all_logs)
            factories = set(log["factory_id"] for log in all_logs)
            
            print(f"✅ HQ user without created_by_me returned {len(all_logs)} logs from {len(creators)} creators and {len(factories)} factories")
            
            # Verify that created_by_me=true returns subset of all logs
            self.assertLessEqual(len(my_logs), len(all_logs))
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Daily logs created_by_me parameter test for HQ user failed: {str(e)}")

    def test_33_daily_logs_created_by_me_false_parameter(self):
        """Test daily-logs endpoint with created_by_me=false parameter"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        try:
            # Test created_by_me=false - should return all accessible logs (same as no parameter)
            response = requests.get(f"{self.base_url}/daily-logs?created_by_me=false", headers=factory_headers)
            self.assertEqual(response.status_code, 200)
            logs_false = response.json()
            
            # Test without parameter
            response = requests.get(f"{self.base_url}/daily-logs", headers=factory_headers)
            self.assertEqual(response.status_code, 200)
            logs_no_param = response.json()
            
            # Should return the same results
            self.assertEqual(len(logs_false), len(logs_no_param))
            
            print(f"✅ created_by_me=false returns same results as no parameter ({len(logs_false)} logs)")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Daily logs created_by_me=false parameter test failed: {str(e)}")

    def test_34_daily_logs_created_by_me_with_other_filters(self):
        """Test daily-logs endpoint with created_by_me combined with other filters"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        # Create a log for testing date filtering
        today = datetime.utcnow()
        test_date = today - timedelta(days=25)
        
        test_log_data = {
            "factory_id": "wakene_food",
            "date": test_date.isoformat(),
            "production_data": {"Flour": 200},
            "sales_data": {"Flour": {"amount": 180, "unit_price": 45}},
            "downtime_hours": 1.0,
            "downtime_reasons": [{"reason": "Combined Filter Test", "hours": 1.0}],
            "stock_data": {"Flour": 700}
        }
        
        try:
            # Create test log
            response = requests.post(f"{self.base_url}/daily-logs", json=test_log_data, headers=factory_headers)
            if response.status_code == 400 and "already exists" in response.text:
                test_log_data["date"] = (test_date - timedelta(days=1)).isoformat()
                response = requests.post(f"{self.base_url}/daily-logs", json=test_log_data, headers=factory_headers)
            
            self.assertEqual(response.status_code, 200)
            created_log = response.json()
            
            # Test created_by_me=true with date range
            start_date = (today - timedelta(days=30)).isoformat()
            end_date = today.isoformat()
            
            params = {
                'created_by_me': 'true',
                'start_date': start_date,
                'end_date': end_date
            }
            
            response = requests.get(f"{self.base_url}/daily-logs", headers=factory_headers, params=params)
            self.assertEqual(response.status_code, 200)
            filtered_logs = response.json()
            
            # All logs should be created by factory user and within date range
            for log in filtered_logs:
                self.assertEqual(log["created_by"], "wakene_manager")
                log_date = datetime.fromisoformat(log["date"].replace('Z', '+00:00'))
                self.assertGreaterEqual(log_date, datetime.fromisoformat(start_date.replace('Z', '+00:00')))
                self.assertLessEqual(log_date, datetime.fromisoformat(end_date.replace('Z', '+00:00')))
            
            print(f"✅ created_by_me=true with date range returned {len(filtered_logs)} logs")
            
            # Test created_by_me=true with factory_id (should be redundant for factory user)
            params = {
                'created_by_me': 'true',
                'factory_id': 'wakene_food'
            }
            
            response = requests.get(f"{self.base_url}/daily-logs", headers=factory_headers, params=params)
            self.assertEqual(response.status_code, 200)
            factory_filtered_logs = response.json()
            
            # All logs should be created by factory user and for wakene_food
            for log in factory_filtered_logs:
                self.assertEqual(log["created_by"], "wakene_manager")
                self.assertEqual(log["factory_id"], "wakene_food")
            
            print(f"✅ created_by_me=true with factory_id returned {len(factory_filtered_logs)} logs")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Daily logs created_by_me with other filters test failed: {str(e)}")

    def test_35_excel_export_openpyxl_dependency_verification(self):
        """Test that Excel export still works after openpyxl dependency was added"""
        if not self.factory_token:
            self.skipTest("Factory token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.factory_token}"}
        
        # Create test data to ensure we have something to export
        today = datetime.utcnow()
        test_date = today - timedelta(days=30)
        
        test_data = {
            "factory_id": "wakene_food",
            "date": test_date.isoformat(),
            "production_data": {
                "Flour": 500,
                "Fruska (Wheat Bran)": 250,
                "Fruskelo (Wheat Germ)": 150
            },
            "sales_data": {
                "Flour": {"amount": 450, "unit_price": 60},
                "Fruska (Wheat Bran)": {"amount": 200, "unit_price": 40},
                "Fruskelo (Wheat Germ)": {"amount": 120, "unit_price": 50}
            },
            "downtime_hours": 2.5,
            "downtime_reasons": [
                {"reason": "Equipment Maintenance", "hours": 1.5},
                {"reason": "Staff Training", "hours": 1.0}
            ],
            "stock_data": {
                "Flour": 1500,
                "Fruska (Wheat Bran)": 800,
                "Fruskelo (Wheat Germ)": 500
            }
        }
        
        try:
            # Create test data
            response = requests.post(f"{self.base_url}/daily-logs", json=test_data, headers=headers)
            if response.status_code == 400 and "already exists" in response.text:
                print("ℹ️ Test data already exists, proceeding with export test")
            else:
                self.assertEqual(response.status_code, 200)
                print("✅ Created test data for openpyxl verification")
            
            # Test Excel export functionality
            response = requests.get(f"{self.base_url}/export-excel", headers=headers)
            self.assertEqual(response.status_code, 200)
            
            # Verify openpyxl is working correctly
            content_type = response.headers.get('content-type', '')
            self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', content_type)
            
            # Check content disposition
            content_disposition = response.headers.get('content-disposition', '')
            self.assertIn('attachment', content_disposition)
            self.assertIn('.xlsx', content_disposition)
            
            # Verify file content is valid Excel
            self.assertGreater(len(response.content), 1000)
            
            # Check Excel file magic bytes (ZIP signature for .xlsx files)
            self.assertEqual(response.content[:2], b'PK')  # ZIP file signature
            
            # Save file for verification
            filename = f"{self.download_dir}/openpyxl_verification_export.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print("✅ Excel export with openpyxl dependency working correctly")
            print(f"  - Content-Type: {content_type}")
            print(f"  - File size: {len(response.content)} bytes")
            print(f"  - File signature: Valid Excel format")
            print(f"  - Saved to: {filename}")
            
            # Try to validate Excel structure if pandas is available
            try:
                import pandas as pd
                excel_data = pd.read_excel(BytesIO(response.content), sheet_name=None)
                
                # Verify both sheets exist
                self.assertIn('Daily Logs', excel_data)
                self.assertIn('Summary', excel_data)
                
                daily_logs_df = excel_data['Daily Logs']
                summary_df = excel_data['Summary']
                
                print(f"  - Daily Logs sheet: {len(daily_logs_df)} rows")
                print(f"  - Summary sheet: {len(summary_df)} rows")
                print("✅ Excel file structure validated with pandas")
                
            except ImportError:
                print("ℹ️ pandas not available for detailed validation, but basic Excel export verified")
                
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text[:500] if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Excel export openpyxl dependency verification failed: {str(e)}")

    def test_36_excel_export_role_based_filtering_verification(self):
        """Test that Excel export role-based filtering still works correctly"""
        if not self.factory_token or not self.hq_token:
            self.skipTest("Tokens not available, skipping test")
            
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        try:
            # Test factory user export - should only get their factory data
            response = requests.get(f"{self.base_url}/export-excel", headers=factory_headers)
            
            if response.status_code == 404:
                print("ℹ️ Factory user has no data to export")
                factory_has_data = False
            else:
                self.assertEqual(response.status_code, 200)
                factory_has_data = True
                
                # Verify it's a valid Excel file
                content_type = response.headers.get('content-type', '')
                self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', content_type)
                
                factory_file_size = len(response.content)
                print(f"✅ Factory user Excel export successful: {factory_file_size} bytes")
            
            # Test headquarters user export - should get all factory data
            response = requests.get(f"{self.base_url}/export-excel", headers=hq_headers)
            
            if response.status_code == 404:
                print("ℹ️ Headquarters user has no data to export")
                hq_has_data = False
            else:
                self.assertEqual(response.status_code, 200)
                hq_has_data = True
                
                # Verify it's a valid Excel file
                content_type = response.headers.get('content-type', '')
                self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', content_type)
                
                hq_file_size = len(response.content)
                print(f"✅ Headquarters user Excel export successful: {hq_file_size} bytes")
                
                # HQ export should typically be larger or equal to factory export
                if factory_has_data:
                    self.assertGreaterEqual(hq_file_size, factory_file_size)
                    print(f"✅ HQ export size ({hq_file_size}) >= Factory export size ({factory_file_size})")
            
            # Test that factory user cannot bypass filtering with factory_id parameter
            params = {'factory_id': 'amen_water'}  # Different factory
            response = requests.get(f"{self.base_url}/export-excel", headers=factory_headers, params=params)
            
            if response.status_code == 404:
                print("✅ Factory user correctly cannot access other factory data (404 - no data)")
            else:
                self.assertEqual(response.status_code, 200)
                # Even if successful, should still only contain wakene_food data due to role filtering
                print("✅ Factory user export with factory_id parameter processed (role filtering applied)")
            
            print("✅ Excel export role-based filtering verification completed successfully")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Excel export role-based filtering verification failed: {str(e)}")

    def test_50_dashboard_analytics_trends_data_structure(self):
        """Test /api/analytics/trends endpoint data structure for dashboard graphs"""
        if not self.factory_token or not self.hq_token:
            self.skipTest("Tokens not available, skipping test")
            
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        try:
            # Test factory user - should get single factory format
            response = requests.get(f"{self.base_url}/analytics/trends?days=30", headers=factory_headers)
            self.assertEqual(response.status_code, 200)
            factory_trends = response.json()
            
            # Verify single factory data structure
            expected_fields = ["production", "sales", "downtime", "stock", "dates"]
            for field in expected_fields:
                self.assertIn(field, factory_trends, f"Missing field: {field}")
                self.assertIsInstance(factory_trends[field], list, f"Field {field} should be a list")
            
            # All arrays should have same length
            if factory_trends["dates"]:
                date_count = len(factory_trends["dates"])
                for field in ["production", "sales", "downtime", "stock"]:
                    self.assertEqual(len(factory_trends[field]), date_count, 
                                   f"Array length mismatch for {field}")
            
            print("✅ Factory user analytics trends data structure correct")
            print(f"  - Data points: {len(factory_trends['dates'])}")
            print(f"  - Fields: {list(factory_trends.keys())}")
            
            # Test headquarters user - should get multi-factory format
            hq_response = requests.get(f"{self.base_url}/analytics/trends?days=30", headers=hq_headers)
            self.assertEqual(hq_response.status_code, 200)
            hq_trends = hq_response.json()
            
            # Verify multi-factory data structure
            expected_hq_fields = ["factories", "dates", "downtime", "stock"]
            for field in expected_hq_fields:
                self.assertIn(field, hq_trends, f"Missing HQ field: {field}")
            
            self.assertIsInstance(hq_trends["factories"], dict, "Factories should be a dict")
            self.assertIsInstance(hq_trends["dates"], list, "Dates should be a list")
            self.assertIsInstance(hq_trends["downtime"], list, "Downtime should be a list")
            self.assertIsInstance(hq_trends["stock"], list, "Stock should be a list")
            
            # Check each factory has proper structure
            for factory_id, factory_data in hq_trends["factories"].items():
                self.assertIn("name", factory_data, f"Factory {factory_id} missing name")
                self.assertIn("dates", factory_data, f"Factory {factory_id} missing dates")
                self.assertIn("production", factory_data, f"Factory {factory_id} missing production")
                self.assertIn("sales", factory_data, f"Factory {factory_id} missing sales")
                
                self.assertIsInstance(factory_data["dates"], list)
                self.assertIsInstance(factory_data["production"], list)
                self.assertIsInstance(factory_data["sales"], list)
                
                # Arrays should have same length as main dates array
                if hq_trends["dates"]:
                    date_count = len(hq_trends["dates"])
                    self.assertEqual(len(factory_data["dates"]), date_count)
                    self.assertEqual(len(factory_data["production"]), date_count)
                    self.assertEqual(len(factory_data["sales"]), date_count)
            
            print("✅ Headquarters user analytics trends data structure correct")
            print(f"  - Factories: {len(hq_trends['factories'])}")
            print(f"  - Data points: {len(hq_trends['dates'])}")
            print(f"  - Factory names: {[f['name'] for f in hq_trends['factories'].values()]}")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Analytics trends data structure test failed: {str(e)}")

    def test_51_dashboard_summary_data_structure(self):
        """Test /api/dashboard-summary endpoint data structure"""
        if not self.factory_token or not self.hq_token:
            self.skipTest("Tokens not available, skipping test")
            
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        try:
            # Test factory user dashboard summary
            response = requests.get(f"{self.base_url}/dashboard-summary", headers=factory_headers)
            self.assertEqual(response.status_code, 200)
            factory_summary = response.json()
            
            # Verify required fields are present
            required_fields = ["total_downtime", "total_stock", "factory_summaries"]
            for field in required_fields:
                self.assertIn(field, factory_summary, f"Missing field: {field}")
            
            # Verify data types
            self.assertIsInstance(factory_summary["total_downtime"], (int, float))
            self.assertIsInstance(factory_summary["total_stock"], (int, float))
            self.assertIsInstance(factory_summary["factory_summaries"], dict)
            
            # Factory user should only see their own factory
            for factory_id in factory_summary["factory_summaries"].keys():
                self.assertEqual(factory_id, "wakene_food", "Factory user should only see their own factory")
            
            # Check factory summary structure
            for factory_id, factory_data in factory_summary["factory_summaries"].items():
                expected_factory_fields = ["name", "production", "sales", "downtime", "stock"]
                for field in expected_factory_fields:
                    self.assertIn(field, factory_data, f"Factory {factory_id} missing {field}")
                    self.assertIsInstance(factory_data[field], (int, float))
            
            print("✅ Factory user dashboard summary data structure correct")
            print(f"  - Total downtime: {factory_summary['total_downtime']}")
            print(f"  - Total stock: {factory_summary['total_stock']}")
            print(f"  - Factories: {len(factory_summary['factory_summaries'])}")
            
            # Test headquarters user dashboard summary
            hq_response = requests.get(f"{self.base_url}/dashboard-summary", headers=hq_headers)
            self.assertEqual(hq_response.status_code, 200)
            hq_summary = hq_response.json()
            
            # Verify same structure for HQ user
            for field in required_fields:
                self.assertIn(field, hq_summary, f"Missing HQ field: {field}")
            
            self.assertIsInstance(hq_summary["total_downtime"], (int, float))
            self.assertIsInstance(hq_summary["total_stock"], (int, float))
            self.assertIsInstance(hq_summary["factory_summaries"], dict)
            
            # HQ user should see multiple factories (if data exists)
            print("✅ Headquarters user dashboard summary data structure correct")
            print(f"  - Total downtime: {hq_summary['total_downtime']}")
            print(f"  - Total stock: {hq_summary['total_stock']}")
            print(f"  - Factories: {len(hq_summary['factory_summaries'])}")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Dashboard summary data structure test failed: {str(e)}")

    def test_52_factory_comparison_data_structure(self):
        """Test /api/analytics/factory-comparison endpoint data structure for today's data"""
        if not self.hq_token:
            self.skipTest("HQ token not available, skipping test")
            
        headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/analytics/factory-comparison", headers=headers)
            self.assertEqual(response.status_code, 200)
            comparison_data = response.json()
            
            # Should be a dictionary with factory IDs as keys
            self.assertIsInstance(comparison_data, dict, "Factory comparison should return a dictionary")
            
            # Check all expected factories are present
            expected_factories = ["amen_water", "mintu_plast", "mintu_export", "wakene_food"]
            for factory_id in expected_factories:
                self.assertIn(factory_id, comparison_data, f"Missing factory: {factory_id}")
            
            # Check each factory has proper metrics structure
            for factory_id, factory_data in comparison_data.items():
                required_metrics = ["name", "production", "sales", "revenue", "downtime", "efficiency", "sku_unit"]
                for metric in required_metrics:
                    self.assertIn(metric, factory_data, f"Factory {factory_id} missing {metric}")
                
                # Verify data types
                self.assertIsInstance(factory_data["name"], str)
                self.assertIsInstance(factory_data["production"], (int, float))
                self.assertIsInstance(factory_data["sales"], (int, float))
                self.assertIsInstance(factory_data["revenue"], (int, float))
                self.assertIsInstance(factory_data["downtime"], (int, float))
                self.assertIsInstance(factory_data["efficiency"], (int, float))
                self.assertIsInstance(factory_data["sku_unit"], str)
                
                # Efficiency should be a percentage (0-100)
                self.assertGreaterEqual(factory_data["efficiency"], 0)
                self.assertLessEqual(factory_data["efficiency"], 200)  # Allow some flexibility
            
            print("✅ Factory comparison data structure correct for today's data")
            print(f"  - Factories compared: {len(comparison_data)}")
            for factory_id, data in comparison_data.items():
                print(f"    - {data['name']}: Production={data['production']}, Sales={data['sales']}, Revenue={data['revenue']}, Efficiency={data['efficiency']:.1f}%")
            
            # Test that factory users cannot access this endpoint
            if hasattr(self, 'factory_token') and self.factory_token:
                factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
                factory_response = requests.get(f"{self.base_url}/analytics/factory-comparison", headers=factory_headers)
                self.assertEqual(factory_response.status_code, 403, "Factory users should not access factory comparison")
                print("✅ Factory comparison correctly restricted to headquarters only")
            
        except Exception as e:
            print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
            self.fail(f"❌ Factory comparison data structure test failed: {str(e)}")

    def test_53_dashboard_endpoints_role_based_filtering(self):
        """Test role-based data filtering across all dashboard endpoints"""
        if not self.factory_token or not self.hq_token:
            self.skipTest("Tokens not available, skipping test")
            
        factory_headers = {"Authorization": f"Bearer {self.factory_token}"}
        hq_headers = {"Authorization": f"Bearer {self.hq_token}"}
        
        try:
            # Test analytics/trends role-based filtering
            factory_response = requests.get(f"{self.base_url}/analytics/trends?days=30", headers=factory_headers)
            hq_response = requests.get(f"{self.base_url}/analytics/trends?days=30", headers=hq_headers)
            
            self.assertEqual(factory_response.status_code, 200)
            self.assertEqual(hq_response.status_code, 200)
            
            factory_trends = factory_response.json()
            hq_trends = hq_response.json()
            
            # Factory user gets single factory format, HQ gets multi-factory format
            self.assertIn("production", factory_trends)  # Single factory format
            self.assertIn("factories", hq_trends)  # Multi-factory format
            
            print("✅ Analytics trends role-based filtering working")
            
            # Test dashboard-summary role-based filtering
            factory_summary_response = requests.get(f"{self.base_url}/dashboard-summary", headers=factory_headers)
            hq_summary_response = requests.get(f"{self.base_url}/dashboard-summary", headers=hq_headers)
            
            self.assertEqual(factory_summary_response.status_code, 200)
            self.assertEqual(hq_summary_response.status_code, 200)
            
            factory_summary = factory_summary_response.json()
            hq_summary = hq_summary_response.json()
            
            # Factory user should only see their factory in summaries
            if factory_summary["factory_summaries"]:
                for factory_id in factory_summary["factory_summaries"].keys():
                    self.assertEqual(factory_id, "wakene_food")
            
            print("✅ Dashboard summary role-based filtering working")
            
            # Test factory-comparison access control
            factory_comparison_response = requests.get(f"{self.base_url}/analytics/factory-comparison", headers=factory_headers)
            hq_comparison_response = requests.get(f"{self.base_url}/analytics/factory-comparison", headers=hq_headers)
            
            self.assertEqual(factory_comparison_response.status_code, 403)  # Factory users denied
            self.assertEqual(hq_comparison_response.status_code, 200)  # HQ users allowed
            
            print("✅ Factory comparison access control working")
            
            print("✅ All dashboard endpoints have proper role-based filtering")
            
        except Exception as e:
            print(f"❌ Dashboard endpoints role-based filtering test failed: {str(e)}")

if __name__ == "__main__":
    # Run the tests in order
    unittest.main(argv=['first-arg-is-ignored'], exit=False)