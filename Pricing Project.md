<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# This streamlit app is a preliminary design, please impement it in the new framework:

import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Pricing Tool", layout="wide")
st.title("📦 Ozwide Pricing Calculator")

# File Upload

uploaded_file = st.file_uploader("Upload purchase file (Excel)", type=[".xlsx", ".xls"])

if uploaded_file:
df = pd.read_excel(uploaded_file)
df.columns = df.columns.str.strip()  \# Remove whitespace from headers

    st.subheader("File Preview")
    st.dataframe(df.head(20))
    
    st.subheader("Input Parameters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        currency = st.selectbox("Currency", options=["AUD", "USD"], index=0)
    with col2:
        exchange_rate = st.number_input("Exchange Rate (if not AUD)", min_value=0.0, value=1.0, step=0.01)
    with col3:
        freight_cost = st.number_input("Total Freight Cost (AUD)", min_value=0.0, value=0.0, step=1.0)
    with col4:
        freight_mode = st.selectbox("Freight Mode", options=["Auto", "Manual"], index=0)
    
    if freight_mode == "Manual":
        st.warning("Manual freight mode selected. Please ensure freight rate is added as a percentage elsewhere.")
    
    show_rrpp_editor = st.checkbox("Edit RRPP Markup Table", value=False)
    
    conn = sqlite3.connect("local_pricing.db")
    try:
        markup_data = pd.read_sql("SELECT * FROM rrpp_markup_table", conn)
    except:
        markup_data = pd.DataFrame([
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
        ], columns=["From", "To", "RRPP Markup"])
    
    if show_rrpp_editor:
        st.subheader("🛠️ RRPP Markup Table")
        edited_markup = st.data_editor(markup_data, use_container_width=True, num_rows="dynamic")
        edited_markup.to_sql("rrpp_markup_table", conn, if_exists="replace", index=False)
    else:
        edited_markup = markup_data
    
    category_multipliers = {
        "Speciality": 2.2,
        "Speciality Fast": 1.5,
        "Universal": 0.9,
        "Diagnostic": 1.7,
        "ATS": 1,
        "PICO": 1.2,
        "Local": 1,
        "N/A": 1,
        "Trucks": 3,
        "Autool": 1.45
    }
    
    if st.button("Calculate Price"):
        try:
            df['Purchase Cost'] = df['Purchase Cost'].replace('[\$,]', '', regex=True).astype(float)
            df['Qty'] = df['Qty'].astype(float)
    
            total_purchase = (df['Qty'] * df['Purchase Cost']).sum()
            df['Purchase Cost AUD'] = df['Purchase Cost'] / exchange_rate if currency != "AUD" else df['Purchase Cost']
    
            df['Landed Cost AUD'] = df.apply(lambda row: row['Purchase Cost AUD'] + (((row['Qty'] * row['Purchase Cost']) / total_purchase) * freight_cost) / row['Qty'], axis=1)
    
            def lookup_rrpp_markup(cost):
                row = edited_markup[(edited_markup['From'] <= cost) & (cost <= edited_markup['To'])]
                return float(row['RRPP Markup'].iloc[0]) if not row.empty else 1.0
    
            df['RRPP Markup'] = df['Landed Cost AUD'].apply(lookup_rrpp_markup)
            df['Category Multiplier'] = df['Category'].map(category_multipliers).fillna(1.0)
            df['RRPP'] = (df['Landed Cost AUD'] * ((df['RRPP Markup'] * df['Category Multiplier'])+1)).round(0)
    
            df['Tier 1'] = df.apply(lambda row: round(row['RRPP'] * 0.95 if row['Category'] in ['Speciality Fast', 'Universal', 'Local'] else row['RRPP'] * 0.9), axis=1)
            df['Tier 2'] = df.apply(lambda row: round(row['RRPP'] * 1.37) if ((-row['RRPP'] + (row['Tier 1'] * 0.95)) / row['RRPP']) > 0.37 else round(row['Tier 1'] * 0.95), axis=1)
            df['Tier 3'] = df.apply(lambda row: round(row['RRPP'] * 1.35) if ((-row['RRPP'] + (row['Tier 2'] * 0.9)) / row['RRPP']) > 0.35 else round(row['Tier 2'] * 0.9), axis=1)
            df['Tier 4'] = df.apply(lambda row: round(row['RRPP'] * 1.3) if ((-row['RRPP'] + (row['Tier 3'] * 0.85)) / row['RRPP']) > 0.3 else round(row['Tier 3'] * 0.85), axis=1)
            df['Tier 5'] = df.apply(lambda row: round(row['RRPP'] * 1.25) if ((-row['RRPP'] + (row['Tier 4'] * 0.95)) / row['RRPP']) > 0.25 else round(row['Tier 4'] * 0.95), axis=1)
    
            st.success("Landed Cost, RRPP, and Tiers calculated successfully.")
            st.dataframe(df)
    
            df.to_sql("priced_parts", conn, if_exists="replace", index=False)
            conn.close()
            st.success("Data saved to local_pricing.db (tables: priced_parts, rrpp_markup_table)")
    
        except Exception as e:
            st.error(f"An error occurred: {e}")
    I'll convert your Streamlit app to the FastAPI framework we established earlier. Here's the complete implementation:

## Updated FastAPI Backend

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd
import secrets
from datetime import datetime
import os
import json
from typing import Optional, List, Dict

# Database setup
DATABASE_URL = "sqlite:///./local_pricing.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database Models
class PricedParts(Base):
    __tablename__ = "priced_parts"
    
    id = Column(Integer, primary_key=True, index=True)
    part_number = Column(String, index=True)
    description = Column(String)
    qty = Column(Float)
    purchase_cost = Column(Float)
    purchase_cost_aud = Column(Float)
    landed_cost_aud = Column(Float)
    category = Column(String)
    rrpp_markup = Column(Float)
    category_multiplier = Column(Float)
    rrpp = Column(Float)
    tier_1 = Column(Float)
    tier_2 = Column(Float)
    tier_3 = Column(Float)
    tier_4 = Column(Float)
    tier_5 = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class RRPPMarkupTable(Base):
    __tablename__ = "rrpp_markup_table"
    
    id = Column(Integer, primary_key=True, index=True)
    from_price = Column(Float, name="from_range")
    to_price = Column(Float, name="to_range")
    rrpp_markup = Column(Float)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ozwide Pricing Calculator API")

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

# Initialize default RRPP markup table
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
                from_range=from_price,
                to_range=to_price,
                rrpp_markup=markup
            )
            db.add(markup_record)
        db.commit()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        initialize_rrpp_table(db)
    finally:
        db.close()
```


## Pricing Engine Implementation

```python
# pricing_engine.py
import pandas as pd
from typing import Dict, List
from sqlalchemy.orm import Session
from main import RRPPMarkupTable

class OzwidePricingEngine:
    def __init__(self, db: Session):
        self.db = db
        self.category_multipliers = {
            "Speciality": 2.2,
            "Speciality Fast": 1.5,
            "Universal": 0.9,
            "Diagnostic": 1.7,
            "ATS": 1,
            "PICO": 1.2,
            "Local": 1,
            "N/A": 1,
            "Trucks": 3,
            "Autool": 1.45
        }
    
    def get_rrpp_markup_table(self) -> pd.DataFrame:
        """Get RRPP markup table from database"""
        markup_records = self.db.query(RRPPMarkupTable).all()
        return pd.DataFrame([
            {
                "From": record.from_range,
                "To": record.to_range,
                "RRPP Markup": record.rrpp_markup
            }
            for record in markup_records
        ])
    
    def lookup_rrpp_markup(self, cost: float) -> float:
        """Lookup RRPP markup based on cost"""
        markup_table = self.get_rrpp_markup_table()
        row = markup_table[(markup_table['From'] <= cost) & (cost <= markup_table['To'])]
        return float(row['RRPP Markup'].iloc[0]) if not row.empty else 1.0
    
    def process_uploaded_file(self, file_path: str) -> pd.DataFrame:
        """Process uploaded Excel file"""
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()  # Remove whitespace from headers
            
            # Validate required columns
            required_columns = ['Purchase Cost', 'Qty']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            return df
        except Exception as e:
            raise ValueError(f"Error processing file: {str(e)}")
    
    def calculate_pricing(self, df: pd.DataFrame, currency: str, exchange_rate: float, 
                         freight_cost: float, freight_mode: str) -> pd.DataFrame:
        """Calculate pricing with Ozwide logic"""
        try:
            # Clean and convert data types
            df['Purchase Cost'] = df['Purchase Cost'].replace('[\$,]', '', regex=True).astype(float)
            df['Qty'] = df['Qty'].astype(float)
            
            # Calculate total purchase for freight allocation
            total_purchase = (df['Qty'] * df['Purchase Cost']).sum()
            
            # Convert to AUD
            df['Purchase Cost AUD'] = df['Purchase Cost'] / exchange_rate if currency != "AUD" else df['Purchase Cost']
            
            # Calculate landed cost with freight allocation
            if freight_mode == "Auto" and freight_cost > 0:
                df['Landed Cost AUD'] = df.apply(
                    lambda row: row['Purchase Cost AUD'] + (
                        ((row['Qty'] * row['Purchase Cost']) / total_purchase) * freight_cost
                    ) / row['Qty'], 
                    axis=1
                )
            else:
                df['Landed Cost AUD'] = df['Purchase Cost AUD']
            
            # Apply RRPP markup lookup
            df['RRPP Markup'] = df['Landed Cost AUD'].apply(self.lookup_rrpp_markup)
            
            # Apply category multipliers
            df['Category Multiplier'] = df['Category'].map(self.category_multipliers).fillna(1.0)
            
            # Calculate RRPP
            df['RRPP'] = (df['Landed Cost AUD'] * ((df['RRPP Markup'] * df['Category Multiplier']) + 1)).round(0)
            
            # Calculate tiers with Ozwide logic
            df['Tier 1'] = df.apply(
                lambda row: round(row['RRPP'] * 0.95) if row['Category'] in ['Speciality Fast', 'Universal', 'Local'] 
                else round(row['RRPP'] * 0.9), 
                axis=1
            )
            
            df['Tier 2'] = df.apply(
                lambda row: round(row['RRPP'] * 1.37) if ((-row['RRPP'] + (row['Tier 1'] * 0.95)) / row['RRPP']) > 0.37 
                else round(row['Tier 1'] * 0.95), 
                axis=1
            )
            
            df['Tier 3'] = df.apply(
                lambda row: round(row['RRPP'] * 1.35) if ((-row['RRPP'] + (row['Tier 2'] * 0.9)) / row['RRPP']) > 0.35 
                else round(row['Tier 2'] * 0.9), 
                axis=1
            )
            
            df['Tier 4'] = df.apply(
                lambda row: round(row['RRPP'] * 1.3) if ((-row['RRPP'] + (row['Tier 3'] * 0.85)) / row['RRPP']) > 0.3 
                else round(row['Tier 3'] * 0.85), 
                axis=1
            )
            
            df['Tier 5'] = df.apply(
                lambda row: round(row['RRPP'] * 1.25) if ((-row['RRPP'] + (row['Tier 4'] * 0.95)) / row['RRPP']) > 0.25 
                else round(row['Tier 4'] * 0.95), 
                axis=1
            )
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error calculating pricing: {str(e)}")
```


## API Endpoints

```python
# Add to main.py

@app.post("/upload-and-calculate/")
async def upload_and_calculate(
    file: UploadFile = File(...),
    currency: str = Form("AUD"),
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
            record = PricedParts(
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

@app.get("/rrpp-markup-table/")
async def get_rrpp_markup_table(
    current_user: str = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    """Get RRPP markup table"""
    markup_records = db.query(RRPPMarkupTable).all()
    return [
        {
            "id": record.id,
            "from": record.from_range,
            "to": record.to_range,
            "rrpp_markup": record.rrpp_markup
        }
        for record in markup_records
    ]

@app.put("/rrpp-markup-table/")
async def update_rrpp_markup_table(
    markup_data: List[Dict],
    current_user: str = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    """Update RRPP markup table"""
    try:
        # Clear existing data
        db.query(RRPPMarkupTable).delete()
        
        # Add new data
        for item in markup_data:
            record = RRPPMarkupTable(
                from_range=float(item['from']),
                to_range=float(item['to']),
                rrpp_markup=float(item['rrpp_markup'])
            )
            db.add(record)
        
        db.commit()
        return {"message": f"Updated {len(markup_data)} markup records"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/priced-parts/")
async def get_priced_parts(
    current_user: str = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    """Get latest priced parts"""
    records = db.query(PricedParts).order_by(PricedParts.created_at.desc()).all()
    return [
        {
            "id": record.id,
            "part_number": record.part_number,
            "description": record.description,
            "qty": record.qty,
            "purchase_cost": record.purchase_cost,
            "landed_cost_aud": record.landed_cost_aud,
            "category": record.category,
            "rrpp": record.rrpp,
            "tier_1": record.tier_1,
            "tier_2": record.tier_2,
            "tier_3": record.tier_3,
            "tier_4": record.tier_4,
            "tier_5": record.tier_5,
            "created_at": record.created_at
        }
        for record in records
    ]

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
```


## Updated Requirements

```txt
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pandas==2.1.3
openpyxl==3.1.2
sqlalchemy==2.0.23
python-multipart==0.0.6
requests==2.31.0
xlrd==2.0.1
```


## Usage Instructions

**Build and run:**

```bash
docker build -t ozwide-pricing .
docker-compose up -d
```

**API Endpoints:**

- Upload \& Calculate: `POST /upload-and-calculate/`
- Get RRPP Table: `GET /rrpp-markup-table/`
- Update RRPP Table: `PUT /rrpp-markup-table/`
- Get Priced Parts: `GET /priced-parts/`
- Export CSV: `GET /export-csv/`
- API Docs: `http://localhost:8000/docs`

**Authentication:** Username: `admin`, Password: `pricing123`

This FastAPI implementation maintains all the Streamlit functionality while providing a robust API structure that can be easily integrated with a React frontend or used directly via the API documentation interface.

