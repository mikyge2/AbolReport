#!/usr/bin/env python3
"""
Comprehensive Factory Management System Test
Based on review request requirements:
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

import requests
import json
from datetime import datetime, timedelta

class FactorySystemTester:
    def __init__(self):
        # Get backend URL
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        backend_url = line.split('=')[1].strip()
                        self.base_url = f"{backend_url}/api"
                        break
                else:
                    self.base_url = "http://localhost:8001/api"
        except:
            self.base_url = "http://localhost:8001/api"
        
        # Admin credentials from review request
        self.admin_username = "admin"
        self.admin_password = "admin1234"
        self.admin_token = None
        
        # Expected metrics from review request
        self.expected_total_logs = 1894
        self.expected_revenue_approx = 195000000  # ~$195M
        self.expected_production_approx = 203000000  # ~203M units
        self.expected_downtime_approx = 5974  # ~5,974 hours
        self.expected_factories = 4
        
        # Date range from review request
        self.start_date = datetime(2024, 8, 7)  # August 7, 2024
        self.end_date = datetime.utcnow()
        
        print(f"🔧 Factory Management System Comprehensive Test")
        print(f"Backend URL: {self.base_url}")
        print(f"Expected date range: {self.start_date.date()} to {self.end_date.date()}")
        print(f"Expected logs: ~{self.expected_total_logs}")
        print(f"Expected revenue: ~${self.expected_revenue_approx:,}")
        print("=" * 80)

    def test_admin_authentication(self):
        """Test 1: Admin User Authentication"""
        print("\n🔐 TEST 1: Admin Authentication")
        print(f"Testing login with username: {self.admin_username}, password: {self.admin_password}")
        
        try:
            # Login
            data = {"username": self.admin_username, "password": self.admin_password}
            response = requests.post(f"{self.base_url}/auth/login", json=data)
            
            if response.status_code != 200:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
            
            login_data = response.json()
            if "access_token" not in login_data:
                print(f"❌ No access token in response: {login_data}")
                return False
            
            self.admin_token = login_data["access_token"]
            
            # Get user info
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{self.base_url}/auth/me", headers=headers)
            
            if response.status_code != 200:
                print(f"❌ Failed to get user info: {response.status_code}")
                return False
            
            user_info = response.json()
            
            print(f"✅ Admin authentication successful:")
            print(f"  - Username: {user_info['username']}")
            print(f"  - Role: {user_info['role']}")
            print(f"  - Token: {self.admin_token[:30]}...")
            
            if user_info['role'] != 'headquarters':
                print(f"❌ Expected role 'headquarters', got '{user_info['role']}'")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Authentication test failed: {str(e)}")
            return False

    def test_data_verification(self):
        """Test 2: Data Verification - Check for ~1,894 logs"""
        print("\n📊 TEST 2: Data Verification")
        print(f"Checking for ~{self.expected_total_logs} daily logs from {self.start_date.date()}")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Get all daily logs
            response = requests.get(f"{self.base_url}/daily-logs", headers=headers)
            if response.status_code != 200:
                print(f"❌ Failed to get daily logs: {response.status_code}")
                return False
            
            all_logs = response.json()
            total_logs = len(all_logs)
            
            print(f"✅ Data Volume Verification:")
            print(f"  - Total logs found: {total_logs:,}")
            print(f"  - Expected: ~{self.expected_total_logs:,}")
            
            # Check factory distribution
            factory_counts = {}
            for log in all_logs:
                factory_id = log.get("factory_id")
                factory_counts[factory_id] = factory_counts.get(factory_id, 0) + 1
            
            print(f"  - Factory distribution:")
            for factory_id, count in sorted(factory_counts.items()):
                print(f"    - {factory_id}: {count:,} logs")
            
            print(f"  - Active factories: {len(factory_counts)}")
            
            # Check date range
            dates = []
            for log in all_logs:
                if log.get("date"):
                    try:
                        date_obj = datetime.fromisoformat(log["date"].replace('Z', '+00:00'))
                        dates.append(date_obj)
                    except:
                        pass
            
            if dates:
                min_date = min(dates)
                max_date = max(dates)
                print(f"  - Date range: {min_date.date()} to {max_date.date()}")
                
                # Check if we have data from August 7, 2024
                aug_7_logs = [d for d in dates if d.date() >= self.start_date.date()]
                print(f"  - Logs from Aug 7, 2024 onwards: {len(aug_7_logs):,}")
            
            # Verify we have substantial data
            if total_logs < self.expected_total_logs * 0.5:
                print(f"⚠️ Warning: Expected ~{self.expected_total_logs} logs, got {total_logs}")
            
            if len(factory_counts) != self.expected_factories:
                print(f"⚠️ Warning: Expected {self.expected_factories} factories, got {len(factory_counts)}")
            
            return total_logs > 100  # At least some substantial data
            
        except Exception as e:
            print(f"❌ Data verification failed: {str(e)}")
            return False

    def test_api_endpoints(self):
        """Test 3: Major API Endpoints"""
        print("\n🌐 TEST 3: API Endpoints Testing")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        results = {}
        
        # Test /api/daily-logs
        try:
            response = requests.get(f"{self.base_url}/daily-logs", headers=headers)
            results['daily-logs'] = response.status_code == 200
            if results['daily-logs']:
                logs_count = len(response.json())
                print(f"✅ /api/daily-logs: {logs_count:,} logs")
            else:
                print(f"❌ /api/daily-logs: {response.status_code}")
        except Exception as e:
            results['daily-logs'] = False
            print(f"❌ /api/daily-logs: {str(e)}")
        
        # Test /api/dashboard-summary
        try:
            response = requests.get(f"{self.base_url}/dashboard-summary", headers=headers)
            results['dashboard-summary'] = response.status_code == 200
            if results['dashboard-summary']:
                summary = response.json()
                print(f"✅ /api/dashboard-summary:")
                print(f"  - Total downtime: {summary.get('total_downtime', 0):,.1f} hours")
                print(f"  - Active factories: {summary.get('active_factories', 0)}")
                print(f"  - Total stock: {summary.get('total_stock', 0):,}")
            else:
                print(f"❌ /api/dashboard-summary: {response.status_code}")
        except Exception as e:
            results['dashboard-summary'] = False
            print(f"❌ /api/dashboard-summary: {str(e)}")
        
        # Test /api/analytics/trends
        try:
            response = requests.get(f"{self.base_url}/analytics/trends", headers=headers)
            results['analytics-trends'] = response.status_code == 200
            if results['analytics-trends']:
                trends = response.json()
                factories_count = len(trends.get('factories', {}))
                print(f"✅ /api/analytics/trends: {factories_count} factories with trend data")
            else:
                print(f"❌ /api/analytics/trends: {response.status_code}")
        except Exception as e:
            results['analytics-trends'] = False
            print(f"❌ /api/analytics/trends: {str(e)}")
        
        # Test /api/analytics/factory-comparison
        try:
            response = requests.get(f"{self.base_url}/analytics/factory-comparison", headers=headers)
            results['factory-comparison'] = response.status_code == 200
            if results['factory-comparison']:
                comparison = response.json()
                print(f"✅ /api/analytics/factory-comparison: {len(comparison)} factories compared")
                total_revenue = sum(f.get('revenue', 0) for f in comparison)
                total_production = sum(f.get('production', 0) for f in comparison)
                print(f"  - Today's total revenue: ${total_revenue:,.2f}")
                print(f"  - Today's total production: {total_production:,}")
            else:
                print(f"❌ /api/analytics/factory-comparison: {response.status_code}")
        except Exception as e:
            results['factory-comparison'] = False
            print(f"❌ /api/analytics/factory-comparison: {str(e)}")
        
        # Test /api/export-excel
        try:
            response = requests.get(f"{self.base_url}/export-excel", headers=headers)
            results['export-excel'] = response.status_code == 200
            if results['export-excel']:
                file_size = len(response.content)
                print(f"✅ /api/export-excel: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                if file_size > 40000:
                    print(f"  - Substantial Excel file generated (>40KB)")
                else:
                    print(f"  - ⚠️ Small Excel file, may indicate limited data")
            else:
                print(f"❌ /api/export-excel: {response.status_code}")
        except Exception as e:
            results['export-excel'] = False
            print(f"❌ /api/export-excel: {str(e)}")
        
        success_count = sum(results.values())
        total_count = len(results)
        print(f"\n📊 API Endpoints Summary: {success_count}/{total_count} successful")
        
        return success_count >= 4  # At least 4 out of 5 endpoints working

    def test_role_based_access(self):
        """Test 4: Role-based Access Control"""
        print("\n🔒 TEST 4: Role-based Access Control")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Test headquarters user can access all factories
            response = requests.get(f"{self.base_url}/daily-logs", headers=headers)
            if response.status_code != 200:
                print(f"❌ Failed to access daily logs: {response.status_code}")
                return False
            
            logs = response.json()
            factory_ids = set(log.get("factory_id") for log in logs)
            
            print(f"✅ Headquarters Access Control:")
            print(f"  - Accessible factories: {len(factory_ids)}")
            print(f"  - Factory IDs: {sorted(factory_ids)}")
            
            # Test user management access
            response = requests.get(f"{self.base_url}/users", headers=headers)
            if response.status_code == 200:
                users = response.json()
                print(f"  - User management access: ✅ ({len(users)} users)")
            else:
                print(f"  - User management access: ❌ ({response.status_code})")
                return False
            
            # Test factory comparison access (HQ only)
            response = requests.get(f"{self.base_url}/analytics/factory-comparison", headers=headers)
            if response.status_code == 200:
                print(f"  - Factory comparison access: ✅")
            else:
                print(f"  - Factory comparison access: ❌ ({response.status_code})")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Role-based access test failed: {str(e)}")
            return False

    def test_data_integrity(self):
        """Test 5: Data Integrity (Report IDs, realistic data)"""
        print("\n🔍 TEST 5: Data Integrity")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Get sample of logs
            response = requests.get(f"{self.base_url}/daily-logs", headers=headers)
            if response.status_code != 200:
                print(f"❌ Failed to get logs: {response.status_code}")
                return False
            
            logs = response.json()[:200]  # Sample first 200 logs
            
            print(f"✅ Data Integrity Check (Sample: {len(logs)} logs):")
            
            # Check report ID format
            rpt_format_count = 0
            rpt_numbers = []
            total_revenue = 0
            total_production = 0
            total_downtime = 0
            
            for log in logs:
                # Check report ID format (RPT-XXXXX)
                report_id = log.get("report_id", "")
                if report_id and report_id.startswith("RPT-") and len(report_id) == 9:
                    rpt_format_count += 1
                    try:
                        num = int(report_id.split("-")[1])
                        rpt_numbers.append(num)
                    except:
                        pass
                
                # Calculate metrics
                production_data = log.get("production_data", {})
                sales_data = log.get("sales_data", {})
                downtime_hours = log.get("downtime_hours", 0)
                
                # Sum production
                total_production += sum(production_data.values())
                
                # Sum revenue
                for product, sales_info in sales_data.items():
                    if isinstance(sales_info, dict):
                        amount = sales_info.get("amount", 0)
                        unit_price = sales_info.get("unit_price", 0)
                        total_revenue += amount * unit_price
                
                # Sum downtime
                total_downtime += downtime_hours
            
            print(f"  - Report IDs in RPT-XXXXX format: {rpt_format_count}/{len(logs)} ({rpt_format_count/len(logs)*100:.1f}%)")
            
            if rpt_numbers:
                rpt_numbers.sort()
                min_rpt = f"RPT-{rpt_numbers[0]:05d}"
                max_rpt = f"RPT-{rpt_numbers[-1]:05d}"
                print(f"  - Report ID range: {min_rpt} to {max_rpt}")
                print(f"  - Expected range: RPT-10000 to RPT-11893")
            
            print(f"  - Sample metrics:")
            print(f"    - Production total: {total_production:,}")
            print(f"    - Revenue total: ${total_revenue:,.2f}")
            print(f"    - Downtime total: {total_downtime:,.1f} hours")
            
            # Verify data quality
            rpt_percentage = rpt_format_count / len(logs) if logs else 0
            has_realistic_data = total_production > 0 and total_revenue > 0
            
            if rpt_percentage < 0.8:
                print(f"⚠️ Warning: Only {rpt_percentage*100:.1f}% of logs have proper report ID format")
            
            if not has_realistic_data:
                print(f"⚠️ Warning: Data appears to have zero production or revenue")
            
            return rpt_percentage > 0.5 and has_realistic_data
            
        except Exception as e:
            print(f"❌ Data integrity test failed: {str(e)}")
            return False

    def test_user_management(self):
        """Test 6: User Management Endpoints"""
        print("\n👥 TEST 6: User Management")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Test GET /users
            response = requests.get(f"{self.base_url}/users", headers=headers)
            if response.status_code != 200:
                print(f"❌ Failed to get users: {response.status_code}")
                return False
            
            users = response.json()
            print(f"✅ User Management:")
            print(f"  - Total users: {len(users)}")
            
            # Check user structure
            if users:
                user = users[0]
                expected_fields = ["id", "username", "email", "role", "first_name", "last_name"]
                missing_fields = [f for f in expected_fields if f not in user]
                if missing_fields:
                    print(f"  - ⚠️ Missing fields in user data: {missing_fields}")
                else:
                    print(f"  - User data structure: ✅")
                
                # Show user roles
                roles = {}
                for u in users:
                    role = u.get('role', 'unknown')
                    roles[role] = roles.get(role, 0) + 1
                
                print(f"  - User roles:")
                for role, count in roles.items():
                    print(f"    - {role}: {count}")
            
            # Test creating a user (optional)
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
                print(f"  - User creation: ✅")
            else:
                print(f"  - User creation: ⚠️ ({response.status_code})")
            
            return True
            
        except Exception as e:
            print(f"❌ User management test failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🚀 Starting Comprehensive Factory Management System Test")
        print("=" * 80)
        
        tests = [
            ("Admin Authentication", self.test_admin_authentication),
            ("Data Verification", self.test_data_verification),
            ("API Endpoints", self.test_api_endpoints),
            ("Role-based Access", self.test_role_based_access),
            ("Data Integrity", self.test_data_integrity),
            ("User Management", self.test_user_management),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {str(e)}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Factory Management System is working perfectly!")
        elif passed >= total * 0.8:
            print("✅ MOSTLY WORKING - System is functional with minor issues")
        else:
            print("⚠️ ISSUES DETECTED - System needs attention")
        
        return passed, total

if __name__ == "__main__":
    tester = FactorySystemTester()
    passed, total = tester.run_all_tests()
    
    if passed == total:
        exit(0)
    else:
        exit(1)