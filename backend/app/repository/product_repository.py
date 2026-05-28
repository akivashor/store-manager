from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.product import Product
from app.models.stock import Stock


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, active_only: bool = True) -> list[Product]:
        q = select(Product).options(selectinload(Product.stock))
        if active_only:
            q = q.where(Product.is_active == True)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self.db.execute(
            select(Product).options(selectinload(Product.stock)).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_barcode(self, barcode: str) -> Product | None:
        result = await self.db.execute(
            select(Product).options(selectinload(Product.stock)).where(Product.barcode == barcode)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict, initial_stock: int = 0, min_quantity: int = 5) -> Product:
        product = Product(**data)
        self.db.add(product)
        await self.db.flush()
        if not product.barcode:
            product.barcode = f"SKU-{product.id:05d}"
        stock = Stock(product_id=product.id, quantity=initial_stock, min_quantity=min_quantity)
        self.db.add(stock)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update(self, product: Product, data: dict) -> Product:
        for key, value in data.items():
            if value is not None:
                setattr(product, key, value)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get_low_stock(self) -> list[Product]:
        result = await self.db.execute(
            select(Product)
            .join(Stock, Product.id == Stock.product_id)
            .options(selectinload(Product.stock))
            .where(Product.is_active == True)
            .where(Stock.quantity <= Stock.min_quantity)
        )
        return list(result.scalars().all())
