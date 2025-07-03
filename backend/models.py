from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class RRPPMarkupTable(Base):
    __tablename__ = "rrpp_markup_table"
    
    id = Column(Integer, primary_key=True, index=True)
    from_price = Column(Float)
    to_price = Column(Float)
    rrpp_markup = Column(Float)
