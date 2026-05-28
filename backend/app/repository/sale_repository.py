from datetime import datetime, date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.sale import Sale, SaleItem
from app.models.stock import Stock


class SaleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, cashier_id: int, items: list[dict], notes: str | None = None) -> Sale:
        total = sum(i["unit_price"] * i["quantity"] for i in items)
        sale = Sale(cashier_id=cashier_id, total_amount=total, notes=notes)
        self.db.add(sale)
        await self.db.flush()

        for item in items:
            self.db.add(SaleItem(
                sale_id=sale.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            ))
            result = await self.db.execute(select(Stock).where(Stock.product_id == item["product_id"]))
            stock = result.scalar_one_or_none()
            if stock:
                stock.quantity -= item["quantity"]
                stock.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(sale)
        return sale

    async def get_by_cashier(self, cashier_id: int, limit: int = 50) -> list[Sale]:
        result = await self.db.execute(
            select(Sale)
            .options(selectinload(Sale.items))
            .where(Sale.cashier_id == cashier_id)
            .order_by(Sale.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_daily_summary(self, target_date: date) -> dict:
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        result = await self.db.execute(
            select(func.count(Sale.id), func.sum(Sale.total_amount))
            .where(Sale.created_at.between(start, end))
        )
        count, total = result.one()
        return {"date": str(target_date), "total_sales": count or 0, "total_revenue": float(total or 0)}
