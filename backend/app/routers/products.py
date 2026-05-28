from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repository.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.auth import get_current_cashier, require_admin

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db), _=Depends(get_current_cashier)):
    return await ProductRepository(db).get_all()


@router.get("/low-stock", response_model=list[ProductOut])
async def low_stock(db: AsyncSession = Depends(get_db), _=Depends(get_current_cashier)):
    return await ProductRepository(db).get_low_stock()


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_cashier)):
    product = await ProductRepository(db).get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=ProductOut, dependencies=[Depends(require_admin)])
async def create_product(data: ProductCreate, initial_stock: int = 0, min_quantity: int = 5, db: AsyncSession = Depends(get_db)):
    return await ProductRepository(db).create(data.model_dump(), initial_stock, min_quantity)


@router.patch("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return await repo.update(product, data.model_dump(exclude_none=True))
