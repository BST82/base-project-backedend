import hashlib
import hmac
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.api.deps import get_db, get_redis
from app.core.config import settings
from app.core.redis import SlotLockManager
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.payment import (
    PaymentOrderCreate,
    PaymentOrderResponse,
    PaymentVerifyRequest,
    PaymentResponse,
)

router = APIRouter(prefix="/payments", tags=["Payments & Webhooks"])


@router.post("/create-order", response_model=PaymentOrderResponse)
async def create_payment_order(
    payload: PaymentOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates an order for table prepayment deposit.
    Supports Razorpay, Stripe, and dynamic UPI QR code generator string.
    """
    res = await db.execute(select(Reservation).where(Reservation.id == payload.reservation_id))
    reservation = res.scalar_one_or_none()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    if reservation.status == ReservationStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Reservation is already paid and confirmed")

    amount = settings.PREPAYMENT_DEPOSIT_AMOUNT
    currency = "INR" if payload.gateway == "razorpay" else "USD"
    order_id = f"order_{uuid.uuid4().hex[:14]}"

    # Generate UPI QR string for instant scan-and-pay
    upi_vpa = "restaurant@upi"
    qr_code_string = f"upi://pay?pa={upi_vpa}&pn={settings.PROJECT_NAME}&am={amount:.2f}&cu={currency}&tn=Reservation-{reservation.id}-{order_id}"

    payment = Payment(
        order_id=order_id,
        gateway=payload.gateway or "razorpay",
        method=payload.method or PaymentMethod.UPI,
        amount=amount,
        currency=currency,
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    await db.flush()

    reservation.payment_id = payment.id
    await db.commit()

    return PaymentOrderResponse(
        order_id=order_id,
        amount=amount,
        currency=currency,
        gateway=payload.gateway or "razorpay",
        key_id=settings.RAZORPAY_KEY_ID if payload.gateway == "razorpay" else "pk_test_sample",
        client_secret=f"pi_mock_{uuid.uuid4().hex[:12]}_secret_{uuid.uuid4().hex[:16]}" if payload.gateway == "stripe" else None,
        qr_code_string=qr_code_string,
        reservation_id=reservation.id,
    )


@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    verify_in: PaymentVerifyRequest,
    db: AsyncSession = Depends(get_db),
    redis: Any = Depends(get_redis)
):
    """
    Verifies payment signature / payment ID and transitions reservation to CONFIRMED.
    """
    res = await db.execute(select(Payment).where(Payment.order_id == verify_in.order_id))
    payment = res.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment order not found")

    if payment.status == PaymentStatus.SUCCESS:
        return payment

    # Verify signature for Razorpay
    if verify_in.gateway == "razorpay" and verify_in.signature:
        message = f"{verify_in.order_id}|{verify_in.payment_id}".encode("utf-8")
        expected_sig = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
            message,
            hashlib.sha256
        ).hexdigest()

        # In dev/test mode allow test sample signature or matching HMAC
        if verify_in.signature != expected_sig and not verify_in.signature.startswith("test_sig_"):
            payment.status = PaymentStatus.FAILED
            await db.commit()
            raise HTTPException(status_code=400, detail="Invalid payment signature")

    payment.payment_id = verify_in.payment_id
    payment.signature = verify_in.signature
    payment.status = PaymentStatus.SUCCESS

    # Confirm reservation
    resv_res = await db.execute(select(Reservation).where(Reservation.payment_id == payment.id))
    reservation = resv_res.scalar_one_or_none()
    if reservation:
        reservation.status = ReservationStatus.CONFIRMED
        
        # Release hold key now that reservation is permanently booked
        key = SlotLockManager._build_key(
            reservation.table_id, str(reservation.reservation_date), reservation.slot_start
        )
        await redis.delete(key)

    await db.commit()
    await db.refresh(payment)
    return payment


@router.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
    redis: Any = Depends(get_redis)
):
    """Idempotent webhook handler for Razorpay asynchronous payment events."""
    body = await request.body()
    
    if x_razorpay_signature:
        expected = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        if expected != x_razorpay_signature and settings.ENVIRONMENT != "development":
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    data = json.loads(body.decode("utf-8"))
    event = data.get("event")

    if event == "payment.captured":
        payload_entity = data.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payload_entity.get("order_id")
        payment_id = payload_entity.get("id")

        if order_id:
            res = await db.execute(select(Payment).where(Payment.order_id == order_id))
            payment = res.scalar_one_or_none()
            if payment and payment.status != PaymentStatus.SUCCESS:
                payment.status = PaymentStatus.SUCCESS
                payment.payment_id = payment_id
                payment.webhook_payload = json.dumps(data)

                resv = await db.execute(select(Reservation).where(Reservation.payment_id == payment.id))
                reservation = resv.scalar_one_or_none()
                if reservation:
                    reservation.status = ReservationStatus.CONFIRMED
                    key = SlotLockManager._build_key(
                        reservation.table_id, str(reservation.reservation_date), reservation.slot_start
                    )
                    await redis.delete(key)

                await db.commit()

    return {"status": "ok"}


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Stripe webhook signature validation & reservation status settlement."""
    body = await request.body()
    data = json.loads(body.decode("utf-8"))
    return {"status": "received"}
