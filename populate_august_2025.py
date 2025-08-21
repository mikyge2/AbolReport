#!/usr/bin/env python3
"""
Script to populate the database with reports from August 1, 2025 till August 21, 2025 for all factories
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timedelta, date
import random
import uuid

# Database configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = "test_database"

# Factory configuration
FACTORIES = {
    "wakene_food": {
        "name": "Wakene Food Complex",
        "products": ["Flour", "Fruska (Wheat Bran)", "Fruskelo (Wheat Germ)"],
        "sku_unit": "Quintal"
    },
    "amen_water": {
        "name": "Amen (Victory) Water",
        "products": ["360ml", "600ml", "1000ml", "2000ml"],
        "sku_unit": "Paket"
    },
    "mintu_plast": {
        "name": "Mintu Plast",
        "products": [
            "Preform 27g/28mm", "Preform 28g/28mm", "Preform 42g/28mm", 
            "Preform 24g/28mm", "Preform 20g/28mm", "Preform 39g/30mm",
            "Preform 17.5g/30mm", "Preform 15g/30mm", "Cap 1.75g/30mm", "Cap 2.6g/28mm"
        ],
        "sku_unit": "Pieces"
    },
    "mintu_export": {
        "name": "Mintu Export",
        "products": ["Sesame", "Niger", "Chickpea", "Red Bean"],
        "sku_unit": "Quintal"
    }
}

DOWNTIME_REASONS = [
    "Equipment Maintenance", "Power Outage", "Raw Material shortage", "Quality Control",
    "Equipment Failure", "Planned Maintenance", "Staff Training", "Cleaning Schedule",
    "Setup Change", "Emergency Repair", "Holiday Break", "Shift Change",
    "Safety Check", "Inventory Management", "Transportation Delay", "Weather Issues"
]

# Different users for variety
USERS = ["admin", "factory_manager", "production_lead", "quality_inspector", "shift_supervisor"]

async def get_next_report_id(db):
    """Generate next sequential report ID"""
    # Find the highest existing report ID
    pipeline = [
        {"$match": {"report_id": {"$regex": "^RPT-\\d{5}$"}}},
        {"$addFields": {
            "report_number": {
                "$toInt": {"$substr": ["$report_id", 4, -1]}
            }
        }},
        {"$sort": {"report_number": -1}},
        {"$limit": 1}
    ]
    
    result = await db.daily_logs.aggregate(pipeline).to_list(length=1)
    
    if result:
        next_number = result[0]["report_number"] + 1
    else:
        next_number = 10000  # Start from RPT-10000
    
    return f"RPT-{next_number:05d}", next_number

async def generate_august_2025_data():
    """Generate daily logs from August 1, 2025 till August 21, 2025 for all factories"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🚀 Starting data generation for August 1-21, 2025...")
    
    # Delete existing data for August 2025 to avoid duplicates
    start_date = datetime(2025, 8, 1)
    end_date = datetime(2025, 8, 21)
    
    delete_result = await db.daily_logs.delete_many({
        "date": {"$gte": start_date, "$lte": end_date}
    })
    print(f"✅ Cleared {delete_result.deleted_count} existing logs for August 1-21, 2025")
    
    total_days = (end_date - start_date).days + 1
    print(f"📅 Generating data for {total_days} days ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
    
    logs_created = 0
    # Get starting report number
    _, current_report_number = await get_next_report_id(db)
    
    # Iterate through each day
    current_date = start_date
    while current_date <= end_date:
        # Skip some weekend days occasionally (15% chance)
        if current_date.weekday() >= 5 and random.random() < 0.15:
            current_date += timedelta(days=1)
            continue
        
        # Generate 1-2 logs per factory per day (some factories may not operate every day)
        for factory_id, factory_info in FACTORIES.items():
            
            # 90% chance factory operates on this day (higher than historical data)
            if random.random() < 0.10:
                continue
                
            # Generate 1-2 logs per factory per day
            logs_per_day = random.randint(1, 2)
            
            for log_num in range(logs_per_day):
                # Generate report ID
                report_id = f"RPT-{current_report_number:05d}"
                current_report_number += 1
                
                # Generate realistic production data for August 2025 (current production levels)
                production_data = {}
                for product in factory_info["products"]:
                    # Base production with summer variation
                    summer_factor = 1.1  # 10% higher production in summer
                    
                    if factory_id == "wakene_food":
                        base_production = random.randint(90, 280) * summer_factor
                    elif factory_id == "amen_water":
                        # Higher production in summer months
                        base_production = random.randint(2500, 9000) * summer_factor
                    elif factory_id == "mintu_plast":
                        base_production = random.randint(18000, 70000) * summer_factor
                    else:  # mintu_export
                        # Export business varies more
                        base_production = random.randint(35, 180) * summer_factor
                    
                    production_data[product] = max(15, int(base_production))
                
                # Generate sales data (75-95% of production - higher efficiency in 2025)
                sales_data = {}
                for product in factory_info["products"]:
                    production_amount = production_data[product]
                    sales_percentage = random.uniform(0.75, 0.95)
                    sales_amount = int(production_amount * sales_percentage)
                    
                    # Generate unit prices for 2025 (adjusted for inflation)
                    if factory_id == "wakene_food":
                        base_price = random.uniform(30, 45)  # Increased from 2024 prices
                    elif factory_id == "amen_water":
                        base_price = random.uniform(0.6, 1.8)  # Increased from 2024 prices
                    elif factory_id == "mintu_plast":
                        base_price = random.uniform(0.06, 0.18)  # Increased from 2024 prices
                    else:  # mintu_export
                        base_price = random.uniform(900, 1400)  # Increased from 2024 prices
                    
                    sales_data[product] = {
                        "amount": sales_amount,
                        "unit_price": round(base_price, 2)
                    }
                
                # Generate downtime data (more efficient in 2025)
                if current_date.weekday() == 0:  # Monday - maintenance day
                    base_downtime = random.uniform(1, 6)
                elif current_date.weekday() >= 5:  # Weekend - reduced operation
                    base_downtime = random.uniform(0, 3)
                else:  # Regular weekdays
                    base_downtime = random.uniform(0.2, 4)
                
                total_downtime = round(base_downtime, 1)
                downtime_reasons = []
                
                if total_downtime > 0:
                    # Generate 1-3 downtime reasons
                    num_reasons = min(random.randint(1, 3), len(DOWNTIME_REASONS))
                    selected_reasons = random.sample(DOWNTIME_REASONS, num_reasons)
                    
                    remaining_hours = total_downtime
                    for i, reason in enumerate(selected_reasons):
                        if i == len(selected_reasons) - 1:
                            hours = remaining_hours
                        else:
                            max_hours = min(remaining_hours - 0.3, remaining_hours * 0.7)
                            hours = random.uniform(0.2, max_hours) if max_hours > 0.2 else remaining_hours
                            remaining_hours -= hours
                        
                        downtime_reasons.append({
                            "reason": reason,
                            "hours": round(hours, 1)
                        })
                
                # Generate stock data with realistic inventory patterns for 2025
                stock_data = {}
                for product in factory_info["products"]:
                    production_amount = production_data[product]
                    sales_amount = sales_data[product]["amount"]
                    
                    # Stock varies based on factory type - higher inventory levels in 2025
                    if factory_id == "mintu_plast":
                        base_stock = random.randint(15000, 50000)
                    elif factory_id == "amen_water":
                        base_stock = random.randint(4000, 20000)
                    elif factory_id == "wakene_food":
                        base_stock = random.randint(120, 600)
                    else:  # mintu_export
                        base_stock = random.randint(60, 400)
                    
                    # Add some relationship to production vs sales
                    inventory_change = production_amount - sales_amount
                    stock_data[product] = max(0, base_stock + inventory_change)
                
                # Select random user
                created_by = random.choice(USERS)
                
                # Create time with some variation throughout the day
                log_time = current_date.replace(
                    hour=random.randint(6, 22),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
                
                # Create daily log
                daily_log = {
                    "id": str(uuid.uuid4()),
                    "report_id": report_id,
                    "factory_id": factory_id,
                    "date": log_time,
                    "production_data": production_data,
                    "sales_data": sales_data,
                    "downtime_hours": total_downtime,
                    "downtime_reasons": downtime_reasons,
                    "stock_data": stock_data,
                    "created_by": created_by,
                    "created_at": datetime.utcnow()
                }
                
                await db.daily_logs.insert_one(daily_log)
                logs_created += 1
                
                # Progress indicator every 50 logs
                if logs_created % 50 == 0:
                    progress_date = current_date.strftime('%Y-%m-%d')
                    print(f"📊 Generated {logs_created} logs... (currently at {progress_date})")
        
        current_date += timedelta(days=1)
    
    print(f"\n🎉 Successfully created {logs_created} daily logs for August 1-21, 2025!")
    print(f"📈 Data spans {total_days} days across {len(FACTORIES)} factories")
    print(f"🏭 Factories: {', '.join([f['name'] for f in FACTORIES.values()])}")
    
    # Generate some statistics for the new data
    total_production = 0
    total_revenue = 0
    total_downtime = 0
    
    # Get only the logs we just created
    new_logs = await db.daily_logs.find({
        "date": {"$gte": start_date, "$lte": end_date}
    }).to_list(length=None)
    
    for log in new_logs:
        total_production += sum(log.get("production_data", {}).values())
        total_downtime += log.get("downtime_hours", 0)
        for product_sales in log.get("sales_data", {}).values():
            total_revenue += product_sales.get("amount", 0) * product_sales.get("unit_price", 0)
    
    print(f"\n📊 AUGUST 2025 STATISTICS:")
    print(f"   💰 Total Revenue: ${total_revenue:,.2f}")
    print(f"   🏭 Total Production: {total_production:,} units")
    print(f"   ⏰ Total Downtime: {total_downtime:,.1f} hours")
    print(f"   📋 Report ID Range: RPT-{current_report_number-logs_created:05d} to RPT-{current_report_number-1:05d}")
    
    client.close()

async def main():
    print("🚀 Starting August 2025 factory data generation...")
    print("📅 Generating data from August 1, 2025 to August 21, 2025")
    await generate_august_2025_data()
    print("✅ August 2025 data generation completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())