"""Run once to create the first admin cashier."""
import asyncio
import sys
from app.database import AsyncSessionLocal
from app.repository.cashier_repository import CashierRepository


async def main(cashier_code: str, name: str, email: str, password: str):
    async with AsyncSessionLocal() as db:
        repo = CashierRepository(db)
        if await repo.get_by_email(email):
            print(f"Admin with email '{email}' already exists.")
            return
        cashier = await repo.create(cashier_code, name, email, password, is_admin=True)
        print(f"Admin created: [{cashier.cashier_code}] {cashier.name} <{cashier.email}>")


if __name__ == "__main__":
    print("Create first admin cashier")
    code = input("Cashier code (e.g. ADMIN01): ").strip()
    name = input("Name: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    asyncio.run(main(code, name, email, password))
