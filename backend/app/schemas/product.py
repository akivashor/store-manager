from datetime import datetime
from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    category: str | None = None
    barcode: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    category: str | None = None
    barcode: str | None = None
    is_active: bool | None = None


class StockInfo(BaseModel):
    quantity: int
    min_quantity: int

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    category: str | None
    barcode: str | None
    is_active: bool
    created_at: datetime
    stock: StockInfo | None = None

    model_config = {"from_attributes": True}
