from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.sync import SyncPullRequest, SyncPullResponse, SyncPushRequest
from app.services.sync import pull_changes, push_changes
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/push")
async def sync_push(
    data: SyncPushRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Client pushes local changes to server."""
    await push_changes(db, user.family_id, data)
    return {"status": "ok"}


@router.post("/pull", response_model=SyncPullResponse)
async def sync_pull(
    req: SyncPullRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Client pulls changes from server since last sync."""
    return await pull_changes(db, user.family_id, req.last_sync_at)
