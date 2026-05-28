from datetime import datetime
from pydantic import BaseModel, EmailStr


class CashierCreate(BaseModel):
    cashier_code: str
    name: str
    email: EmailStr
    password: str
    is_admin: bool = False


class CashierOut(BaseModel):
    id: int
    cashier_code: str
    name: str
    email: str
    is_admin: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str
    cashier: CashierOut
