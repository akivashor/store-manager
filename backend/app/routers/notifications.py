import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.push_subscription import PushSubscription
from app.repository.product_repository import ProductRepository
from app.auth import get_current_cashier, require_admin
from app.config import settings

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.post("/subscribe")
async def subscribe(subscription: dict, db: AsyncSession = Depends(get_db), cashier=Depends(get_current_cashier)):
    db.add(PushSubscription(cashier_id=cashier.id, subscription_json=json.dumps(subscription)))
    await db.commit()
    return {"status": "subscribed"}


@router.get("/vapid-public-key")
async def vapid_public_key():
    return {"public_key": settings.vapid_public_key}


@router.post("/send-low-stock-alerts", dependencies=[Depends(require_admin)])
async def send_low_stock_alerts(db: AsyncSession = Depends(get_db)):
    if not settings.vapid_private_key:
        raise HTTPException(status_code=503, detail="Push notifications not configured")

    low_stock_products = await ProductRepository(db).get_low_stock()
    if not low_stock_products:
        return {"sent": 0, "message": "All stock levels are fine"}

    from pywebpush import webpush, WebPushException
    result = await db.execute(select(PushSubscription))
    subscriptions = result.scalars().all()

    sent = 0
    names = [p.name for p in low_stock_products]
    payload = json.dumps({"title": "Low Stock Alert", "body": f"Low stock: {', '.join(names)}", "products": names})

    for sub in subscriptions:
        try:
            webpush(
                subscription_info=json.loads(sub.subscription_json),
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": f"mailto:{settings.vapid_claims_email}"},
            )
            sent += 1
        except WebPushException:
            pass

    return {"sent": sent, "low_stock_products": names}
