import pandas as pd
from typing import Dict, List
from sqlalchemy.orm import Session
from models import RRPPMarkupTable

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
                "From": record.from_price,
                "To": record.to_price,
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
            df['Purchase Cost'] = df['Purchase Cost'].replace('[$,]', '', regex=True).astype(float)
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
