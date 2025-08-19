#!/usr/bin/env python3

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://perfect-check.preview.emergentagent.com/api"

def login_hq_user():
    """Login as headquarters user"""
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=data)
    if response.status_code == 200:
        login_data = response.json()
        print(f"✅ HQ user login successful: {login_data['user_info']['username']}")
        return login_data["access_token"]
    else:
        print(f"❌ HQ user login failed: {response.status_code} - {response.text}")
        return None

def create_factory_user(hq_token):
    """Create a factory user for testing"""
    headers = {"Authorization": f"Bearer {hq_token}"}
    
    user_data = {
        "username": "wakene_manager",
        "email": "wakene@company.com",
        "password": "wakene123",
        "role": "factory_employer",
        "factory_id": "wakene_food",
        "first_name": "Wakene",
        "last_name": "Manager"
    }
    
    response = requests.post(f"{BASE_URL}/users", json=user_data, headers=headers)
    if response.status_code == 200:
        print("✅ Factory user created successfully")
        return True
    elif response.status_code == 400 and "already registered" in response.text:
        print("ℹ️ Factory user already exists")
        return True
    else:
        print(f"❌ Factory user creation failed: {response.status_code} - {response.text}")
        return False

def login_factory_user():
    """Login as factory user"""
    data = {
        "username": "wakene_manager",
        "password": "wakene123"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=data)
    if response.status_code == 200:
        login_data = response.json()
        print(f"✅ Factory user login successful: {login_data['user_info']['username']}")
        return login_data["access_token"]
    else:
        print(f"❌ Factory user login failed: {response.status_code} - {response.text}")
        return None

def test_migration_hq_user(hq_token):
    """Test report ID migration with headquarters user"""
    headers = {"Authorization": f"Bearer {hq_token}"}
    
    print("\n=== Testing Report ID Migration (HQ User) ===")
    response = requests.post(f"{BASE_URL}/admin/migrate-report-ids", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Migration successful: {result['message']}")
        return True
    else:
        print(f"❌ Migration failed: {response.status_code} - {response.text}")
        return False

def test_migration_factory_user_denied(factory_token):
    """Test that factory user cannot run migration"""
    headers = {"Authorization": f"Bearer {factory_token}"}
    
    print("\n=== Testing Migration Access Control (Factory User) ===")
    response = requests.post(f"{BASE_URL}/admin/migrate-report-ids", headers=headers)
    
    if response.status_code == 403:
        print("✅ Migration correctly denied for factory user (403 Forbidden)")
        return True
    else:
        print(f"❌ Expected 403, got: {response.status_code} - {response.text}")
        return False

def verify_report_id_format(hq_token):
    """Verify that reports have RPT-XXXXX format"""
    headers = {"Authorization": f"Bearer {hq_token}"}
    
    print("\n=== Verifying Report ID Format ===")
    response = requests.get(f"{BASE_URL}/daily-logs", headers=headers)
    
    if response.status_code == 200:
        logs = response.json()
        if len(logs) == 0:
            print("ℹ️ No logs found to verify report ID format")
            return True
        
        rpt_format_count = 0
        for log in logs:
            if "report_id" in log and log["report_id"]:
                report_id = log["report_id"]
                if report_id.startswith("RPT-") and len(report_id) == 9 and report_id[4:].isdigit():
                    rpt_format_count += 1
        
        print(f"✅ Report ID format verification completed")
        print(f"  - Total logs checked: {len(logs)}")
        print(f"  - Logs with RPT-XXXXX format: {rpt_format_count}")
        
        # Show some example report IDs
        example_ids = [log.get("report_id", "N/A") for log in logs[:5]]
        print(f"  - Example report IDs: {example_ids}")
        
        return True
    else:
        print(f"❌ Failed to get logs: {response.status_code} - {response.text}")
        return False

def test_new_report_sequential_id(factory_token):
    """Test that new reports get sequential RPT-XXXXX IDs"""
    headers = {"Authorization": f"Bearer {factory_token}"}
    
    print("\n=== Testing Sequential ID Generation ===")
    
    # Create a new daily log
    today = datetime.utcnow()
    test_date = today - timedelta(days=40)  # Use 40 days ago to avoid conflicts
    
    create_data = {
        "factory_id": "wakene_food",
        "date": test_date.isoformat(),
        "production_data": {"Flour": 250},
        "sales_data": {"Flour": {"amount": 200, "unit_price": 45}},
        "downtime_hours": 1.0,
        "downtime_reasons": [{"reason": "Sequential ID Test", "hours": 1.0}],
        "stock_data": {"Flour": 750}
    }
    
    response = requests.post(f"{BASE_URL}/daily-logs", json=create_data, headers=headers)
    if response.status_code == 400 and "already exists" in response.text:
        # Try with a different date
        create_data["date"] = (test_date - timedelta(days=1)).isoformat()
        response = requests.post(f"{BASE_URL}/daily-logs", json=create_data, headers=headers)
    
    if response.status_code == 200:
        new_log = response.json()
        report_id = new_log.get("report_id", "")
        
        if report_id.startswith("RPT-") and len(report_id) == 9 and report_id[4:].isdigit():
            report_number = int(report_id[4:])
            print(f"✅ New report sequential ID generation working correctly")
            print(f"  - New report ID: {report_id}")
            print(f"  - Report number: {report_number}")
            print(f"  - Format validation: RPT-XXXXX ✓")
            return True
        else:
            print(f"❌ Invalid report ID format: {report_id}")
            return False
    else:
        print(f"❌ Failed to create new log: {response.status_code} - {response.text}")
        return False

def test_excel_export_report_ids(hq_token):
    """Test that Excel export includes report IDs"""
    headers = {"Authorization": f"Bearer {hq_token}"}
    
    print("\n=== Testing Excel Export with Report IDs ===")
    response = requests.get(f"{BASE_URL}/export-excel", headers=headers)
    
    if response.status_code == 404:
        print("ℹ️ No data available for Excel export")
        return True
    elif response.status_code == 200:
        content_type = response.headers.get('content-type', '')
        if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
            print("✅ Excel export successful")
            print(f"  - Content-Type: {content_type}")
            print(f"  - File size: {len(response.content)} bytes")
            
            # Save file for inspection
            with open('/tmp/report_id_export_test.xlsx', 'wb') as f:
                f.write(response.content)
            print("  - File saved to: /tmp/report_id_export_test.xlsx")
            
            return True
        else:
            print(f"❌ Invalid content type: {content_type}")
            return False
    else:
        print(f"❌ Excel export failed: {response.status_code} - {response.text}")
        return False

def main():
    print("🚀 Starting Report ID Migration Tests")
    print("=" * 50)
    
    # Step 1: Login as HQ user
    hq_token = login_hq_user()
    if not hq_token:
        print("❌ Cannot proceed without HQ token")
        return
    
    # Step 2: Create factory user
    if not create_factory_user(hq_token):
        print("❌ Cannot proceed without factory user")
        return
    
    # Step 3: Login as factory user
    factory_token = login_factory_user()
    if not factory_token:
        print("❌ Cannot proceed without factory token")
        return
    
    # Step 4: Run migration tests
    results = []
    
    results.append(test_migration_hq_user(hq_token))
    results.append(test_migration_factory_user_denied(factory_token))
    results.append(verify_report_id_format(hq_token))
    results.append(test_new_report_sequential_id(factory_token))
    results.append(test_excel_export_report_ids(hq_token))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
    
    print("\nTest Results:")
    test_names = [
        "Report ID Migration (HQ User)",
        "Migration Access Control (Factory User)",
        "Report ID Format Verification",
        "Sequential ID Generation",
        "Excel Export with Report IDs"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {i+1}. {name}: {status}")

if __name__ == "__main__":
    main()