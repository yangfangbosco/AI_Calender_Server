from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.family import Family
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/info")
async def get_family_info(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's family info."""
    result = await db.execute(select(Family).where(Family.id == user.family_id))
    family = result.scalar_one()
    return {
        "uuid": str(family.uuid),
        "name": family.name,
        "invite_code": family.invite_code,
    }


@router.put("/name")
async def update_family_name(
    name: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update family name."""
    result = await db.execute(select(Family).where(Family.id == user.family_id))
    family = result.scalar_one()
    family.name = name
    await db.commit()
    return {"uuid": str(family.uuid), "name": family.name}
