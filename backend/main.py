# main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd
import secrets
from datetime import datetime, timezone
import os
import json
from typing import List, Literal
from contextlib import asynccontextmanager

# Database setup
DATABASE_URL = "sqlite:///./local_pricing.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from models import Base, PricedParts, RRPPMarkupTable
from pricing_engine import OzwidePricingEngine
import schemas

Base.metadata.create_all(bind=engine)

def initialize_rrpp_table(db: Session):
    existing_count = db.query(RRPPMarkupTable).count()
    if existing_count == 0:
        default_markups = [
            [0.00, 2.49, 2.586508714], [2.50, 4.99, 2.330134294], [5.00, 7.99, 2.102174088],
            [8.00, 9.99, 1.900946641], [10.00, 11.99, 1.7247705], [12.00, 14.99, 1.57196421],
            [15.00, 16.99, 1.440846316], [17.00, 19.99, 1.329735365], [20.00, 21.99, 1.236949903],
            [22.00, 24.99, 1.160808475], [25.00, 27.99, 1.099629626], [28.00, 29.99, 1.051731904],
            [30.00, 34.99, 1.015433853], [35.00, 39.99, 0.989054019], [40.00, 44.99, 0.970910948],
            [45.00, 49.99, 1.050687299], [50.00, 54.99, 1.052406441], [55.00, 59.99, 1.057554945],
            [60.00, 69.99, 1.217670698], [70.00, 79.99, 1.214866467], [80.00, 89.99, 0.985666114],
            [90.00, 99.99, 0.933296661], [100.00, 109.99, 0.920515342], [110.00, 119.99, 0.900837698],
            [120.00, 149.99, 0.872582275], [150.00, 169.99, 0.834067618], [170.00, 199.99, 0.783612273],
            [200.00, 249.99, 0.719534787], [250.00, 299.99, 0.701120724], [300.00, 499.99, 0.543787571],
            [500.00, 749.99, 0.428754933], [750.00, 999.99, 0.293374337], [1000.00, 5000.00, 0.135964327]
        ]
        
        for from_price, to_price, markup in default_markups:
            markup_record = RRPPMarkupTable(
                from_price=from_price,
                to_price=to_price,
                rrpp_markup=markup
            )
            db.add(markup_record)
        db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        initialize_rrpp_table(db)
        yield
    finally:
        db.close()

app = FastAPI(title="Ozwide Pricing Calculator API", lifespan=lifespan)

# Simple Authentication
security = HTTPBasic()

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "pricing123")
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/upload-and-calculate/")
async def upload_and_calculate(
    file: UploadFile = File(...),
    currency: Literal["USD", "AUD", "EUR", "JPY"] = Form("AUD"),
    exchange_rate: float = Form(1.0),
    freight_cost: float = Form(0.0),
    freight_mode: str = Form("Auto"),
    current_user: str = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    """Upload Excel file and calculate pricing"""
    
    # Save uploaded file temporarily
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    try:
        # Process file
        pricing_engine = OzwidePricingEngine(db)
        df = pricing_engine.process_uploaded_file(file_path)
        
        # Return preview for first 20 rows
        preview_data = df.head(20).to_dict('records')
        
        # Calculate pricing
        processed_df = pricing_engine.calculate_pricing(df, currency, exchange_rate, freight_cost, freight_mode)
        
        # Save to database
        db.query(PricedParts).delete()  # Clear existing data
        
        for _, row in processed_df.iterrows():
            part_data = schemas.PricedPartCreate(
                part_number=str(row.get('Part Number', '')),
                description=str(row.get('Description', '')),
                qty=float(row['Qty']),
                purchase_cost=float(row['Purchase Cost']),
                purchase_cost_aud=float(row['Purchase Cost AUD']),
                landed_cost_aud=float(row['Landed Cost AUD']),
                category=str(row.get('Category', 'N/A')),
                rrpp_markup=float(row['RRPP Markup']),
                category_multiplier=float(row['Category Multiplier']),
                rrpp=float(row['RRPP']),
                tier_1=float(row['Tier 1']),
                tier_2=float(row['Tier 2']),
                tier_3=float(row['Tier 3']),
                tier_4=float(row['Tier 4']),
                tier_5=float(row['Tier 5'])
            )
            record = PricedParts(**part_data.model_dump())
            db.add(record)
        
        db.commit()
        
        # Return processed data
        result_data = processed_df.to_dict('records')
        
        return {
            "message": f"Successfully processed {len(result_data)} records",
            "preview": preview_data,
            "processed_data": result_data,
            "parameters": {
                "currency": currency,
                "exchange_rate": exchange_rate,
                "freight_cost": freight_cost,
                "freight_mode": freight_mode
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/rrpp-markup-table/", response_model=List[schemas.RRPPMarkup])
async def get_rrpp_markup_table(
    current_user: str = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    """Get RRPP markup table"""
    markup_records = db.query(RRPPMarkupTable).all()
    return markup_records

@app.put("/rrpp-markup-table/", response_model=List[schemas.RRPPMarkup])
async def update_rrpp_markup_table(
    markup_data: List[schemas.RRPPMarkupCreate],
    current_user: str = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    """Update RRPP markup table"""
    try:
        # Clear existing data
        db.query(RRPPMarkupTable).delete()
        
        # Add new data
        for item in markup_data:
            record = RRPPMarkupTable(**item.model_dump())
            db.add(record)
        
        db.commit()
        db.refresh(record)
        return db.query(RRPPMarkupTable).all()
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/priced-parts/", response_model=List[schemas.PricedPart])
async def get_priced_parts(
    current_user: str = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    """Get latest priced parts"""
    records = db.query(PricedParts).order_by(PricedParts.created_at.desc()).all()
    return records

@app.get("/export-csv/")
async def export_csv(
    current_user: str = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    """Export priced parts as CSV"""
    from fastapi.responses import StreamingResponse
    import io
    
    records = db.query(PricedParts).all()
    
    # Convert to DataFrame
    data = []
    for record in records:
        data.append({
            "Part Number": record.part_number,
            "Description": record.description,
            "Qty": record.qty,
            "Purchase Cost": record.purchase_cost,
            "Landed Cost AUD": record.landed_cost_aud,
            "Category": record.category,
            "RRPP": record.rrpp,
            "Tier 1": record.tier_1,
            "Tier 2": record.tier_2,
            "Tier 3": record.tier_3,
            "Tier 4": record.tier_4,
            "Tier 5": record.tier_5
        })
    
    df = pd.DataFrame(data)
    
    # Create CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=priced_parts.csv"}
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": "Ozwide Pricing Calculator"}
