from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.family import Family
from app.models.member import FamilyMember
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/info")
async def get_family_info(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's family info including members and roles."""
    result = await db.execute(select(Family).where(Family.id == user.family_id))
    family = result.scalar_one()

    # Get all users in this family (with their member info)
    users_result = await db.execute(
        select(User).where(User.family_id == family.id)
    )
    users = users_result.scalars().all()

    members = []
    for u in users:
        if u.member_id:
            m_result = await db.execute(
                select(FamilyMember).where(FamilyMember.id == u.member_id)
            )
            m = m_result.scalar_one_or_none()
            if m:
                members.append({
                    "user_id": u.id,
                    "member_uuid": str(m.uuid),
                    "name": m.name,
                    "avatar_key": m.avatar_key,
                    "is_admin": u.is_admin,
                    "is_current_user": u.id == user.id,
                })

    return {
        "uuid": str(family.uuid),
        "name": family.name,
        "invite_code": family.invite_code,
        "members": members,
        "current_user_is_admin": user.is_admin,
    }


@router.put("/name")
async def update_family_name(
    name: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update family name. Admin only."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可修改")
    result = await db.execute(select(Family).where(Family.id == user.family_id))
    family = result.scalar_one()
    family.name = name
    await db.commit()
    return {"uuid": str(family.uuid), "name": family.name}


@router.post("/promote-admin")
async def promote_admin(
    target_user_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Promote a family member to admin. Admin only."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    result = await db.execute(
        select(User).where(User.id == target_user_id, User.family_id == user.family_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    target.is_admin = True
    await db.commit()
    return {"status": "ok"}


@router.post("/demote-admin")
async def demote_admin(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Current user gives up admin role. Must have at least 1 admin remaining."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="你不是管理员")

    # Count admins
    result = await db.execute(
        select(func.count()).select_from(User).where(
            User.family_id == user.family_id, User.is_admin == True
        )
    )
    admin_count = result.scalar()

    if admin_count <= 1:
        raise HTTPException(status_code=400, detail="家庭至少需要一个管理员")

    user.is_admin = False
    await db.commit()
    return {"status": "ok"}
