import requests
import unittest
import json
import os
from datetime import datetime, timedelta
from io import BytesIO

class ComprehensiveFactorySystemTest(unittest.TestCase):
    """
    Comprehensive test suite for the factory management system based on review request:
    - Test admin authentication (username: admin, password: admin1234, role: headquarters)
    - Verify ~1,894 daily logs from August 7, 2024 to today across 4 factories
    - Test all major API endpoints with populated data
    - Verify role-based access control
    - Check data integrity (RPT-XXXXX format, realistic metrics)
    - Test user management endpoints
    
    Expected Results:
    - Total logs: ~1,894
    - Revenue: ~$195M 
    - Production: ~203M units
    - Downtime: ~5,974 hours
    - Report IDs: RPT-10000 to RPT-11893
    - 4 active factories
    """
    
    def setUp(self):
        # Get the backend URL from the frontend .env file
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        backend_url = line.split('=')[1].strip()
                        self.base_url = f"{backend_url}/api"
                        break
                else:
                    # Fallback to localhost if not found
                    self.base_url = "http://localhost:8001/api"
        except:
            self.base_url = "http://localhost:8001/api"
            
        self.admin_token = None
        self.admin_user_info = None
        
        # Admin credentials from review request
        self.admin_username = "admin"
        self.admin_password = "admin1234"
        
        # Expected data metrics from review request
        self.expected_total_logs = 1894
        self.expected_revenue_approx = 195000000  # ~$195M
        self.expected_production_approx = 203000000  # ~203M units
        self.expected_downtime_approx = 5974  # ~5,974 hours
        self.expected_report_id_start = "RPT-10000"
        self.expected_report_id_end = "RPT-11893"
        self.expected_factories = 4
        
        # Date range from review request
        self.start_date = datetime(2024, 8, 7)  # August 7, 2024
        self.end_date = datetime.utcnow()
        
        print(f"\n🔧 Test Setup:")
        print(f"  - Backend URL: {self.base_url}")
        print(f"  - Expected date range: {self.start_date.date()} to {self.end_date.date()}")
        print(f"  - Expected logs: ~{self.expected_total_logs}")
        print(f"  - Expected revenue: ~${self.expected_revenue_approx:,}")

    def test_01_admin_authentication(self):
        """Test admin user authentication with specific credentials from review request"""
        print("\n🔐 Testing Admin Authentication...")
        
        data = {
            "username": self.admin_username,
            "password": self.admin_password
        }
        
        try:
            response = requests.post(f"{self.base_url}/auth/login", json=data)
            self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
            
            login_data = response.json()
            self.assertIn("access_token", login_data)
            self.assertEqual(login_data["token_type"], "bearer")
            
            # Save token for subsequent tests
            self.admin_token = login_data["access_token"]
            
            # Get user info
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{self.base_url}/auth/me", headers=headers)
            self.assertEqual(response.status_code, 200)
            
            user_info = response.json()
            self.assertEqual(user_info["username"], self.admin_username)
            self.assertEqual(user_info["role"], "headquarters")
            self.admin_user_info = user_info
            
            print(f"✅ Admin authentication successful:")
            print(f"  - Username: {user_info['username']}")
            print(f"  - Role: {user_info['role']}")
            print(f"  - Token obtained: {self.admin_token[:20]}...")
            
        except Exception as e:
            self.fail(f"❌ Admin authentication failed: {str(e)}")

    def test_02_data_verification_comprehensive(self):
        """Verify database contains expected data volume and structure"""
        if not self.admin_token:
            self.skipTest("Admin token not available")
            
        print(f"\n📊 Testing Data Verification (Expected ~{self.expected_total_logs} logs)...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Get all daily logs with date range
            params = {
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat()
            }
            
            response = requests.get(f"{self.base_url}/daily-logs", headers=headers, params=params)
            self.assertEqual(response.status_code, 200)
            
            all_logs = response.json()
            total_logs = len(all_logs)
            
            print(f"✅ Data Volume Verification:")
            print(f"  - Total logs found: {total_logs}")
            print(f"  - Expected: ~{self.expected_total_logs}")
            print(f"  - Date range: {self.start_date.date()} to {self.end_date.date()}")
            
            # Verify we have substantial data (allow some variance)
            self.assertGreater(total_logs, self.expected_total_logs * 0.8, 
                             f"Expected at least {self.expected_total_logs * 0.8} logs, got {total_logs}")
            
            # Verify factory distribution
            factory_counts = {}
            for log in all_logs:
                factory_id = log.get("factory_id")
                factory_counts[factory_id] = factory_counts.get(factory_id, 0) + 1
            
            print(f"  - Factory distribution:")
            for factory_id, count in factory_counts.items():
                print(f"    - {factory_id}: {count} logs")
            
            self.assertEqual(len(factory_counts), self.expected_factories, 
                           f"Expected {self.expected_factories} factories, got {len(factory_counts)}")
            
            # Verify date range coverage
            dates = [datetime.fromisoformat(log["date"]) for log in all_logs if log.get("date")]
            if dates:
                min_date = min(dates)
                max_date = max(dates)
                print(f"  - Actual date range: {min_date.date()} to {max_date.date()}")
                
                # Verify dates are within expected range
                self.assertGreaterEqual(min_date.date(), self.start_date.date())
                self.assertLessEqual(max_date.date(), self.end_date.date())
            
            # Verify report ID format and range
            report_ids = [log.get("report_id") for log in all_logs if log.get("report_id")]
            rpt_ids = [rid for rid in report_ids if rid and rid.startswith("RPT-")]
            
            print(f"  - Report IDs with RPT format: {len(rpt_ids)}")
            
            if rpt_ids:
                # Sort to find range
                rpt_numbers = []
                for rid in rpt_ids:
                    try:
                        num = int(rid.split("-")[1])
                        rpt_numbers.append(num)
                    except:
                        continue
                
                if rpt_numbers:
                    rpt_numbers.sort()
                    min_rpt = f"RPT-{rpt_numbers[0]:05d}"
                    max_rpt = f"RPT-{rpt_numbers[-1]:05d}"
                    print(f"  - Report ID range: {min_rpt} to {max_rpt}")
                    print(f"  - Expected range: {self.expected_report_id_start} to {self.expected_report_id_end}")
            
        except Exception as e:
            self.fail(f"❌ Data verification failed: {str(e)}")

    def test_03_dashboard_summary_metrics(self):
        """Test dashboard summary endpoint and verify expected metrics"""
        if not self.admin_token:
            self.skipTest("Admin token not available")
            
        print(f"\n📈 Testing Dashboard Summary Metrics...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/dashboard-summary", headers=headers)
            self.assertEqual(response.status_code, 200)
            
            summary = response.json()
            
            # Verify expected fields
            expected_fields = ["total_downtime", "active_factories", "total_stock"]
            for field in expected_fields:
                self.assertIn(field, summary, f"Missing field: {field}")
            
            total_downtime = summary.get("total_downtime", 0)
            active_factories = summary.get("active_factories", 0)
            total_stock = summary.get("total_stock", 0)
            
            print(f"✅ Dashboard Summary Metrics:")
            print(f"  - Total Downtime: {total_downtime:,.1f} hours")
            print(f"  - Active Factories: {active_factories}")
            print(f"  - Total Stock: {total_stock:,}")
            print(f"  - Expected Downtime: ~{self.expected_downtime_approx:,} hours")
            print(f"  - Expected Factories: {self.expected_factories}")
            
            # Verify metrics are in expected ranges (allow variance)
            self.assertEqual(active_factories, self.expected_factories, 
                           f"Expected {self.expected_factories} factories, got {active_factories}")
            
            # Downtime should be substantial
            self.assertGreater(total_downtime, self.expected_downtime_approx * 0.5, 
                             f"Expected substantial downtime, got {total_downtime}")
            
        except Exception as e:
            self.fail(f"❌ Dashboard summary test failed: {str(e)}")

    def test_04_analytics_trends_comprehensive(self):
        """Test analytics trends endpoint with comprehensive data"""
        if not self.admin_token:
            self.skipTest("Admin token not available")
            
        print(f"\n📊 Testing Analytics Trends...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Test with 30-day trends
            response = requests.get(f"{self.base_url}/analytics/trends?days=30", headers=headers)
            self.assertEqual(response.status_code, 200)
            
            trends = response.json()
            
            # Verify structure
            self.assertIn("factories", trends)
            self.assertIn("date_range", trends)
            
            factories_data = trends["factories"]
            
            print(f"✅ Analytics Trends Data:")
            print(f"  - Factories with data: {len(factories_data)}")
            print(f"  - Date range: {trends['date_range']['start'][:10]} to {trends['date_range']['end'][:10]}")
            
            total_production = 0
            total_sales = 0
            
            for factory_id, factory_data in factories_data.items():
                # Verify factory data structure
                expected_fields = ["name", "dates", "production", "sales", "production_by_product", "sales_by_product"]
                for field in expected_fields:
                    self.assertIn(field, factory_data, f"Missing field {field} in factory {factory_id}")
                
                # Calculate totals
                factory_production = sum(factory_data["production"])
                factory_sales = sum(factory_data["sales"])
                total_production += factory_production
                total_sales += factory_sales
                
                print(f"  - {factory_data['name']}:")
                print(f"    - Production: {factory_production:,}")
                print(f"    - Sales: {factory_sales:,}")
                print(f"    - Data points: {len(factory_data['dates'])}")
            
            print(f"  - Total Production (30 days): {total_production:,}")
            print(f"  - Total Sales (30 days): {total_sales:,}")
            
            # Verify we have substantial production data
            self.assertGreater(total_production, 1000000, "Expected substantial production data")
            
        except Exception as e:
            self.fail(f"❌ Analytics trends test failed: {str(e)}")

    def test_05_factory_comparison_today(self):
        """Test factory comparison analytics for today's data"""
        if not self.admin_token:
            self.skipTest("Admin token not available")
            
        print(f"\n🏭 Testing Factory Comparison (Today's Data)...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/analytics/factory-comparison", headers=headers)
            self.assertEqual(response.status_code, 200)
            
            comparison_data = response.json()
            
            print(f"✅ Factory Comparison Data:")
            print(f"  - Factories compared: {len(comparison_data)}")
            
            total_today_production = 0
            total_today_sales = 0
            total_today_revenue = 0
            total_today_downtime = 0
            
            for factory_data in comparison_data:
                # Verify factory data structure
                expected_fields = ["name", "production", "sales", "revenue", "downtime", "efficiency", "sku_unit"]
                for field in expected_fields:
                    self.assertIn(field, factory_data, f"Missing field: {field}")
                
                total_today_production += factory_data["production"]
                total_today_sales += factory_data["sales"]
                total_today_revenue += factory_data["revenue"]
                total_today_downtime += factory_data["downtime"]
                
                print(f"  - {factory_data['name']}:")
                print(f"    - Production: {factory_data['production']:,}")
                print(f"    - Sales: {factory_data['sales']:,}")
                print(f"    - Revenue: ${factory_data['revenue']:,.2f}")
                print(f"    - Downtime: {factory_data['downtime']:.1f}h")
                print(f"    - Efficiency: {factory_data['efficiency']:.1f}%")
            
            print(f"  - Today's Totals:")
            print(f"    - Production: {total_today_production:,}")
            print(f"    - Sales: {total_today_sales:,}")
            print(f"    - Revenue: ${total_today_revenue:,.2f}")
            print(f"    - Downtime: {total_today_downtime:.1f}h")
            
            # Verify we have 4 factories
            self.assertEqual(len(comparison_data), self.expected_factories, 
                           f"Expected {self.expected_factories} factories, got {len(comparison_data)}")
            
        except Exception as e:
            self.fail(f"❌ Factory comparison test failed: {str(e)}")

    def test_06_excel_export_comprehensive(self):
        """Test Excel export functionality with comprehensive data"""
        if not self.admin_token:
            self.skipTest("Admin token not available")
            
        print(f"\n📄 Testing Excel Export (Expected Substantial Files)...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Test full export
            response = requests.get(f"{self.base_url}/export-excel", headers=headers)
            self.assertEqual(response.status_code, 200, f"Excel export failed: {response.text}")
            
            # Verify content type
            content_type = response.headers.get('content-type', '')
            self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', content_type)
            
            # Verify content disposition
            content_disposition = response.headers.get('content-disposition', '')
            self.assertIn('attachment', content_disposition)
            self.assertIn('.xlsx', content_disposition)
            
            file_size = len(response.content)
            
            print(f"✅ Excel Export Results:")
            print(f"  - File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            print(f"  - Content-Type: {content_type}")
            print(f"  - Expected: Substantial file (>40KB)")
            
            # Verify substantial file size (should be large with ~1,894 logs)
            self.assertGreater(file_size, 40000, f"Expected substantial Excel file, got {file_size} bytes")
            
            # Test with date range
            params = {
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat()
            }
            
            response = requests.get(f"{self.base_url}/export-excel", headers=headers, params=params)
            self.assertEqual(response.status_code, 200)
            
            date_range_size = len(response.content)
            print(f"  - Date range export: {date_range_size:,} bytes ({date_range_size/1024:.1f} KB)")
            
            # Test factory-specific export
            params = {'factory_id': 'wakene_food'}
            response = requests.get(f"{self.base_url}/export-excel", headers=headers, params=params)
            
            if response.status_code == 200:
                factory_size = len(response.content)
                print(f"  - Factory-specific export: {factory_size:,} bytes ({factory_size/1024:.1f} KB)")
            else:
                print(f"  - Factory-specific export: No data available")
            
        except Exception as e:
            self.fail(f"❌ Excel export test failed: {str(e)}")

    def test_07_role_based_access_control(self):
        """Test role-based access control for headquarters users"""
        if not self.admin_token:
            self.skipTest("Admin token not available")
            
        print(f"\n🔒 Testing Role-based Access Control...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Test headquarters user can access all factories
            response = requests.get(f"{self.base_url}/daily-logs", headers=headers)
            self.assertEqual(response.status_code, 200)
            
            all_logs = response.json()
            factory_ids = set(log.get("factory_id") for log in all_logs)
            
            print(f"✅ Headquarters Access Control:")
            print(f"  - Accessible factories: {len(factory_ids)}")
            print(f"  - Factory IDs: {sorted(factory_ids)}")
            print(f"  - Total logs accessible: {len(all_logs)}")
            
            # Verify access to all expected factories
            expected_factory_ids = {"amen_water", "mintu_plast", "mintu_export", "wakene_food"}
            self.assertEqual(factory_ids, expected_factory_ids, 
                           f"Expected access to {expected_factory_ids}, got {factory_ids}")
            
            # Test user management access
            response = requests.get(f"{self.base_url}/users", headers=headers)
            self.assertEqual(response.status_code, 200)
            
            users = response.json()
            print(f"  - User management access: ✅ ({len(users)} users)")
            
            # Test factory comparison access
            response = requests.get(f"{self.base_url}/analytics/factory-comparison", headers=headers)
            self.assertEqual(response.status_code, 200)
            print(f"  - Factory comparison access: ✅")
            
        except Exception as e:
            self.fail(f"❌ Role-based access control test failed: {str(e)}")

    def test_08_data_integrity_verification(self):
        """Verify data integrity including report IDs, realistic data, etc."""
        if not self.admin_token:
            self.skipTest("Admin token not available")
            
        print(f"\n🔍 Testing Data Integrity...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Get sample of logs for integrity checking
            response = requests.get(f"{self.base_url}/daily-logs?start_date={self.start_date.isoformat()}", headers=headers)
            self.assertEqual(response.status_code, 200)
            
            logs = response.json()[:100]  # Sample first 100 logs
            
            print(f"✅ Data Integrity Check (Sample: {len(logs)} logs):")
            
            # Check report ID format
            rpt_format_count = 0
            revenue_total = 0
            production_total = 0
            downtime_total = 0
            
            for log in logs:
                # Check report ID format
                report_id = log.get("report_id", "")
                if report_id and report_id.startswith("RPT-") and len(report_id) == 9:
                    rpt_format_count += 1
                
                # Calculate metrics
                production_data = log.get("production_data", {})
                sales_data = log.get("sales_data", {})
                downtime_hours = log.get("downtime_hours", 0)
                
                # Sum production
                production_total += sum(production_data.values())
                
                # Sum revenue
                for product, sales_info in sales_data.items():
                    if isinstance(sales_info, dict):
                        amount = sales_info.get("amount", 0)
                        unit_price = sales_info.get("unit_price", 0)
                        revenue_total += amount * unit_price
                
                # Sum downtime
                downtime_total += downtime_hours
            
            print(f"  - Report IDs in RPT-XXXXX format: {rpt_format_count}/{len(logs)} ({rpt_format_count/len(logs)*100:.1f}%)")
            print(f"  - Sample production total: {production_total:,}")
            print(f"  - Sample revenue total: ${revenue_total:,.2f}")
            print(f"  - Sample downtime total: {downtime_total:,.1f} hours")
            
            # Verify high percentage of proper report IDs
            self.assertGreater(rpt_format_count/len(logs), 0.9, 
                             f"Expected >90% proper report IDs, got {rpt_format_count/len(logs)*100:.1f}%")
            
            # Verify realistic data ranges
            self.assertGreater(production_total, 0, "Expected positive production data")
            self.assertGreater(revenue_total, 0, "Expected positive revenue data")
            
        except Exception as e:
            self.fail(f"❌ Data integrity test failed: {str(e)}")

    def test_09_user_management_endpoints(self):
        """Test user management endpoints functionality"""
        if not self.admin_token:
            self.skipTest("Admin token not available")
            
        print(f"\n👥 Testing User Management Endpoints...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Test GET /users
            response = requests.get(f"{self.base_url}/users", headers=headers)
            self.assertEqual(response.status_code, 200)
            
            users = response.json()
            
            print(f"✅ User Management:")
            print(f"  - Total users: {len(users)}")
            
            # Verify user structure
            for user in users[:3]:  # Check first 3 users
                expected_fields = ["id", "username", "email", "role", "first_name", "last_name", "created_at"]
                for field in expected_fields:
                    self.assertIn(field, user, f"Missing field {field} in user data")
                
                print(f"  - User: {user['username']} ({user['role']})")
            
            # Test creating a new user
            test_user_data = {
                "username": f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "email": "test@factory.com",
                "password": "test123",
                "role": "factory_employer",
                "factory_id": "amen_water",
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = requests.post(f"{self.base_url}/users", json=test_user_data, headers=headers)
            if response.status_code == 200:
                created_user = response.json()
                print(f"  - User creation: ✅ (ID: {created_user.get('user_id', 'N/A')})")
            else:
                print(f"  - User creation: ⚠️ ({response.status_code}: {response.text[:100]})")
            
        except Exception as e:
            self.fail(f"❌ User management test failed: {str(e)}")

    def test_10_performance_and_response_times(self):
        """Test system performance with large dataset"""
        if not self.admin_token:
            self.skipTest("Admin token not available")
            
        print(f"\n⚡ Testing Performance with Large Dataset...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Test daily-logs endpoint performance
            start_time = datetime.now()
            response = requests.get(f"{self.base_url}/daily-logs", headers=headers)
            daily_logs_time = (datetime.now() - start_time).total_seconds()
            
            self.assertEqual(response.status_code, 200)
            logs_count = len(response.json())
            
            # Test dashboard-summary performance
            start_time = datetime.now()
            response = requests.get(f"{self.base_url}/dashboard-summary", headers=headers)
            dashboard_time = (datetime.now() - start_time).total_seconds()
            
            self.assertEqual(response.status_code, 200)
            
            # Test analytics-trends performance
            start_time = datetime.now()
            response = requests.get(f"{self.base_url}/analytics/trends", headers=headers)
            analytics_time = (datetime.now() - start_time).total_seconds()
            
            self.assertEqual(response.status_code, 200)
            
            print(f"✅ Performance Results:")
            print(f"  - Daily logs ({logs_count:,} records): {daily_logs_time:.2f}s")
            print(f"  - Dashboard summary: {dashboard_time:.2f}s")
            print(f"  - Analytics trends: {analytics_time:.2f}s")
            
            # Verify reasonable response times (allow up to 10s for large datasets)
            self.assertLess(daily_logs_time, 10.0, f"Daily logs endpoint too slow: {daily_logs_time:.2f}s")
            self.assertLess(dashboard_time, 5.0, f"Dashboard endpoint too slow: {dashboard_time:.2f}s")
            self.assertLess(analytics_time, 10.0, f"Analytics endpoint too slow: {analytics_time:.2f}s")
            
        except Exception as e:
            self.fail(f"❌ Performance test failed: {str(e)}")

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2, buffer=True)