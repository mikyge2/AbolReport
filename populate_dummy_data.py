#!/usr/bin/env python3
"""
Script to populate the database with dummy daily logs for testing graphs
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timedelta
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
    "Machine maintenance",
    "Power outage",
    "Raw material shortage",
    "Quality control",
    "Equipment failure",
    "Planned maintenance",
    "Staff training",
    "Cleaning",
    "Setup change",
    "Emergency repair"
]

async def generate_dummy_data():
    """Generate dummy daily logs for the last 30 days"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Clear existing daily logs
    await db.daily_logs.delete_many({})
    print("Cleared existing daily logs")
    
    # Generate data for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    logs_created = 0
    
    for factory_id, factory_info in FACTORIES.items():
        print(f"\nGenerating data for {factory_info['name']}...")
        
        for day in range(30):
            current_date = start_date + timedelta(days=day)
            
            # Skip some days randomly to make it more realistic
            if random.random() < 0.1:  # 10% chance to skip a day
                continue
            
            # Generate production data
            production_data = {}
            for product in factory_info["products"]:
                # Generate realistic production amounts based on factory type
                if factory_id == "wakene_food":
                    base_production = random.randint(50, 200)
                elif factory_id == "amen_water":
                    base_production = random.randint(1000, 5000)
                elif factory_id == "mintu_plast":
                    base_production = random.randint(10000, 50000)
                else:  # mintu_export
                    base_production = random.randint(20, 100)
                
                # Add some variation
                production_data[product] = base_production + random.randint(-20, 20)
            
            # Generate sales data (usually 70-90% of production)
            sales_data = {}
            for product in factory_info["products"]:
                production_amount = production_data[product]
                sales_amount = int(production_amount * random.uniform(0.7, 0.9))
                
                # Generate unit price based on factory type
                if factory_id == "wakene_food":
                    unit_price = random.uniform(25, 35)
                elif factory_id == "amen_water":
                    unit_price = random.uniform(0.5, 1.5)
                elif factory_id == "mintu_plast":
                    unit_price = random.uniform(0.05, 0.15)
                else:  # mintu_export
                    unit_price = random.uniform(800, 1200)
                
                sales_data[product] = {
                    "amount": sales_amount,
                    "unit_price": round(unit_price, 2)
                }
            
            # Generate downtime data
            total_downtime = random.uniform(0, 8)  # 0-8 hours of downtime
            downtime_reasons = []
            
            if total_downtime > 0:
                # Generate 1-3 reasons
                num_reasons = random.randint(1, min(3, len(DOWNTIME_REASONS)))
                selected_reasons = random.sample(DOWNTIME_REASONS, num_reasons)
                
                remaining_hours = total_downtime
                for i, reason in enumerate(selected_reasons):
                    if i == len(selected_reasons) - 1:
                        # Last reason gets remaining hours
                        hours = remaining_hours
                    else:
                        # Random portion of remaining hours
                        hours = random.uniform(0.5, remaining_hours - 0.5)
                        remaining_hours -= hours
                    
                    downtime_reasons.append({
                        "reason": reason,
                        "hours": round(hours, 1)
                    })
            
            # Generate stock data
            stock_data = {}
            for product in factory_info["products"]:
                production_amount = production_data[product]
                sales_amount = sales_data[product]["amount"]
                # Stock is previous stock + production - sales + some base stock
                stock_data[product] = max(0, production_amount - sales_amount + random.randint(10, 100))
            
            # Create daily log
            daily_log = {
                "id": str(uuid.uuid4()),
                "factory_id": factory_id,
                "date": current_date,
                "production_data": production_data,
                "sales_data": sales_data,
                "downtime_hours": round(total_downtime, 1),
                "downtime_reasons": downtime_reasons,
                "stock_data": stock_data,
                "created_by": "admin",
                "created_at": datetime.utcnow()
            }
            
            await db.daily_logs.insert_one(daily_log)
            logs_created += 1
    
    print(f"\n✅ Successfully created {logs_created} dummy daily logs")
    client.close()

async def main():
    print("🚀 Starting dummy data generation...")
    await generate_dummy_data()
    print("✅ Dummy data generation completed!")

if __name__ == "__main__":
    asyncio.run(main())