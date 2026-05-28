from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repository.sale_repository import SaleRepository
from app.repository.product_repository import ProductRepository
from app.schemas.sale import SaleCreate, SaleOut, StockAdjust
from app.auth import get_current_cashier, require_admin

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.post("", response_model=SaleOut)
async def create_sale(data: SaleCreate, db: AsyncSession = Depends(get_db), cashier=Depends(get_current_cashier)):
    product_repo = ProductRepository(db)
    items = []
    for item in data.items:
        product = await product_repo.get_by_id(item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if not product.stock or product.stock.quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")
        items.append({"product_id": item.product_id, "quantity": item.quantity, "unit_price": float(product.price)})

    return await SaleRepository(db).create(cashier.id, items, data.notes)


@router.get("/my", response_model=list[SaleOut])
async def my_sales(db: AsyncSession = Depends(get_db), cashier=Depends(get_current_cashier)):
    return await SaleRepository(db).get_by_cashier(cashier.id)


@router.get("/summary/daily")
async def daily_summary(target_date: date = None, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    return await SaleRepository(db).get_daily_summary(target_date or date.today())


@router.post("/stock/adjust", dependencies=[Depends(require_admin)])
async def adjust_stock(data: StockAdjust, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.stock import Stock
    result = await db.execute(select(Stock).where(Stock.product_id == data.product_id))
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock record not found")
    stock.quantity = data.quantity
    if data.min_quantity is not None:
        stock.min_quantity = data.min_quantity
    await db.commit()
    return {"product_id": data.product_id, "quantity": stock.quantity, "min_quantity": stock.min_quantity}
