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

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: Dict[str, Any]

class DowntimeReason(BaseModel):
    reason: str
    hours: float

async def migrate_existing_report_ids():
    """Migrate existing reports to use RPT-XXXXX format"""
    try:
        # Find all logs without RPT format
        cursor = db.daily_logs.find({"report_id": {"$not": {"$regex": "^RPT-\\d{5}$"}}})
        
        report_counter = 10000
        updated_count = 0
        
        async for log in cursor:
            new_report_id = f"RPT-{report_counter:05d}"
            
            await db.daily_logs.update_one(
                {"_id": log["_id"]},
                {"$set": {"report_id": new_report_id}}
            )
            
            report_counter += 1
            updated_count += 1
        
        print(f"✅ Migration completed: Updated {updated_count} reports with new RPT-XXXXX format")
        return updated_count
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 0

async def get_next_report_id():
    """Generate next sequential report ID in format RPT-XXXXX starting from RPT-10000"""
    # Find the highest report_id that matches the pattern
    cursor = db.daily_logs.find({"report_id": {"$regex": "^RPT-\\d{5}$"}}).sort("report_id", -1).limit(1)
    
    highest_report = None
    async for doc in cursor:
        highest_report = doc
        break
    
    if highest_report and highest_report.get('report_id'):
        # Extract the number and increment
        current_number = int(highest_report['report_id'].split('-')[1])
        next_number = current_number + 1
    else:
        # Start from 10000 if no existing reports
        next_number = 10000
    
    return f"RPT-{next_number:05d}"

async def get_next_report_id():
    """Generate next sequential report ID in format RPT-XXXXX starting from RPT-10000"""
    # Find the highest report_id that matches the pattern
    cursor = db.daily_logs.find({"report_id": {"$regex": "^RPT-\\d{5}$"}}).sort("report_id", -1).limit(1)
    
    highest_report = None
    async for doc in cursor:
        highest_report = doc
        break
    
    if highest_report and highest_report.get('report_id'):
        # Extract the number and increment
        current_number = int(highest_report['report_id'].split('-')[1])
        next_number = current_number + 1
    else:
        # Start from 10000 if no existing reports
        next_number = 10000
    
    return f"RPT-{next_number:05d}"

class DailyLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_id: str = Field(default="")  # Will be set by get_next_report_id()
    factory_id: str
    date: datetime
    production_data: Dict[str, float]  # product -> amount
    sales_data: Dict[str, Dict[str, float]]  # product -> {amount, unit_price}
    downtime_hours: float
    downtime_reasons: List[DowntimeReason]  # Updated to support multiple reasons
    stock_data: Dict[str, float]  # product -> current_stock
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DailyLogCreate(BaseModel):
    factory_id: str
    date: datetime
    production_data: Dict[str, float]
    sales_data: Dict[str, Dict[str, float]]
    downtime_hours: float
    downtime_reasons: List[DowntimeReason]  # Updated to support multiple reasons
    stock_data: Dict[str, float]

class DailyLogUpdate(BaseModel):
    factory_id: Optional[str] = None
    date: Optional[datetime] = None
    production_data: Optional[Dict[str, float]] = None
    sales_data: Optional[Dict[str, Dict[str, float]]] = None
    downtime_hours: Optional[float] = None
    downtime_reasons: Optional[List[DowntimeReason]] = None
    stock_data: Optional[Dict[str, float]] = None

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
@api_router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "headquarters":
        raise HTTPException(status_code=403, detail="Access restricted to headquarters only")
    
    # Check if user exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Validate factory_id for factory employers only
    if user.role == "factory_employer":
        if not user.factory_id or user.factory_id not in FACTORIES:
            raise HTTPException(status_code=400, detail="Valid factory_id required for factory employers")
    elif user.role == "headquarters":
        # Headquarters users should not have factory_id
        user.factory_id = None
    
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
        first_name=user_obj.first_name,
        last_name=user_obj.last_name,
        created_at=user_obj.created_at
    )
    return user_response

@api_router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Validate factory_id for factory employers only
    if user.role == "factory_employer":
        if not user.factory_id or user.factory_id not in FACTORIES:
            raise HTTPException(status_code=400, detail="Valid factory_id required for factory employers")
    elif user.role == "headquarters":
        # Headquarters users should not have factory_id
        user.factory_id = None
    
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
        first_name=user_obj.first_name,
        last_name=user_obj.last_name,
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
    
    # Generate sequential report ID
    report_id = await get_next_report_id()
    log_dict["report_id"] = report_id
    
    log_obj = DailyLog(**log_dict)
    
    await db.daily_logs.insert_one(log_obj.dict())
    return log_obj

@api_router.get("/daily-logs", response_model=List[DailyLog])
async def get_daily_logs(
    factory_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    created_by_me: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    query = {}
    
    # Filter by factory access
    if current_user.role == "factory_employer":
        query["factory_id"] = current_user.factory_id
    elif factory_id:
        query["factory_id"] = factory_id
    
    # Filter by creator if requested
    if created_by_me:
        query["created_by"] = current_user.username
    
    # Date filtering
    if start_date or end_date:
        query["date"] = {}
        if start_date:
            query["date"]["$gte"] = start_date
        if end_date:
            query["date"]["$lte"] = end_date
    
    logs = await db.daily_logs.find(query).to_list(1000)
    return [DailyLog(**log) for log in logs]

@api_router.put("/daily-logs/{log_id}", response_model=DailyLog)
async def update_daily_log(log_id: str, log_update: DailyLogUpdate, current_user: User = Depends(get_current_user)):
    # Find the existing log
    existing_log = await db.daily_logs.find_one({"id": log_id})
    if not existing_log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    
    # Check if user is the creator of this log
    if existing_log["created_by"] != current_user.username:
        raise HTTPException(status_code=403, detail="You can only edit your own daily logs")
    
    # Validate factory access (user should not be able to change factory_id to unauthorized factory)
    if log_update.factory_id is not None:
        if current_user.role == "factory_employer" and current_user.factory_id != log_update.factory_id:
            raise HTTPException(status_code=403, detail="Access denied to this factory")
    
    # If user is editing date, check for conflicts
    if log_update.date is not None and log_update.date != existing_log["date"]:
        existing_factory_id = log_update.factory_id if log_update.factory_id is not None else existing_log["factory_id"]
        conflicting_log = await db.daily_logs.find_one({
            "factory_id": existing_factory_id,
            "date": log_update.date,
            "id": {"$ne": log_id}  # Exclude current log
        })
        if conflicting_log:
            raise HTTPException(status_code=400, detail="Daily log for this date already exists")
    
    # Prepare update data - only update fields that are provided
    update_data = {}
    for field, value in log_update.dict(exclude_unset=True).items():
        update_data[field] = value
    
    # Update the log
    await db.daily_logs.update_one({"id": log_id}, {"$set": update_data})
    
    # Return updated log
    updated_log = await db.daily_logs.find_one({"id": log_id})
    return DailyLog(**updated_log)

@api_router.delete("/daily-logs/{log_id}")
async def delete_daily_log(log_id: str, current_user: User = Depends(get_current_user)):
    # Find the existing log
    existing_log = await db.daily_logs.find_one({"id": log_id})
    if not existing_log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    
    # Check if user is the creator of this log
    if existing_log["created_by"] != current_user.username:
        raise HTTPException(status_code=403, detail="You can only delete your own daily logs")
    
    # Delete the log
    result = await db.daily_logs.delete_one({"id": log_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete daily log")
    
    return {"message": "Daily log deleted successfully"}

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

@api_router.get("/users", response_model=List[UserResponse])
async def list_users(current_user: User = Depends(get_current_user)):
    if current_user.role != "headquarters":
        raise HTTPException(status_code=403, detail="Access restricted to headquarters only")
    
    users = await db.users.find().to_list(1000)
    return [
        UserResponse(
            id=u["id"],
            username=u["username"],
            email=u["email"],
            role=u["role"],
            factory_id=u.get("factory_id"),
            first_name=u.get("first_name"),
            last_name=u.get("last_name"),
            created_at=u["created_at"]
        )
        for u in users
    ]

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, updated_data: dict, current_user: User = Depends(get_current_user)):
    if current_user.role != "headquarters":
        raise HTTPException(status_code=403, detail="Access restricted to headquarters only")
    
    existing_user = await db.users.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updates = {}

    # You can selectively allow fields to be updated
    if "first_name" in updated_data:
        updates["first_name"] = updated_data["first_name"]
    if "last_name" in updated_data:
        updates["last_name"] = updated_data["last_name"]
    if "username" in updated_data:
        updates["username"] = updated_data["username"]
    if "email" in updated_data:
        updates["email"] = updated_data["email"]
    if "role" in updated_data:
        updates["role"] = updated_data["role"]
    if "password" in updated_data and updated_data["password"]:
        updates["password_hash"] = get_password_hash(updated_data["password"])
    if "factory_id" in updated_data:
        updates["factory_id"] = updated_data["factory_id"]

    await db.users.update_one({"id": user_id}, {"$set": updates})

    # Return updated user
    user = await db.users.find_one({"id": user_id})
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"],
        factory_id=user.get("factory_id"),
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        created_at=user["created_at"]
    )

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "headquarters":
        raise HTTPException(status_code=403, detail="Access restricted to headquarters only")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"detail": "User deleted successfully"}

# Add migration endpoint for admin use
@api_router.post("/admin/migrate-report-ids")
async def migrate_report_ids_endpoint(current_user: User = Depends(get_current_user)):
    if current_user.role != "headquarters":
        raise HTTPException(status_code=403, detail="Only headquarters users can run migrations")
    
    updated_count = await migrate_existing_report_ids()
    return {"message": f"Migration completed: Updated {updated_count} reports"}

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
        downtime_reasons_str = "; ".join([f"{reason['reason']} ({reason['hours']}h)" for reason in log.get("downtime_reasons", [])])
        base_row = {
            "Report ID": log.get("report_id", "N/A"),
            "Date": log["date"].strftime("%Y-%m-%d") if isinstance(log["date"], datetime) else log["date"],
            "Factory": factory_name,
            "SKU Unit": sku_unit,
            "Downtime Hours": log["downtime_hours"],
            "Downtime Reasons": downtime_reasons_str,
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
        
        # Get the workbook and worksheet for styling
        workbook = writer.book
        worksheet = writer.sheets['Daily Logs']
        
        # Apply styling to headers
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, NamedStyle
        from openpyxl.utils import get_column_letter
        
        # Create professional styles
        header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="2F4F4F", end_color="2F4F4F", fill_type="solid")  # Dark slate gray
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Data styles
        data_font = Font(name="Calibri", size=11)
        data_alignment = Alignment(horizontal="left", vertical="center")
        center_alignment = Alignment(horizontal="center", vertical="center")
        right_alignment = Alignment(horizontal="right", vertical="center")
        
        # Currency and number styles
        currency_style = NamedStyle(name="currency_style")
        currency_style.font = data_font
        currency_style.alignment = right_alignment
        currency_style.number_format = '"ETB "#,##0.00'
        
        number_style = NamedStyle(name="number_style")
        number_style.font = data_font
        number_style.alignment = right_alignment
        number_style.number_format = '#,##0.00'
        
        # Apply header styling with freeze panes
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Freeze top row for better navigation
        worksheet.freeze_panes = "A2"
        
        # Set specific column widths and apply formatting
        column_config = {
            'A': {'width': 12, 'style': 'center'},      # Report ID
            'B': {'width': 12, 'style': 'center'},      # Date
            'C': {'width': 20, 'style': 'left'},        # Factory
            'D': {'width': 12, 'style': 'center'},      # SKU Unit
            'E': {'width': 18, 'style': 'left'},        # Product
            'F': {'width': 15, 'style': 'number'},      # Production Amount
            'G': {'width': 15, 'style': 'number'},      # Sales Amount
            'H': {'width': 12, 'style': 'currency'},    # Unit Price
            'I': {'width': 15, 'style': 'currency'},    # Revenue
            'J': {'width': 15, 'style': 'number'},      # Current Stock
            'K': {'width': 15, 'style': 'number'},      # Downtime Hours
            'L': {'width': 30, 'style': 'left'},        # Downtime Reasons
            'M': {'width': 15, 'style': 'left'},        # Created By
        }
        
        # Apply column configurations
        for col_letter, config in column_config.items():
            worksheet.column_dimensions[col_letter].width = config['width']
            
            # Apply styling to data cells in this column
            for row_num in range(2, worksheet.max_row + 1):
                cell = worksheet[f"{col_letter}{row_num}"]
                cell.font = data_font
                
                if config['style'] == 'center':
                    cell.alignment = center_alignment
                elif config['style'] == 'right':
                    cell.alignment = right_alignment
                elif config['style'] == 'number':
                    cell.alignment = right_alignment
                    cell.number_format = '#,##0.00'
                elif config['style'] == 'currency':
                    cell.alignment = right_alignment
                    cell.number_format = '"ETB "#,##0.00'
                else:
                    cell.alignment = data_alignment
        
        # Add professional borders
        thin_border = Border(
            left=Side(style='thin', color='D3D3D3'),
            right=Side(style='thin', color='D3D3D3'),
            top=Side(style='thin', color='D3D3D3'),
            bottom=Side(style='thin', color='D3D3D3')
        )
        
        # Apply borders and alternating row colors
        light_fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
        
        for row_num, row in enumerate(worksheet.iter_rows(min_row=2), start=2):
            for cell in row:
                cell.border = thin_border
                # Apply alternating row colors
                if row_num % 2 == 0:
                    cell.fill = light_fill
        
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
                    "Total Production": f"{total_production:,.2f}",
                    "Total Sales": f"{total_sales:,.2f}",
                    "Total Revenue": f"ETB {total_revenue:,.2f}",
                    "Total Downtime (Hours)": f"{total_downtime:.1f}",
                    "Average Stock": f"{avg_stock:,.2f}",
                    "Number of Records": len(factory_logs)
                })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Style summary sheet with professional formatting
        summary_worksheet = writer.sheets['Summary']
        
        # Apply header styling to summary sheet
        for cell in summary_worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Freeze panes for summary sheet
        summary_worksheet.freeze_panes = "A2"
        
        # Configure summary sheet columns
        summary_column_config = {
            'A': {'width': 25, 'style': 'left'},        # Factory
            'B': {'width': 18, 'style': 'number'},      # Total Production
            'C': {'width': 18, 'style': 'number'},      # Total Sales
            'D': {'width': 18, 'style': 'currency'},    # Total Revenue
            'E': {'width': 20, 'style': 'number'},      # Total Downtime
            'F': {'width': 18, 'style': 'number'},      # Average Stock
            'G': {'width': 18, 'style': 'center'},      # Number of Records
        }
        
        # Apply summary column configurations
        for col_letter, config in summary_column_config.items():
            summary_worksheet.column_dimensions[col_letter].width = config['width']
            
            # Apply styling to data cells in summary sheet
            for row_num in range(2, summary_worksheet.max_row + 1):
                cell = summary_worksheet[f"{col_letter}{row_num}"]
                cell.font = data_font
                
                if config['style'] == 'center':
                    cell.alignment = center_alignment
                elif config['style'] == 'right':
                    cell.alignment = right_alignment
                elif config['style'] == 'number':
                    cell.alignment = right_alignment
                    cell.number_format = '#,##0.00'
                elif config['style'] == 'currency':
                    cell.alignment = right_alignment
                    cell.number_format = '"ETB "#,##0.00'
                else:
                    cell.alignment = data_alignment
        
        # Add borders and alternating colors to summary sheet
        for row_num, row in enumerate(summary_worksheet.iter_rows(min_row=2), start=2):
            for cell in row:
                cell.border = thin_border
                if row_num % 2 == 0:
                    cell.fill = light_fill
        
        # Add a title to the summary sheet
        summary_worksheet.insert_rows(1)
        title_cell = summary_worksheet['A1']
        title_cell.value = f"Factory Performance Summary Report - Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        title_cell.font = Font(name="Calibri", bold=True, size=14, color="2F4F4F")
        title_cell.alignment = Alignment(horizontal="left", vertical="center")
        summary_worksheet.merge_cells('A1:G1')
        
        # Move headers to row 2
        summary_worksheet.freeze_panes = "A3"
    
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
    print(f"Analytics trends request - User: {current_user.username}, Role: {current_user.role}, Factory ID: {current_user.factory_id}")
    
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
    
    # For single factory (factory_employer or specific factory requested)
    if current_user.role == "factory_employer" or (factory_id is not None and factory_id != ""):
        # Prepare single factory trend data
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
            for item in log["sales_data"].values():
                if isinstance(item, dict):
                    daily_data[date_str]["sales"] += item.get("amount", 0)
                else:
                    daily_data[date_str]["sales"] += item
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
    
    # For headquarters - return factory-specific data
    else:
        # Prepare factory-specific trend data
        factory_trends = {
            "factories": {},
            "dates": [],
            "downtime": [],
            "stock": []
        }
        
        # Get all unique dates
        all_dates = set()
        for log in logs:
            date_str = log["date"].strftime("%Y-%m-%d") if isinstance(log["date"], datetime) else log["date"]
            all_dates.add(date_str)
        
        factory_trends["dates"] = sorted(list(all_dates))
        
        # Initialize factory data
        for factory_id, factory_info in FACTORIES.items():
            factory_trends["factories"][factory_id] = {
                "name": factory_info["name"],
                "dates": factory_trends["dates"].copy(),
                "production": [0] * len(factory_trends["dates"]),
                "sales": [0] * len(factory_trends["dates"]),
                "production_by_product": {},
                "sales_by_product": {}
            }
            
            # Initialize product-level arrays for each factory
            for product in factory_info["products"]:
                factory_trends["factories"][factory_id]["production_by_product"][product] = [0] * len(factory_trends["dates"])
                factory_trends["factories"][factory_id]["sales_by_product"][product] = [0] * len(factory_trends["dates"])
        
        # Initialize overall downtime and stock arrays
        factory_trends["downtime"] = [0] * len(factory_trends["dates"])
        factory_trends["stock"] = [0] * len(factory_trends["dates"])
        
        # Group logs by factory and date
        factory_daily_data = {}
        product_daily_data = {}  # Track product-level data
        overall_daily_data = {}
        
        for log in logs:
            date_str = log["date"].strftime("%Y-%m-%d") if isinstance(log["date"], datetime) else log["date"]
            factory_id = log["factory_id"]
            
            # Factory-specific aggregate data
            if factory_id not in factory_daily_data:
                factory_daily_data[factory_id] = {}
            
            if date_str not in factory_daily_data[factory_id]:
                factory_daily_data[factory_id][date_str] = {
                    "production": 0,
                    "sales": 0
                }
            
            factory_daily_data[factory_id][date_str]["production"] += sum(log["production_data"].values())
            for item in log["sales_data"].values():
                if isinstance(item, dict):
                    factory_daily_data[factory_id][date_str]["sales"] += item.get("amount", 0)
                else:
                    factory_daily_data[factory_id][date_str]["sales"] += item

            # Product-specific data tracking
            if factory_id not in product_daily_data:
                product_daily_data[factory_id] = {}
            
            if date_str not in product_daily_data[factory_id]:
                product_daily_data[factory_id][date_str] = {}
            
            # Track production by product
            for product, production_amount in log["production_data"].items():
                if product not in product_daily_data[factory_id][date_str]:
                    product_daily_data[factory_id][date_str][product] = {"production": 0, "sales": 0}
                product_daily_data[factory_id][date_str][product]["production"] += production_amount
            
            # Track sales by product
            for product, sales_item in log["sales_data"].items():
                if product not in product_daily_data[factory_id][date_str]:
                    product_daily_data[factory_id][date_str][product] = {"production": 0, "sales": 0}
                
                if isinstance(sales_item, dict):
                    product_daily_data[factory_id][date_str][product]["sales"] += sales_item.get("amount", 0)
                else:
                    product_daily_data[factory_id][date_str][product]["sales"] += sales_item

            
            # Overall data for downtime and stock
            if date_str not in overall_daily_data:
                overall_daily_data[date_str] = {
                    "downtime": 0,
                    "stock": 0
                }
            
            overall_daily_data[date_str]["downtime"] += log["downtime_hours"]
            overall_daily_data[date_str]["stock"] += sum(log["stock_data"].values())
        
        # Fill in the factory trend data
        for factory_id, factory_info in FACTORIES.items():
            for i, date_str in enumerate(factory_trends["dates"]):
                if factory_id in factory_daily_data and date_str in factory_daily_data[factory_id]:
                    factory_trends["factories"][factory_id]["production"][i] = factory_daily_data[factory_id][date_str]["production"]
                    factory_trends["factories"][factory_id]["sales"][i] = factory_daily_data[factory_id][date_str]["sales"]
                
                # Fill product-level data
                for product in factory_info["products"]:
                    if (factory_id in product_daily_data and 
                        date_str in product_daily_data[factory_id] and 
                        product in product_daily_data[factory_id][date_str]):
                        
                        factory_trends["factories"][factory_id]["production_by_product"][product][i] = product_daily_data[factory_id][date_str][product]["production"]
                        factory_trends["factories"][factory_id]["sales_by_product"][product][i] = product_daily_data[factory_id][date_str][product]["sales"]
        
        # Fill in overall downtime and stock data
        for i, date_str in enumerate(factory_trends["dates"]):
            if date_str in overall_daily_data:
                factory_trends["downtime"][i] = overall_daily_data[date_str]["downtime"]
                factory_trends["stock"][i] = overall_daily_data[date_str]["stock"]
        
        # Add this before the return statement in the headquarters section:
        print(f"Returning factory trends for headquarters:")
        print(f"- Number of factories: {len(factory_trends['factories'])}")
        print(f"- Factory IDs: {list(factory_trends['factories'].keys())}")
        print(f"- Date range: {len(factory_trends['dates'])} days")
        for fid, fdata in factory_trends['factories'].items():
            print(f"  Factory {fid}: {sum(fdata['production'])} total production, {sum(fdata['sales'])} total sales")

        return factory_trends

@api_router.get("/analytics/factory-comparison")
async def get_factory_comparison(
    current_user: User = Depends(get_current_user)
):
    """Get factory comparison data - today's data only"""
    if current_user.role == "factory_employer":
        raise HTTPException(status_code=403, detail="Access restricted to headquarters only")
    
    # Get today's data only
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    query = {"date": {"$gte": start_of_day, "$lte": end_of_day}}
    
    logs = await db.daily_logs.find(query).to_list(1000)
    
    factory_data = {}
    for factory_id, factory_info in FACTORIES.items():
        factory_logs = [log for log in logs if log["factory_id"] == factory_id]
        
        total_production = sum(sum(log["production_data"].values()) for log in factory_logs)
        total_sales = sum(sum(item["amount"] for item in log["sales_data"].values()) for log in factory_logs)
        total_revenue = sum(sum(item["amount"] * item["unit_price"] for item in log["sales_data"].values()) for log in factory_logs)
        total_downtime = sum(log["downtime_hours"] for log in factory_logs)
        
        factory_data[factory_id] = {
            "name": factory_info["name"],
            "production": total_production,
            "sales": total_sales,
            "revenue": total_revenue,
            "downtime": total_downtime,
            "efficiency": 0,  # Will calculate efficiency percentage
            "sku_unit": factory_info["sku_unit"]  # Add SKU unit for tooltips
        }
        
        # Calculate efficiency (production vs planned - using production as baseline)
        if factory_data[factory_id]["production"] > 0:
            planned_production = factory_data[factory_id]["production"] * 1.2  # Assume 20% more was planned
            factory_data[factory_id]["efficiency"] = (factory_data[factory_id]["production"] / planned_production) * 100
        else:
            factory_data[factory_id]["efficiency"] = 0
    
    return factory_data

@api_router.get("/dashboard-summary")
async def get_dashboard_summary(current_user: User = Depends(get_current_user)):
    # Get recent logs (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    query = {"date": {"$gte": thirty_days_ago}}
    if current_user.role == "factory_employer":
        query["factory_id"] = current_user.factory_id
    
    logs = await db.daily_logs.find(query).to_list(1000)
    
    # Calculate summaries - removed total_production and total_sales
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
        factory_summaries[factory_id]["production"] += production
        
        # Sales
        sales = sum(item["amount"] for item in log["sales_data"].values())
        factory_summaries[factory_id]["sales"] += sales
        
        # Downtime
        total_downtime += log["downtime_hours"]
        factory_summaries[factory_id]["downtime"] += log["downtime_hours"]
        
        # Stock
        stock = sum(log["stock_data"].values())
        total_stock += stock
        factory_summaries[factory_id]["stock"] += stock
    
    return {
        "total_downtime": total_downtime,
        "total_stock": total_stock,
        "factory_summaries": factory_summaries
    }

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
            "password_hash": get_password_hash("admin1234"),
            "role": "headquarters",
            "factory_id": None,
            "created_at": datetime.utcnow()
        }
        admin_obj = User(**admin_data)
        await db.users.insert_one(admin_obj.dict())
        logger.info("Created default admin user: admin/admin1234")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()