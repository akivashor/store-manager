from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repository.cashier_repository import CashierRepository
from app.schemas.cashier import CashierCreate, CashierOut, Token
from app.auth import create_access_token, get_current_cashier, require_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    repo = CashierRepository(db)
    cashier = await repo.get_by_email(form.username)
    if not cashier or not repo.verify_password(form.password, cashier.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": cashier.email})
    return {"access_token": token, "token_type": "bearer", "cashier": cashier}


@router.get("/me", response_model=CashierOut)
async def me(cashier=Depends(get_current_cashier)):
    return cashier


@router.post("/cashiers", response_model=CashierOut, dependencies=[Depends(require_admin)])
async def create_cashier(data: CashierCreate, db: AsyncSession = Depends(get_db)):
    repo = CashierRepository(db)
    if await repo.get_by_email(data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await repo.get_by_code(data.cashier_code):
        raise HTTPException(status_code=400, detail="Cashier code already in use")
    return await repo.create(data.cashier_code, data.name, data.email, data.password, data.is_admin)


@router.get("/cashiers", response_model=list[CashierOut], dependencies=[Depends(require_admin)])
async def list_cashiers(db: AsyncSession = Depends(get_db)):
    return await CashierRepository(db).get_all()
