from datetime import datetime
from pydantic import BaseModel


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int


class SaleCreate(BaseModel):
    items: list[SaleItemCreate]
    notes: str | None = None


class SaleItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

    model_config = {"from_attributes": True}


class SaleOut(BaseModel):
    id: int
    cashier_id: int
    total_amount: float
    notes: str | None
    created_at: datetime
    items: list[SaleItemOut]

    model_config = {"from_attributes": True}


class StockAdjust(BaseModel):
    product_id: int
    quantity: int
    min_quantity: int | None = None
