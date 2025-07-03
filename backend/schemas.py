from pydantic import BaseModel
from datetime import datetime
from typing import List

class PricedPartBase(BaseModel):
    part_number: str
    description: str
    qty: float
    purchase_cost: float
    purchase_cost_aud: float
    landed_cost_aud: float
    category: str
    rrpp_markup: float
    category_multiplier: float
    rrpp: float
    tier_1: float
    tier_2: float
    tier_3: float
    tier_4: float
    tier_5: float

class PricedPartCreate(PricedPartBase):
    pass

class PricedPart(PricedPartBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class RRPPMarkupBase(BaseModel):
    from_price: float
    to_price: float
    rrpp_markup: float

class RRPPMarkupCreate(RRPPMarkupBase):
    pass

class RRPPMarkup(RRPPMarkupBase):
    id: int

    class Config:
        from_attributes = True
