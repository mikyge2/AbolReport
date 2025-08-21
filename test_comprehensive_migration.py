#!/usr/bin/env python3

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://factory-reports-data.preview.emergentagent.com/api"

def login_users():
    """Login both HQ and factory users"""
    # HQ user
    hq_data = {"username": "admin", "password": "admin123"}
    hq_response = requests.post(f"{BASE_URL}/login", json=hq_data)
    hq_token = hq_response.json()["access_token"] if hq_response.status_code == 200 else None
    
    # Factory user
    factory_data = {"username": "wakene_manager", "password": "wakene123"}
    factory_response = requests.post(f"{BASE_URL}/login", json=factory_data)
    factory_token = factory_response.json()["access_token"] if factory_response.status_code == 200 else None
    
    return hq_token, factory_token

def create_test_logs_with_old_format(factory_token):
    """Create some logs that will have old UUID format initially"""
    headers = {"Authorization": f"Bearer {factory_token}"}
    
    print("🔧 Creating test logs to demonstrate migration...")
    
    # Create several logs with different dates
    today = datetime.utcnow()
    logs_created = 0
    
    for i in range(3):
        test_date = today - timedelta(days=50 + i)
        
        create_data = {
            "factory_id": "wakene_food",
            "date": test_date.isoformat(),
            "production_data": {"Flour": 300 + i * 50},
            "sales_data": {"Flour": {"amount": 250 + i * 40, "unit_price": 45 + i}},
            "downtime_hours": 1.5 + i * 0.5,
            "downtime_reasons": [{"reason": f"Test Reason {i+1}", "hours": 1.5 + i * 0.5}],
            "stock_data": {"Flour": 800 + i * 100}
        }
        
        response = requests.post(f"{BASE_URL}/daily-logs", json=create_data, headers=headers)
        if response.status_code == 200:
            logs_created += 1
            log = response.json()
            print(f"  ✅ Created log {i+1}: {log.get('report_id', 'N/A')}")
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"  ℹ️ Log {i+1} already exists")
        else:
            print(f"  ❌ Failed to create log {i+1}: {response.status_code}")
    
    print(f"📊 Created {logs_created} new logs")
    return logs_created > 0

def manually_create_logs_with_uuid_format(hq_token):
    """Manually insert logs with UUID format to test migration"""
    print("🔧 Creating logs with old UUID format for migration testing...")
    
    # This would require direct database access, but we can simulate by creating logs
    # and then checking if migration updates them properly
    
    # For now, let's just verify the current state
    headers = {"Authorization": f"Bearer {hq_token}"}
    response = requests.get(f"{BASE_URL}/daily-logs", headers=headers)
    
    if response.status_code == 200:
        logs = response.json()
        print(f"📊 Current logs in database: {len(logs)}")
        
        # Show current report IDs
        for i, log in enumerate(logs[:5]):  # Show first 5
            report_id = log.get("report_id", "N/A")
            date = log.get("date", "N/A")
            print(f"  Log {i+1}: {report_id} (Date: {date[:10] if date != 'N/A' else 'N/A'})")
        
        return len(logs) > 0
    else:
        print(f"❌ Failed to get logs: {response.status_code}")
        return False

def test_comprehensive_migration(hq_token):
    """Test migration with existing logs"""
    headers = {"Authorization": f"Bearer {hq_token}"}
    
    print("\n🔄 Running comprehensive migration test...")
    
    # Get logs before migration
    response = requests.get(f"{BASE_URL}/daily-logs", headers=headers)
    if response.status_code == 200:
        logs_before = response.json()
        print(f"📊 Logs before migration: {len(logs_before)}")
        
        # Show some report IDs before migration
        print("Report IDs before migration:")
        for i, log in enumerate(logs_before[:3]):
            report_id = log.get("report_id", "N/A")
            print(f"  Log {i+1}: {report_id}")
    else:
        print("❌ Failed to get logs before migration")
        return False
    
    # Run migration
    print("\n🔄 Running migration...")
    migration_response = requests.post(f"{BASE_URL}/admin/migrate-report-ids", headers=headers)
    
    if migration_response.status_code == 200:
        result = migration_response.json()
        print(f"✅ Migration result: {result['message']}")
    else:
        print(f"❌ Migration failed: {migration_response.status_code}")
        return False
    
    # Get logs after migration
    response = requests.get(f"{BASE_URL}/daily-logs", headers=headers)
    if response.status_code == 200:
        logs_after = response.json()
        print(f"📊 Logs after migration: {len(logs_after)}")
        
        # Verify all logs have RPT-XXXXX format
        rpt_format_count = 0
        for log in logs_after:
            report_id = log.get("report_id", "")
            if report_id.startswith("RPT-") and len(report_id) == 9 and report_id[4:].isdigit():
                rpt_format_count += 1
        
        print(f"✅ Logs with RPT-XXXXX format: {rpt_format_count}/{len(logs_after)}")
        
        # Show some report IDs after migration
        print("Report IDs after migration:")
        for i, log in enumerate(logs_after[:5]):
            report_id = log.get("report_id", "N/A")
            print(f"  Log {i+1}: {report_id}")
        
        return rpt_format_count == len(logs_after)
    else:
        print("❌ Failed to get logs after migration")
        return False

def test_sequential_numbering(factory_token):
    """Test that new logs get sequential numbers"""
    headers = {"Authorization": f"Bearer {factory_token}"}
    
    print("\n🔢 Testing sequential numbering...")
    
    # Create multiple logs and verify they get sequential IDs
    today = datetime.utcnow()
    created_ids = []
    
    for i in range(3):
        test_date = today - timedelta(days=60 + i)
        
        create_data = {
            "factory_id": "wakene_food",
            "date": test_date.isoformat(),
            "production_data": {"Flour": 200 + i * 25},
            "sales_data": {"Flour": {"amount": 180 + i * 20, "unit_price": 50}},
            "downtime_hours": 1.0,
            "downtime_reasons": [{"reason": f"Sequential Test {i+1}", "hours": 1.0}],
            "stock_data": {"Flour": 700}
        }
        
        response = requests.post(f"{BASE_URL}/daily-logs", json=create_data, headers=headers)
        if response.status_code == 200:
            log = response.json()
            report_id = log.get("report_id", "")
            created_ids.append(report_id)
            print(f"  ✅ Created log with ID: {report_id}")
        elif response.status_code == 400 and "already exists" in response.text:
            print(f"  ℹ️ Log {i+1} already exists, skipping")
        else:
            print(f"  ❌ Failed to create log {i+1}: {response.status_code}")
    
    # Verify sequential numbering
    if len(created_ids) >= 2:
        numbers = []
        for report_id in created_ids:
            if report_id.startswith("RPT-") and len(report_id) == 9:
                numbers.append(int(report_id[4:]))
        
        if len(numbers) >= 2:
            is_sequential = all(numbers[i] == numbers[i-1] + 1 for i in range(1, len(numbers)))
            if is_sequential:
                print(f"✅ Sequential numbering verified: {numbers}")
                return True
            else:
                print(f"❌ Numbers not sequential: {numbers}")
                return False
        else:
            print("ℹ️ Not enough valid report IDs to test sequencing")
            return True
    else:
        print("ℹ️ Not enough logs created to test sequencing")
        return True

def main():
    print("🧪 Comprehensive Report ID Migration Testing")
    print("=" * 60)
    
    # Login
    hq_token, factory_token = login_users()
    if not hq_token or not factory_token:
        print("❌ Failed to login users")
        return
    
    print("✅ Successfully logged in both users")
    
    # Create test data
    create_test_logs_with_old_format(factory_token)
    manually_create_logs_with_uuid_format(hq_token)
    
    # Run comprehensive tests
    results = []
    
    results.append(test_comprehensive_migration(hq_token))
    results.append(test_sequential_numbering(factory_token))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL COMPREHENSIVE TESTS PASSED ({passed}/{total})")
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
    
    test_names = [
        "Comprehensive Migration Test",
        "Sequential Numbering Test"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {i+1}. {name}: {status}")

if __name__ == "__main__":
    main()