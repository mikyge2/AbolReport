from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import pandas as pd
from io import BytesIO
import json
import openpyxl


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours for better user experience
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Factory Configuration
FACTORIES = {
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
    },
    "wakene_food": {
        "name": "Wakene Food Complex",
        "products": ["Flour", "Fruska (Wheat Bran)", "Fruskelo (Wheat Germ)"],
        "sku_unit": "Quintal"
    }
}

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    role: str  # "factory_employer" or "headquarters"
    factory_id: Optional[str] = None  # Only for factory employers
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    factory_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "factory_employer"  # Default role
    factory_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    factory_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DowntimeReason(BaseModel):
    reason: str
    hours: float

class DailyLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_id: str  # RPT-XXXXX format
    date: datetime
    factory_id: str
    production_data: Dict[str, int] = Field(default_factory=dict)
    sales_data: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  
    downtime_hours: float = 0.0
    downtime_reasons: List[DowntimeReason] = Field(default_factory=list)
    stock_data: Dict[str, int] = Field(default_factory=dict)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DailyLogCreate(BaseModel):
    date: str
    factory_id: str
    production_data: Dict[str, int] = Field(default_factory=dict)
    sales_data: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    downtime_hours: float = 0.0
    downtime_reasons: List[DowntimeReason] = Field(default_factory=list)
    stock_data: Dict[str, int] = Field(default_factory=dict)

class DailyLogUpdate(BaseModel):
    production_data: Optional[Dict[str, int]] = None
    sales_data: Optional[Dict[str, Dict[str, Any]]] = None
    downtime_hours: Optional[float] = None
    downtime_reasons: Optional[List[DowntimeReason]] = None
    stock_data: Optional[Dict[str, int]] = None

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authentication functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return user

# Authentication endpoints
@api_router.post("/auth/login", response_model=Token)
async def login(user_data: LoginRequest):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# Utility functions
async def get_next_report_id():
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
    
    return f"RPT-{next_number:05d}"

# Factory configuration endpoint
@api_router.get("/factories")
async def get_factories():
    return FACTORIES

# Daily logs endpoints
@api_router.post("/daily-logs")
async def create_daily_log(log_data: DailyLogCreate, current_user: dict = Depends(get_current_user)):
    # Check user permissions
    if current_user["role"] == "factory_employer" and log_data.factory_id != current_user.get("factory_id"):
        raise HTTPException(status_code=403, detail="Cannot create logs for other factories")
    
    # Check if log already exists for this date and factory
    existing_log = await db.daily_logs.find_one({
        "date": datetime.fromisoformat(log_data.date),
        "factory_id": log_data.factory_id
    })
    if existing_log:
        raise HTTPException(status_code=400, detail="Daily log already exists for this date and factory")
    
    # Generate sequential report ID
    report_id = await get_next_report_id()
    
    # Create the daily log
    daily_log = DailyLog(
        report_id=report_id,
        date=datetime.fromisoformat(log_data.date),
        factory_id=log_data.factory_id,
        production_data=log_data.production_data,
        sales_data=log_data.sales_data,
        downtime_hours=log_data.downtime_hours,
        downtime_reasons=log_data.downtime_reasons,
        stock_data=log_data.stock_data,
        created_by=current_user["username"]
    )
    
    # Convert to dict for insertion
    log_dict = daily_log.dict()
    
    result = await db.daily_logs.insert_one(log_dict)
    if result.inserted_id:
        return {"message": "Daily log created successfully", "report_id": report_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create daily log")

@api_router.get("/daily-logs")
async def get_daily_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    factory_id: Optional[str] = None,
    created_by_me: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    # Build query filters
    query = {}
    
    # Role-based filtering
    if current_user["role"] == "factory_employer":
        query["factory_id"] = current_user.get("factory_id")
    elif factory_id:
        query["factory_id"] = factory_id
    
    # Date filtering
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = datetime.fromisoformat(start_date)
        if end_date:
            date_filter["$lte"] = datetime.fromisoformat(end_date)
        query["date"] = date_filter
    
    # Created by me filter
    if created_by_me:
        query["created_by"] = current_user["username"]
    
    # Fetch logs
    logs = await db.daily_logs.find(query).sort("date", -1).to_list(length=None)
    
    # Convert ObjectId to string and format dates
    for log in logs:
        log["_id"] = str(log["_id"])
        if isinstance(log.get("date"), datetime):
            log["date"] = log["date"].isoformat()
        if isinstance(log.get("created_at"), datetime):
            log["created_at"] = log["created_at"].isoformat()
    
    return logs

@api_router.put("/daily-logs/{log_id}")
async def update_daily_log(log_id: str, log_update: DailyLogUpdate, current_user: dict = Depends(get_current_user)):
    # Find the log
    log = await db.daily_logs.find_one({"id": log_id})
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    
    # Check permissions (only creator can edit)
    if log["created_by"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Can only edit your own logs")
    
    # Factory permission check for factory employees
    if current_user["role"] == "factory_employer" and log["factory_id"] != current_user.get("factory_id"):
        raise HTTPException(status_code=403, detail="Cannot edit logs from other factories")
    
    # Prepare update data
    update_data = {}
    if log_update.production_data is not None:
        update_data["production_data"] = log_update.production_data
    if log_update.sales_data is not None:
        update_data["sales_data"] = log_update.sales_data
    if log_update.downtime_hours is not None:
        update_data["downtime_hours"] = log_update.downtime_hours
    if log_update.downtime_reasons is not None:
        update_data["downtime_reasons"] = [reason.dict() for reason in log_update.downtime_reasons]
    if log_update.stock_data is not None:
        update_data["stock_data"] = log_update.stock_data
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    # Update the log
    result = await db.daily_logs.update_one(
        {"id": log_id},
        {"$set": update_data}
    )
    
    if result.modified_count > 0:
        return {"message": "Daily log updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update daily log")

@api_router.delete("/daily-logs/{log_id}")
async def delete_daily_log(log_id: str, current_user: dict = Depends(get_current_user)):
    # Find the log
    log = await db.daily_logs.find_one({"id": log_id})
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    
    # Check permissions (only creator can delete)
    if log["created_by"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Can only delete your own logs")
    
    # Factory permission check for factory employees
    if current_user["role"] == "factory_employer" and log["factory_id"] != current_user.get("factory_id"):
        raise HTTPException(status_code=403, detail="Cannot delete logs from other factories")
    
    # Delete the log
    result = await db.daily_logs.delete_one({"id": log_id})
    
    if result.deleted_count > 0:
        return {"message": "Daily log deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete daily log")

# Add migration endpoint for admin use
@api_router.post("/admin/migrate-report-ids")
async def migrate_report_ids(current_user: dict = Depends(get_current_user)):
    # Only headquarters users can run migration
    if current_user["role"] != "headquarters":
        raise HTTPException(status_code=403, detail="Only headquarters users can run migration")
    
    try:
        # Find all logs without report_id or with empty report_id
        logs_to_update = await db.daily_logs.find({
            "$or": [
                {"report_id": {"$exists": False}},
                {"report_id": ""},
                {"report_id": None}
            ]
        }).sort("created_at", 1).to_list(length=None)
        
        updated_count = 0
        current_number = 10000
        
        for log in logs_to_update:
            report_id = f"RPT-{current_number:05d}"
            
            await db.daily_logs.update_one(
                {"_id": log["_id"]},
                {"$set": {"report_id": report_id}}
            )
            
            updated_count += 1
            current_number += 1
        
        return {
            "message": f"Migration completed successfully",
            "updated_count": updated_count,
            "starting_report_id": "RPT-10000" if updated_count > 0 else None
        }
        
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

# Analytics endpoints
@api_router.get("/analytics/trends")
async def get_analytics_trends(days: int = 30, current_user: dict = Depends(get_current_user)):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Build query based on user role
    query = {"date": {"$gte": start_date, "$lte": end_date}}
    if current_user["role"] == "factory_employer":
        query["factory_id"] = current_user.get("factory_id")
    
    logs = await db.daily_logs.find(query).to_list(length=None)
    
    # Group data by factory
    factories_data = {}
    for factory_id, factory_config in FACTORIES.items():
        # Skip factories not accessible to current user
        if current_user["role"] == "factory_employer" and factory_id != current_user.get("factory_id"):
            continue
            
        factory_logs = [log for log in logs if log["factory_id"] == factory_id]
        
        # Create date range
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)
        
        # Initialize data arrays
        production_data = []
        sales_data = []
        production_by_product = {product: [] for product in factory_config["products"]}
        sales_by_product = {product: [] for product in factory_config["products"]}
        
        # Fill data for each date
        for date_str in dates:
            date_obj = datetime.fromisoformat(date_str)
            day_logs = [log for log in factory_logs if log["date"].date() == date_obj.date()]
            
            daily_production = 0
            daily_sales = 0
            
            for product in factory_config["products"]:
                product_production = 0
                product_sales = 0
                
                for log in day_logs:
                    if product in log.get("production_data", {}):
                        product_production += log["production_data"][product]
                    if product in log.get("sales_data", {}):
                        product_sales += log["sales_data"][product].get("amount", 0)
                
                production_by_product[product].append(product_production)
                sales_by_product[product].append(product_sales)
                daily_production += product_production
                daily_sales += product_sales
            
            production_data.append(daily_production)
            sales_data.append(daily_sales)
        
        factories_data[factory_id] = {
            "name": factory_config["name"],
            "dates": dates,
            "production": production_data,
            "sales": sales_data,
            "production_by_product": production_by_product,
            "sales_by_product": sales_by_product
        }
    
    logger.info(f"Analytics trends request - User: {current_user['username']}, Role: {current_user['role']}, Factory ID: {current_user.get('factory_id', 'None')}")
    
    return {
        "factories": factories_data,
        "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()}
    }

@api_router.get("/dashboard-summary")
async def get_dashboard_summary(current_user: dict = Depends(get_current_user)):
    # Build query based on user role
    query = {}
    if current_user["role"] == "factory_employer":
        query["factory_id"] = current_user.get("factory_id")
    
    logs = await db.daily_logs.find(query).to_list(length=None)
    
    total_downtime = sum(log.get("downtime_hours", 0) for log in logs)
    total_stock = sum(sum(log.get("stock_data", {}).values()) for log in logs)
    
    # Count unique factories based on role
    if current_user["role"] == "factory_employer":
        active_factories = 1 if logs else 0
    else:
        unique_factories = set(log.get("factory_id") for log in logs)
        active_factories = len(unique_factories)
    
    logger.info(f"Returning factory trends for {current_user['role']}:")
    logger.info(f"- Number of factories: {active_factories}")
    if current_user["role"] == "headquarters":
        factory_ids = list(set(log.get("factory_id") for log in logs))
        logger.info(f"- Factory IDs: {factory_ids}")
        logger.info(f"- Date range: {len(set(log.get('date').date() if log.get('date') else None for log in logs if log.get('date')))} days")
        
        # Log production and sales totals per factory
        for factory_id in factory_ids:
            factory_logs = [log for log in logs if log.get("factory_id") == factory_id]
            total_production = sum(sum(log.get("production_data", {}).values()) for log in factory_logs)
            total_sales = sum(sum(log.get("sales_data", {}).get(product, {}).get("amount", 0) for product in log.get("sales_data", {})) for log in factory_logs)
            logger.info(f"  Factory {factory_id}: {total_production} total production, {total_sales} total sales")
    
    return {
        "total_downtime": total_downtime,
        "active_factories": active_factories,
        "total_stock": total_stock
    }

@api_router.get("/analytics/factory-comparison")
async def get_factory_comparison(current_user: dict = Depends(get_current_user)):
    # Only headquarters can access factory comparison
    if current_user["role"] != "headquarters":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get today's data only
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    query = {"date": {"$gte": start_of_day, "$lte": end_of_day}}
    logs = await db.daily_logs.find(query).to_list(length=None)
    
    # Group by factory
    factory_stats = []
    for factory_id, factory_config in FACTORIES.items():
        factory_logs = [log for log in logs if log["factory_id"] == factory_id]
        
        total_production = sum(sum(log.get("production_data", {}).values()) for log in factory_logs)
        total_sales = sum(sum(log.get("sales_data", {}).get(product, {}).get("amount", 0) for product in log.get("sales_data", {})) for log in factory_logs)
        total_revenue = sum(sum(log.get("sales_data", {}).get(product, {}).get("amount", 0) * log.get("sales_data", {}).get(product, {}).get("unit_price", 0) for product in log.get("sales_data", {})) for log in factory_logs)
        total_downtime = sum(log.get("downtime_hours", 0) for log in factory_logs)
        
        # Calculate efficiency (assuming 24-hour operation)
        efficiency = ((24 - total_downtime) / 24) * 100 if total_downtime < 24 else 0
        
        factory_stats.append({
            "name": factory_config["name"],
            "production": total_production,
            "sales": total_sales,
            "revenue": total_revenue,
            "downtime": total_downtime,
            "efficiency": round(efficiency, 2),
            "sku_unit": factory_config["sku_unit"]
        })
    
    return factory_stats

# Excel export endpoint
@api_router.get("/export-excel")
async def export_excel(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    factory_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Build query filters based on user role and parameters
        query = {}
        
        # Role-based filtering - factory employees can only export their factory data
        if current_user["role"] == "factory_employer":
            query["factory_id"] = current_user.get("factory_id")
        elif factory_id:
            query["factory_id"] = factory_id
        
        # Date filtering
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.fromisoformat(start_date)
            if end_date:
                date_filter["$lte"] = datetime.fromisoformat(end_date)
            query["date"] = date_filter
        
        # Fetch data
        logs = await db.daily_logs.find(query).sort("date", -1).to_list(length=None)
        
        if not logs:
            raise HTTPException(status_code=404, detail="No data found for the specified criteria")
        
        # Prepare data for Excel
        excel_data = []
        for log in logs:
            # Calculate totals
            total_production = sum(log.get("production_data", {}).values())
            total_sales = sum(item.get("amount", 0) for item in log.get("sales_data", {}).values())
            total_revenue = sum(
                item.get("amount", 0) * item.get("unit_price", 0) 
                for item in log.get("sales_data", {}).values()
            )
            
            # Get factory name
            factory_name = FACTORIES.get(log.get("factory_id", ""), {}).get("name", log.get("factory_id", "Unknown"))
            
            excel_data.append({
                "Report ID": log.get("report_id", "N/A"),
                "Date": log.get("date").strftime("%Y-%m-%d") if log.get("date") else "N/A",
                "Factory": factory_name,
                "Total Production": total_production,
                "Total Sales": total_sales,
                "Total Revenue": total_revenue,
                "Downtime Hours": log.get("downtime_hours", 0),
                "Created By": log.get("created_by", "Unknown"),
                "Created At": log.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if log.get("created_at") else "N/A"
            })
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Create Excel file in memory with improved approach for hosting environments
        from openpyxl import Workbook
        from openpyxl.utils.dataframe import dataframe_to_rows
        
        wb = Workbook()
        
        # Daily Logs Sheet
        ws1 = wb.active
        ws1.title = "Daily Logs"
        
        # Add headers
        headers = ["Report ID", "Date", "Factory", "Total Production", "Total Sales", 
                  "Total Revenue", "Downtime Hours", "Created By", "Created At"]
        ws1.append(headers)
        
        # Add data
        for row_data in excel_data:
            ws1.append([row_data[header] for header in headers])
        
        # Summary Sheet
        ws2 = wb.create_sheet("Summary")
        summary_headers = ["Metric", "Value"]
        ws2.append(summary_headers)
        
        summary_data = [
            ["Total Reports", len(excel_data)],
            ["Total Production", sum(row['Total Production'] for row in excel_data)],
            ["Total Sales", sum(row['Total Sales'] for row in excel_data)],
            ["Total Revenue", sum(row['Total Revenue'] for row in excel_data)],
            ["Total Downtime", sum(row['Downtime Hours'] for row in excel_data)]
        ]
        
        for row in summary_data:
            ws2.append(row)
        
        # Save to BytesIO with proper handling
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Get the content as bytes
        content = output.getvalue()
        
        # Verify content is not empty
        if len(content) == 0:
            raise HTTPException(status_code=500, detail="Generated Excel file is empty")
        
        # Create proper streaming response for hosting environments
        def generate():
            yield content
        
        # Create response with proper headers
        response = StreamingResponse(
            generate(),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        filename = f"factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.headers["Content-Length"] = str(len(content))
        response.headers["Cache-Control"] = "no-cache"
        
        return response
        
    except Exception as e:
        logger.error(f"Excel export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# User management endpoints (headquarters only)
@api_router.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "headquarters":
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = await db.users.find({}).to_list(length=None)
    
    # Convert ObjectId to string and remove password hash
    user_responses = []
    for user in users:
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)  # Remove password hash for security
        user_responses.append(UserResponse(**user))
    
    return user_responses

@api_router.post("/users")
async def create_user(user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "headquarters":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password and create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        factory_id=user_data.factory_id,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    result = await db.users.insert_one(user.dict())
    if result.inserted_id:
        return {"message": "User created successfully", "user_id": user.id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create user")

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "headquarters":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Find user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update data
    update_data = {}
    if user_update.username is not None:
        # Check if username already exists (for other users)
        existing_user = await db.users.find_one({"username": user_update.username, "id": {"$ne": user_id}})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        update_data["username"] = user_update.username
    
    if user_update.email is not None:
        update_data["email"] = user_update.email
    if user_update.password is not None:
        update_data["password_hash"] = hash_password(user_update.password)
    if user_update.role is not None:
        update_data["role"] = user_update.role
    if user_update.factory_id is not None:
        update_data["factory_id"] = user_update.factory_id
    if user_update.first_name is not None:
        update_data["first_name"] = user_update.first_name
    if user_update.last_name is not None:
        update_data["last_name"] = user_update.last_name
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    result = await db.users.update_one({"id": user_id}, {"$set": update_data})
    if result.modified_count > 0:
        return {"message": "User updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update user")

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "headquarters":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Don't allow deletion of self
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count > 0:
        return {"message": "User deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

# Include the API router with the /api prefix
app.include_router(api_router)

# Create default admin user on startup
@app.on_event("startup")
async def create_admin_user():
    # Remove existing admin user if exists
    await db.users.delete_many({"username": "admin"})
    
    # Create new admin user with updated password
    admin_data = {
        "username": "admin",
        "email": "admin@factory.com", 
        "password": "admin1234",
        "role": "headquarters",
        "first_name": "Admin",
        "last_name": "User"
    }
    
    admin_user = User(
        username=admin_data["username"],
        email=admin_data["email"],
        password_hash=hash_password(admin_data["password"]),
        role=admin_data["role"],
        first_name=admin_data["first_name"],
        last_name=admin_data["last_name"]
    )
    
    await db.users.insert_one(admin_user.dict())
    logger.info("Admin user created/updated successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)