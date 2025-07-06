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


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
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
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    factory_id: Optional[str] = None
    created_at: datetime

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str
    factory_id: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: Dict[str, Any]

class DailyLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    factory_id: str
    date: datetime
    production_data: Dict[str, float]  # product -> amount
    sales_data: Dict[str, Dict[str, float]]  # product -> {amount, unit_price}
    downtime_hours: float
    downtime_reason: str
    stock_data: Dict[str, float]  # product -> current_stock
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DailyLogCreate(BaseModel):
    factory_id: str
    date: datetime
    production_data: Dict[str, float]
    sales_data: Dict[str, Dict[str, float]]
    downtime_hours: float
    downtime_reason: str
    stock_data: Dict[str, float]

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

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
    return User(**user)

# Routes
@api_router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Validate factory_id for factory employers
    if user.role == "factory_employer":
        if not user.factory_id or user.factory_id not in FACTORIES:
            raise HTTPException(status_code=400, detail="Valid factory_id required for factory employers")
    
    # Create user
    user_dict = user.dict()
    user_dict["password_hash"] = get_password_hash(user.password)
    del user_dict["password"]
    
    user_obj = User(**user_dict)
    await db.users.insert_one(user_obj.dict())
    
    # Create response without password_hash
    user_response = UserResponse(
        id=user_obj.id,
        username=user_obj.username,
        email=user_obj.email,
        role=user_obj.role,
        factory_id=user_obj.factory_id,
        created_at=user_obj.created_at
    )
    return user_response

@api_router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    user_info = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "factory_id": user.get("factory_id")
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": user_info
    }

@api_router.get("/factories")
async def get_factories():
    return FACTORIES

@api_router.post("/daily-logs", response_model=DailyLog)
async def create_daily_log(log: DailyLogCreate, current_user: User = Depends(get_current_user)):
    # Validate factory access
    if current_user.role == "factory_employer" and current_user.factory_id != log.factory_id:
        raise HTTPException(status_code=403, detail="Access denied to this factory")
    
    # Check if log for this date already exists
    existing_log = await db.daily_logs.find_one({
        "factory_id": log.factory_id,
        "date": log.date
    })
    if existing_log:
        raise HTTPException(status_code=400, detail="Daily log for this date already exists")
    
    log_dict = log.dict()
    log_dict["created_by"] = current_user.username
    log_obj = DailyLog(**log_dict)
    
    await db.daily_logs.insert_one(log_obj.dict())
    return log_obj

@api_router.get("/daily-logs", response_model=List[DailyLog])
async def get_daily_logs(
    factory_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    query = {}
    
    # Filter by factory access
    if current_user.role == "factory_employer":
        query["factory_id"] = current_user.factory_id
    elif factory_id:
        query["factory_id"] = factory_id
    
    # Date filtering
    if start_date or end_date:
        query["date"] = {}
        if start_date:
            query["date"]["$gte"] = start_date
        if end_date:
            query["date"]["$lte"] = end_date
    
    logs = await db.daily_logs.find(query).to_list(1000)
    return [DailyLog(**log) for log in logs]

@api_router.get("/dashboard-summary")
async def get_dashboard_summary(current_user: User = Depends(get_current_user)):
    # Get recent logs (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    query = {"date": {"$gte": thirty_days_ago}}
    if current_user.role == "factory_employer":
        query["factory_id"] = current_user.factory_id
    
    logs = await db.daily_logs.find(query).to_list(1000)
    
    # Calculate summaries
    total_production = 0
    total_sales = 0
    total_downtime = 0
    total_stock = 0
    
    factory_summaries = {}
    
    for log in logs:
        factory_id = log["factory_id"]
        if factory_id not in factory_summaries:
            factory_summaries[factory_id] = {
                "name": FACTORIES.get(factory_id, {}).get("name", factory_id),
                "production": 0,
                "sales": 0,
                "downtime": 0,
                "stock": 0
            }
        
        # Production
        production = sum(log["production_data"].values())
        total_production += production
        factory_summaries[factory_id]["production"] += production
        
        # Sales
        sales = sum(item["amount"] for item in log["sales_data"].values())
        total_sales += sales
        factory_summaries[factory_id]["sales"] += sales
        
        # Downtime
        total_downtime += log["downtime_hours"]
        factory_summaries[factory_id]["downtime"] += log["downtime_hours"]
        
        # Stock
        stock = sum(log["stock_data"].values())
        total_stock += stock
        factory_summaries[factory_id]["stock"] += stock
    
    return {
        "total_production": total_production,
        "total_sales": total_sales,
        "total_downtime": total_downtime,
        "total_stock": total_stock,
        "factory_summaries": factory_summaries
    }

@api_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        factory_id=current_user.factory_id,
        created_at=current_user.created_at
    )

@api_router.get("/export-excel")
async def export_excel_report(
    factory_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Export comprehensive Excel report"""
    query = {}
    
    # Filter by factory access
    if current_user.role == "factory_employer":
        query["factory_id"] = current_user.factory_id
    elif factory_id:
        query["factory_id"] = factory_id
    
    # Date filtering
    if start_date or end_date:
        query["date"] = {}
        if start_date:
            query["date"]["$gte"] = start_date
        if end_date:
            query["date"]["$lte"] = end_date
    
    # Get logs
    logs = await db.daily_logs.find(query).to_list(1000)
    
    if not logs:
        raise HTTPException(status_code=404, detail="No data found for the specified criteria")
    
    # Prepare data for Excel
    excel_data = []
    for log in logs:
        factory_name = FACTORIES.get(log["factory_id"], {}).get("name", log["factory_id"])
        sku_unit = FACTORIES.get(log["factory_id"], {}).get("sku_unit", "Unit")
        
        # Base row data
        base_row = {
            "Date": log["date"].strftime("%Y-%m-%d") if isinstance(log["date"], datetime) else log["date"],
            "Factory": factory_name,
            "SKU Unit": sku_unit,
            "Downtime Hours": log["downtime_hours"],
            "Downtime Reason": log["downtime_reason"],
            "Created By": log["created_by"]
        }
        
        # Add production data
        for product, amount in log["production_data"].items():
            row = base_row.copy()
            row.update({
                "Product": product,
                "Production Amount": amount,
                "Sales Amount": log["sales_data"].get(product, {}).get("amount", 0),
                "Unit Price": log["sales_data"].get(product, {}).get("unit_price", 0),
                "Revenue": log["sales_data"].get(product, {}).get("amount", 0) * log["sales_data"].get(product, {}).get("unit_price", 0),
                "Current Stock": log["stock_data"].get(product, 0)
            })
            excel_data.append(row)
    
    # Create Excel file
    df = pd.DataFrame(excel_data)
    
    # Create Excel writer object
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Main data sheet
        df.to_excel(writer, sheet_name='Daily Logs', index=False)
        
        # Summary sheet
        summary_data = []
        for factory_id, factory_info in FACTORIES.items():
            factory_logs = [log for log in logs if log["factory_id"] == factory_id]
            if factory_logs:
                total_production = sum(sum(log["production_data"].values()) for log in factory_logs)
                total_sales = sum(sum(item["amount"] for item in log["sales_data"].values()) for log in factory_logs)
                total_revenue = sum(sum(item["amount"] * item["unit_price"] for item in log["sales_data"].values()) for log in factory_logs)
                total_downtime = sum(log["downtime_hours"] for log in factory_logs)
                avg_stock = sum(sum(log["stock_data"].values()) for log in factory_logs) / len(factory_logs)
                
                summary_data.append({
                    "Factory": factory_info["name"],
                    "Total Production": total_production,
                    "Total Sales": total_sales,
                    "Total Revenue": total_revenue,
                    "Total Downtime (Hours)": total_downtime,
                    "Average Stock": avg_stock,
                    "Number of Records": len(factory_logs)
                })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    
    # Generate filename
    filename = f"factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.get("/analytics/trends")
async def get_analytics_trends(
    factory_id: Optional[str] = None,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get analytics trends for charts"""
    query = {}
    
    # Filter by factory access
    if current_user.role == "factory_employer":
        query["factory_id"] = current_user.factory_id
    elif factory_id:
        query["factory_id"] = factory_id
    
    # Date filtering for last N days
    start_date = datetime.utcnow() - timedelta(days=days)
    query["date"] = {"$gte": start_date}
    
    logs = await db.daily_logs.find(query).sort("date", 1).to_list(1000)
    
    # Prepare trend data
    trends = {
        "production": [],
        "sales": [],
        "downtime": [],
        "stock": [],
        "dates": []
    }
    
    # Group by date
    daily_data = {}
    for log in logs:
        date_str = log["date"].strftime("%Y-%m-%d") if isinstance(log["date"], datetime) else log["date"]
        if date_str not in daily_data:
            daily_data[date_str] = {
                "production": 0,
                "sales": 0,
                "downtime": 0,
                "stock": 0
            }
        
        daily_data[date_str]["production"] += sum(log["production_data"].values())
        daily_data[date_str]["sales"] += sum(item["amount"] for item in log["sales_data"].values())
        daily_data[date_str]["downtime"] += log["downtime_hours"]
        daily_data[date_str]["stock"] += sum(log["stock_data"].values())
    
    # Sort by date and prepare final data
    for date_str in sorted(daily_data.keys()):
        trends["dates"].append(date_str)
        trends["production"].append(daily_data[date_str]["production"])
        trends["sales"].append(daily_data[date_str]["sales"])
        trends["downtime"].append(daily_data[date_str]["downtime"])
        trends["stock"].append(daily_data[date_str]["stock"])
    
    return trends

@api_router.get("/analytics/factory-comparison")
async def get_factory_comparison(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get factory comparison data"""
    if current_user.role == "factory_employer":
        raise HTTPException(status_code=403, detail="Access restricted to headquarters only")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    query = {"date": {"$gte": start_date}}
    
    logs = await db.daily_logs.find(query).to_list(1000)
    
    factory_data = {}
    for factory_id, factory_info in FACTORIES.items():
        factory_logs = [log for log in logs if log["factory_id"] == factory_id]
        
        factory_data[factory_id] = {
            "name": factory_info["name"],
            "production": sum(sum(log["production_data"].values()) for log in factory_logs),
            "sales": sum(sum(item["amount"] for item in log["sales_data"].values()) for log in factory_logs),
            "revenue": sum(sum(item["amount"] * item["unit_price"] for item in log["sales_data"].values()) for log in factory_logs),
            "downtime": sum(log["downtime_hours"] for log in factory_logs),
            "efficiency": 0  # Will calculate efficiency percentage
        }
        
        # Calculate efficiency (production vs planned - using production as baseline)
        if factory_data[factory_id]["production"] > 0:
            planned_production = factory_data[factory_id]["production"] * 1.2  # Assume 20% more was planned
            factory_data[factory_id]["efficiency"] = (factory_data[factory_id]["production"] / planned_production) * 100
    
    return factory_data

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create default admin user on startup
@app.on_event("startup")
async def create_default_user():
    # Check if admin user exists
    admin_user = await db.users.find_one({"username": "admin"})
    if not admin_user:
        # Create default admin user
        admin_data = {
            "username": "admin",
            "email": "admin@company.com",
            "password_hash": get_password_hash("admin123"),
            "role": "headquarters",
            "factory_id": None,
            "created_at": datetime.utcnow()
        }
        admin_obj = User(**admin_data)
        await db.users.insert_one(admin_obj.dict())
        logger.info("Created default admin user: admin/admin123")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()