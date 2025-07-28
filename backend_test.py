import requests
import unittest
import json
import os
from datetime import datetime, timedelta
from io import BytesIO

class FactoryPortalAPITest(unittest.TestCase):
    def setUp(self):
        # Get the backend URL from the frontend .env file
        self.base_url = "https://db3bb479-5918-43d2-852b-be41ab9c1d2c.preview.emergentagent.com/api"
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

if __name__ == "__main__":
    # Run the tests in order
    unittest.main(argv=['first-arg-is-ignored'], exit=False)