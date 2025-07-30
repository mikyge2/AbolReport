#!/usr/bin/env python3
"""
Script to populate today's dummy data for all four factories
"""

import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import random

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = "test_database"

# Factory configuration matching the backend
FACTORIES = {
    "amen_water": {
        "name": "Amen (Victory) Water",
        "products": ["Bottle 500ml", "Bottle 1L", "Bottle 1.5L", "Cup 200ml"],
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
        "products": ["Export Package A", "Export Package B", "Export Package C"],
        "sku_unit": "Container"
    },
    "wakene_food": {
        "name": "Wakene Food Complex", 
        "products": ["Food Item 1", "Food Item 2", "Food Item 3", "Food Item 4"],
        "sku_unit": "Kg"
    }
}

# Sample users
USERS = ["admin", "wakene_manager"]

# Sample downtime reasons
DOWNTIME_REASONS = [
    "Equipment Maintenance", "Power Outage", "Material Shortage", 
    "Staff Training", "Quality Check", "Machine Setup", "Cleaning"
]

async def populate_today_data():
    """Populate today's data for all factories"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🚀 Creating today's dummy data for all factories...")
    
    today = datetime.utcnow().replace(hour=random.randint(8, 16), minute=random.randint(0, 59), second=0, microsecond=0)
    logs_created = 0
    
    # Create 1-2 logs for each factory today
    for factory_id, factory_info in FACTORIES.items():
        logs_for_factory = random.randint(1, 2)
        
        for log_num in range(logs_for_factory):
            # Pick a random user
            user = random.choice(USERS)
            
            # Generate production data for this factory's products
            production_data = {}
            for product in factory_info["products"]:
                # Generate realistic production numbers based on product type
                if "preform" in product.lower():
                    base_production = random.randint(10000, 18000)  # Higher for preforms
                elif "cap" in product.lower():
                    base_production = random.randint(8000, 14000)  # Medium for caps
                elif factory_id == "amen_water":
                    base_production = random.randint(1500, 6000)   # Water bottles
                elif factory_id == "wakene_food":
                    base_production = random.randint(80, 250)      # Food items
                else:  # mintu_export
                    base_production = random.randint(30, 120)      # Export packages
                
                # Add some variance
                production_data[product] = base_production + random.randint(-100, 100)
            
            # Generate sales data (usually 70-90% of production)
            sales_data = {}
            for product, production_qty in production_data.items():
                sales_percentage = random.uniform(0.75, 0.95)
                sales_amount = int(production_qty * sales_percentage)
                
                # Generate unit price based on factory type
                if factory_id == "wakene_food":
                    unit_price = random.uniform(28, 38)
                elif factory_id == "amen_water":
                    unit_price = random.uniform(0.8, 1.8)
                elif factory_id == "mintu_plast":
                    unit_price = random.uniform(0.08, 0.18)
                else:  # mintu_export
                    unit_price = random.uniform(900, 1300)
                
                sales_data[product] = {
                    "amount": sales_amount,
                    "unit_price": round(unit_price, 2)
                }
            
            # Generate stock data (remaining inventory)
            stock_data = {}
            for product in factory_info["products"]:
                if factory_id == "mintu_plast":
                    stock_data[product] = random.randint(8000, 25000)
                elif factory_id == "amen_water":
                    stock_data[product] = random.randint(3000, 12000)
                elif factory_id == "wakene_food":
                    stock_data[product] = random.randint(200, 800)
                else:  # mintu_export
                    stock_data[product] = random.randint(50, 200)
            
            # Generate downtime data
            downtime_hours = round(random.uniform(0.5, 6.0), 2)
            
            # Create 1-2 downtime reasons
            num_reasons = random.randint(1, 2)
            downtime_reasons = []
            remaining_hours = downtime_hours
            
            for i in range(num_reasons):
                if i == num_reasons - 1:  # Last reason gets remaining hours
                    hours = round(remaining_hours, 2)
                else:
                    hours = round(random.uniform(0.5, remaining_hours * 0.7), 2)
                    remaining_hours = round(remaining_hours - hours, 2)
                
                downtime_reasons.append({
                    "reason": random.choice(DOWNTIME_REASONS),
                    "hours": hours
                })
            
            # Create the daily log document
            daily_log = {
                "date": today,
                "factory_id": factory_id,
                "production_data": production_data,
                "sales_data": sales_data,
                "downtime_hours": downtime_hours,
                "downtime_reasons": downtime_reasons,
                "stock_data": stock_data,
                "created_by": user,
                "created_at": datetime.utcnow()
            }
            
            # Insert the log
            await db.daily_logs.insert_one(daily_log)
            logs_created += 1
            
            print(f"✅ Created today's log for {factory_info['name']} (Production: {sum(production_data.values()):,})")
    
    print(f"🎉 Successfully created {logs_created} daily logs for today across all {len(FACTORIES)} factories")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(populate_today_data())