from datetime import datetime

from pydantic import BaseModel


# ── Shared sync item schemas ──


class MemberSync(BaseModel):
    uuid: str
    name: str
    avatar_key: str
    sort_order: int = 0
    star_balance: int = 0
    total_earned: int = 0
    total_spent: int = 0
    is_deleted: bool = False
    updated_at: datetime


class EventSync(BaseModel):
    uuid: str
    member_uuid: str | None = None
    title: str
    description: str | None = None
    location: str | None = None
    color: str
    date: str
    start_time: str
    end_time: str
    is_all_day: bool = False
    is_ai_suggestion: bool = False
    is_deleted: bool = False
    updated_at: datetime


class SubTaskSync(BaseModel):
    uuid: str
    task_uuid: str
    member_uuid: str | None = None
    text: str
    is_done: bool = False
    is_deleted: bool = False
    updated_at: datetime


class TaskSync(BaseModel):
    uuid: str
    member_uuid: str | None = None
    title: str
    priority: str
    is_done: bool = False
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    is_all_day: bool = False
    recurrence: str = "NONE"
    reward_points: int = 0
    requires_approval: bool = False
    approval_status: str = "NONE"
    subtasks: list[SubTaskSync] = []
    is_deleted: bool = False
    updated_at: datetime


class ListItemSync(BaseModel):
    uuid: str
    list_uuid: str
    text: str
    is_done: bool = False
    section: str | None = None
    is_deleted: bool = False
    updated_at: datetime


class UserListSync(BaseModel):
    uuid: str
    name: str
    icon: str = "list"
    sort_order: int = 0
    items: list[ListItemSync] = []
    is_deleted: bool = False
    updated_at: datetime


class RewardSync(BaseModel):
    uuid: str
    member_uuid: str | None = None
    title: str
    star_cost: int
    icon: str = "star"
    sort_order: int = 0
    is_deleted: bool = False
    updated_at: datetime


class StarTransactionSync(BaseModel):
    uuid: str
    member_uuid: str
    amount: int
    type: str
    description: str
    timestamp: int
    task_uuid: str | None = None
    reward_uuid: str | None = None
    is_deleted: bool = False
    updated_at: datetime


# ── Push / Pull payloads ──


class SyncPushRequest(BaseModel):
    """Client sends changed data to server."""

    members: list[MemberSync] = []
    events: list[EventSync] = []
    tasks: list[TaskSync] = []
    lists: list[UserListSync] = []
    rewards: list[RewardSync] = []
    star_transactions: list[StarTransactionSync] = []


class SyncPullRequest(BaseModel):
    """Client asks for changes since last sync."""

    last_sync_at: datetime | None = None


class SyncPullResponse(BaseModel):
    """Server returns data changed since last_sync_at."""

    members: list[MemberSync] = []
    events: list[EventSync] = []
    tasks: list[TaskSync] = []
    lists: list[UserListSync] = []
    rewards: list[RewardSync] = []
    star_transactions: list[StarTransactionSync] = []
    server_time: datetime
