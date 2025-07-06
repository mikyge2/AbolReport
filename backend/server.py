from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
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

@api_router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    user_info = current_user.dict()
    del user_info["password_hash"]
    return user_info

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()