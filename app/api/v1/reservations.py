from datetime import date, datetime, timedelta
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_redis, get_current_user, get_optional_current_user, get_current_active_admin
from app.core.config import settings
from app.core.redis import SlotLockManager
from app.models.reservation import Table, Reservation, ReservationStatus
from app.models.user import User
from app.schemas.reservation import (
    TableResponse,
    TableCreate,
    AvailableSlot,
    ReservationHoldRequest,
    ReservationHoldResponse,
    ReservationCreate,
    ReservationResponse,
    ReservationStatusUpdate,
    ReservationRescheduleRequest,
)

router = APIRouter(prefix="/reservations", tags=["Table Reservations"])

# Standard dining time slots
STANDARD_SLOTS = [
    ("12:00", "13:30"),
    ("13:30", "15:00"),
    ("18:00", "19:30"),
    ("19:30", "21:00"),
    ("21:00", "22:30"),
]


# ==============================================================================
# Tables & Availability
# ==============================================================================

@router.get("/tables", response_model=List[TableResponse])
async def list_tables(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Table).where(Table.is_active == True).order_by(Table.capacity))
    return result.scalars().all()


@router.post("/tables", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
async def create_table(
    table_in: TableCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    table = Table(**table_in.model_dump())
    db.add(table)
    await db.commit()
    await db.refresh(table)
    return table


@router.get("/available-slots", response_model=List[AvailableSlot])
async def check_available_slots(
    date_val: date = Query(..., alias="date"),
    guests: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """
    Evaluates available tables for the requested date and party size,
    checking for collision against PostgreSQL confirmed/pending reservations and
    active Redis checkout temporary holds.
    """
    # 1. Fetch tables that can accommodate the party size
    tables_res = await db.execute(
        select(Table).where(and_(Table.capacity >= guests, Table.is_active == True))
    )
    suitable_tables = tables_res.scalars().all()

    # 2. Fetch existing active reservations for the date
    resv_query = await db.execute(
        select(Reservation).where(
            and_(
                Reservation.reservation_date == date_val,
                Reservation.status.in_([ReservationStatus.CONFIRMED, ReservationStatus.PENDING_PAYMENT])
            )
        )
    )
    active_reservations = resv_query.scalars().all()
    
    # Map of (table_id, slot_start) -> booked
    booked_map = {(r.table_id, r.slot_start): True for r in active_reservations}

    available_slots: List[AvailableSlot] = []

    for table in suitable_tables:
        for slot_start, slot_end in STANDARD_SLOTS:
            # Check DB collision
            if (table.id, slot_start) in booked_map:
                continue

            # Check Redis temporary hold
            is_held = await SlotLockManager.is_slot_held(
                redis=redis,
                table_id=table.id,
                date_str=str(date_val),
                slot_start=slot_start
            )
            if is_held:
                continue

            available_slots.append(
                AvailableSlot(
                    slot_start=slot_start,
                    slot_end=slot_end,
                    table_id=table.id,
                    table_number=table.table_number,
                    capacity=table.capacity,
                    location=table.location,
                    is_available=True
                )
            )

    return available_slots


# ==============================================================================
# Slot Locking (Redis Temporary Hold)
# ==============================================================================

@router.post("/hold-slot", response_model=ReservationHoldResponse)
async def hold_slot(
    hold_in: ReservationHoldRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """
    Locks a table slot for 10 minutes in Redis while the customer completes checkout.
    Prevents race conditions / double bookings across multiple users.
    """
    # 1. Verify table exists
    t_res = await db.execute(select(Table).where(Table.id == hold_in.table_id))
    if not t_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Table not found")

    # 2. Verify DB collision
    db_resv = await db.execute(
        select(Reservation).where(
            and_(
                Reservation.table_id == hold_in.table_id,
                Reservation.reservation_date == hold_in.date,
                Reservation.slot_start == hold_in.slot_start,
                Reservation.status.in_([ReservationStatus.CONFIRMED, ReservationStatus.PENDING_PAYMENT])
            )
        )
    )
    if db_resv.scalar_one_or_none():
        return ReservationHoldResponse(
            success=False,
            session_id=hold_in.session_id,
            held_until_seconds=0,
            message="This slot has already been reserved"
        )

    # 3. Attempt atomic acquire in Redis
    acquired = await SlotLockManager.acquire_hold(
        redis=redis,
        table_id=hold_in.table_id,
        date_str=str(hold_in.date),
        slot_start=hold_in.slot_start,
        session_id=hold_in.session_id,
        ttl_seconds=settings.RESERVATION_HOLD_SECONDS
    )

    if not acquired:
        return ReservationHoldResponse(
            success=False,
            session_id=hold_in.session_id,
            held_until_seconds=0,
            message="Slot is currently on hold by another customer. Please choose another slot or retry in a few moments."
        )

    return ReservationHoldResponse(
        success=True,
        session_id=hold_in.session_id,
        held_until_seconds=settings.RESERVATION_HOLD_SECONDS,
        message="Slot successfully held for 10 minutes"
    )


# ==============================================================================
# Reservation Creation & Lifecycle
# ==============================================================================

@router.post("/book", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_in: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Creates a reservation record with PENDING_PAYMENT status.
    Requires an active Redis temporary hold for the session.
    """
    # Verify slot hold exists for this session
    key = SlotLockManager._build_key(
        booking_in.table_id, str(booking_in.reservation_date), booking_in.slot_start
    )
    holding_session = await redis.get(key)
    if holding_session != booking_in.session_id:
        raise HTTPException(
            status_code=400,
            detail="Session hold has expired or is invalid. Please select a slot again."
        )

    reservation = Reservation(
        table_id=booking_in.table_id,
        user_id=current_user.id if current_user else None,
        customer_name=booking_in.customer_name,
        customer_email=booking_in.customer_email,
        customer_phone=booking_in.customer_phone,
        reservation_date=booking_in.reservation_date,
        slot_start=booking_in.slot_start,
        slot_end=booking_in.slot_end,
        guests=booking_in.guests,
        special_requests=booking_in.special_requests,
        status=ReservationStatus.PENDING_PAYMENT,
    )
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)

    res = await db.execute(
        select(Reservation).options(selectinload(Reservation.table)).where(Reservation.id == reservation.id)
    )
    return res.scalar_one()


@router.get("/my", response_model=List[ReservationResponse])
async def list_my_reservations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Reservation)
        .options(selectinload(Reservation.table))
        .where(Reservation.user_id == current_user.id)
        .order_by(Reservation.reservation_date.desc())
    )
    return result.scalars().all()


@router.get("/all", response_model=List[ReservationResponse])
async def list_all_reservations(
    date_val: Optional[date] = None,
    status_val: Optional[ReservationStatus] = None,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    query = select(Reservation).options(selectinload(Reservation.table))
    if date_val:
        query = query.where(Reservation.reservation_date == date_val)
    if status_val:
        query = query.where(Reservation.status == status_val)
    
    result = await db.execute(query.order_by(Reservation.reservation_date.desc(), Reservation.slot_start))
    return result.scalars().all()


@router.patch("/{reservation_id}/status", response_model=ReservationResponse)
async def update_reservation_status(
    reservation_id: int,
    status_update: ReservationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_active_admin)
):
    res = await db.execute(
        select(Reservation).options(selectinload(Reservation.table)).where(Reservation.id == reservation_id)
    )
    reservation = res.scalar_one_or_none()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    reservation.status = status_update.status
    await db.commit()
    await db.refresh(reservation)
    return reservation


@router.patch("/{reservation_id}/reschedule", response_model=ReservationResponse)
async def reschedule_reservation(
    reservation_id: int,
    reschedule_in: ReservationRescheduleRequest,
    db: AsyncSession = Depends(get_db)
):
    """Admin / management portal: reschedule a booking date, slot, or table."""
    res = await db.execute(
        select(Reservation).options(selectinload(Reservation.table)).where(Reservation.id == reservation_id)
    )
    reservation = res.scalar_one_or_none()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    reservation.reservation_date = reschedule_in.reservation_date
    reservation.slot_start = reschedule_in.slot_start
    reservation.slot_end = reschedule_in.slot_end
    if reschedule_in.table_id:
        reservation.table_id = reschedule_in.table_id
    reservation.status = ReservationStatus.CONFIRMED

    await db.commit()
    await db.refresh(reservation)
    
    reloaded = await db.execute(
        select(Reservation).options(selectinload(Reservation.table)).where(Reservation.id == reservation.id)
    )
    return reloaded.scalar_one()

