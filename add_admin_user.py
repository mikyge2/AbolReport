#!/usr/bin/env python3
"""
Script to add admin user to the database
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Database configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def add_admin_user():
    """Add admin user to the database"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Check if admin user already exists
        existing_user = await db.users.find_one({"username": "admin"})
        if existing_user:
            print("🗑️  Removing existing admin user...")
            await db.users.delete_one({"username": "admin"})
        
        # Create new admin user
        password_hash = pwd_context.hash("admin1234")
        
        admin_user = {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "email": "admin@factory.com",
            "password_hash": password_hash,
            "role": "headquarters",
            "factory_id": None,
            "first_name": "Admin",
            "last_name": "User",
            "created_at": datetime.utcnow()
        }
        
        # Insert the user
        result = await db.users.insert_one(admin_user)
        
        if result.inserted_id:
            print("✅ Successfully created admin user:")
            print(f"   Username: admin")
            print(f"   Password: admin1234")
            print(f"   Role: headquarters")
            print(f"   Email: admin@factory.com")
            print(f"   User ID: {admin_user['id']}")
        else:
            print("❌ Failed to create admin user")
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(add_admin_user())