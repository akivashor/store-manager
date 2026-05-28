from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repository.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.auth import get_current_cashier, require_admin

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(include_inactive: bool = False, db: AsyncSession = Depends(get_db), cashier=Depends(get_current_cashier)):
    if include_inactive and not cashier.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return await ProductRepository(db).get_all(active_only=not include_inactive)


@router.get("/low-stock", response_model=list[ProductOut])
async def low_stock(db: AsyncSession = Depends(get_db), _=Depends(get_current_cashier)):
    return await ProductRepository(db).get_low_stock()


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_cashier)):
    product = await ProductRepository(db).get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", dependencies=[Depends(require_admin)])
async def create_product(data: ProductCreate, initial_stock: int = 0, min_quantity: int = 5, db: AsyncSession = Depends(get_db)):
    repo = ProductRepository(db)
    existing = await repo.get_by_name(data.name)
    if existing:
        return JSONResponse(
            status_code=409,
            content={"detail": "Product name already exists", "existing_id": existing.id, "existing_name": existing.name},
        )
    return await repo.create(data.model_dump(), initial_stock, min_quantity)


@router.patch("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = data.model_dump(exclude_none=True)
    if "name" in update_data and update_data["name"] != product.name:
        conflict = await repo.get_by_name(update_data["name"])
        if conflict:
            return JSONResponse(
                status_code=409,
                content={"detail": "Product name already exists", "existing_id": conflict.id, "existing_name": conflict.name},
            )
    return await repo.update(product, update_data)


@router.post("/{product_id}/deactivate", response_model=ProductOut, dependencies=[Depends(require_admin)])
async def deactivate_product(product_id: int, db: AsyncSession = Depends(get_db)):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return await repo.update(product, {"is_active": False})


@router.post("/{product_id}/reactivate", response_model=ProductOut, dependencies=[Depends(require_admin)])
async def reactivate_product(product_id: int, db: AsyncSession = Depends(get_db)):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return await repo.update(product, {"is_active": True})
