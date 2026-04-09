from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device import Device
from app.models.family import Family
from app.models.user import User
from app.schemas.auth import (
    DeviceJoinRequest,
    DeviceRegisterRequest,
    JoinFamilyRequest,
    LoginRequest,
    QuickRegisterRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth import (
    create_token,
    generate_invite_code,
    get_family_by_invite_code,
    get_user_by_email,
    hash_password,
    verify_password,
)
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user and create a new family."""
    if await get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    family = Family(name=req.family_name, invite_code=generate_invite_code())
    db.add(family)
    await db.flush()

    user = User(
        family_id=family.id,
        email=req.email,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    await db.commit()

    token = create_token(user.id, family.id)
    return TokenResponse(
        access_token=token,
        family_uuid=str(family.uuid),
        invite_code=family.invite_code,
    )


@router.post("/join", response_model=TokenResponse)
async def join_family(req: JoinFamilyRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user and join an existing family via invite code."""
    if await get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    family = await get_family_by_invite_code(db, req.invite_code)
    if not family:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    user = User(
        family_id=family.id,
        email=req.email,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    await db.commit()

    token = create_token(user.id, family.id)
    return TokenResponse(
        access_token=token,
        family_uuid=str(family.uuid),
        invite_code=family.invite_code,
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    user = await get_user_by_email(db, req.email)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    from sqlalchemy import select
    result = await db.execute(select(Family).where(Family.id == user.family_id))
    family = result.scalar_one()

    token = create_token(user.id, family.id)
    return TokenResponse(
        access_token=token,
        family_uuid=str(family.uuid),
        invite_code=family.invite_code,
    )


@router.post("/quick-register", response_model=TokenResponse)
async def quick_register(req: QuickRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register with just a username. Create or join a family."""
    fake_email = f"{req.username}-{generate_invite_code(6)}@user.local"

    if req.invite_code:
        # Join existing family
        family = await get_family_by_invite_code(db, req.invite_code)
        if not family:
            raise HTTPException(status_code=404, detail="邀请码无效")
    else:
        # Create new family
        family = Family(name=f"{req.username}的家庭", invite_code=generate_invite_code())
        db.add(family)
        await db.flush()

    user = User(
        family_id=family.id,
        email=fake_email,
        password_hash="quick",
    )
    db.add(user)
    await db.commit()

    token = create_token(user.id, family.id)
    return TokenResponse(
        access_token=token,
        family_uuid=str(family.uuid),
        invite_code=family.invite_code,
    )


@router.post("/device-join", response_model=TokenResponse)
async def device_join(req: DeviceJoinRequest, db: AsyncSession = Depends(get_db)):
    """Join a family with just an invite code (for tablet/frame devices)."""
    family = await get_family_by_invite_code(db, req.invite_code)
    if not family:
        raise HTTPException(status_code=404, detail="邀请码无效")

    # Create a device user (no email/password needed)
    device_email = f"device-{family.invite_code}-{generate_invite_code(4)}@device.local"
    user = User(
        family_id=family.id,
        email=device_email,
        password_hash="device",
    )
    db.add(user)
    await db.commit()

    token = create_token(user.id, family.id)
    return TokenResponse(
        access_token=token,
        family_uuid=str(family.uuid),
        invite_code=family.invite_code,
    )


@router.post("/device")
async def register_device(
    req: DeviceRegisterRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a device for push notifications."""
    device = Device(
        user_id=user.id,
        device_type=req.device_type,
        device_name=req.device_name,
        push_token=req.push_token,
    )
    db.add(device)
    await db.commit()
    return {"uuid": str(device.uuid), "device_type": device.device_type}
