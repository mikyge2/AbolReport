#!/usr/bin/env python3
"""
Script to update existing daily logs with report IDs
"""
import asyncio
import os
import uuid
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def update_logs_with_report_ids():
    """Update all existing daily logs to have report_id field"""
    print("Starting update of existing daily logs with report IDs...")
    
    # Find all logs without report_id
    logs_without_report_id = await db.daily_logs.find({"report_id": {"$exists": False}}).to_list(1000)
    
    print(f"Found {len(logs_without_report_id)} logs without report IDs")
    
    if not logs_without_report_id:
        print("All logs already have report IDs!")
        return
    
    # Update each log with a unique report_id
    updated_count = 0
    for log in logs_without_report_id:
        report_id = str(uuid.uuid4())
        result = await db.daily_logs.update_one(
            {"_id": log["_id"]},
            {"$set": {"report_id": report_id}}
        )
        if result.modified_count > 0:
            updated_count += 1
    
    print(f"Successfully updated {updated_count} logs with report IDs")

async def main():
    try:
        await update_logs_with_report_ids()
        print("Update completed successfully!")
    except Exception as e:
        print(f"Error updating logs: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())