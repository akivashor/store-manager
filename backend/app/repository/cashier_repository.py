import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.cashier import Cashier


class CashierRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Cashier | None:
        result = await self.db.execute(select(Cashier).where(Cashier.email == email))
        return result.scalar_one_or_none()

    async def get_by_code(self, cashier_code: str) -> Cashier | None:
        result = await self.db.execute(select(Cashier).where(Cashier.cashier_code == cashier_code))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Cashier]:
        result = await self.db.execute(select(Cashier).where(Cashier.is_active == True))
        return list(result.scalars().all())

    async def create(self, cashier_code: str, name: str, email: str, password: str, is_admin: bool = False) -> Cashier:
        cashier = Cashier(
            cashier_code=cashier_code,
            name=name,
            email=email,
            hashed_password=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            is_admin=is_admin,
        )
        self.db.add(cashier)
        await self.db.commit()
        await self.db.refresh(cashier)
        return cashier

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
