from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event
from app.models.list import ListItem, UserList
from app.models.member import FamilyMember
from app.models.reward import Reward, StarTransaction
from app.models.task import SubTask, Task
from app.schemas.sync import (
    EventSync,
    ListItemSync,
    MemberSync,
    RewardSync,
    StarTransactionSync,
    SubTaskSync,
    SyncPullResponse,
    SyncPushRequest,
    TaskSync,
    UserListSync,
)


# ── Helper: resolve member uuid → id within a family ──


async def _member_uuid_map(db: AsyncSession, family_id: int) -> dict[str, int]:
    """Return {member_uuid_str: member_id} for a family."""
    result = await db.execute(
        select(FamilyMember).where(FamilyMember.family_id == family_id)
    )
    return {str(m.uuid): m.id for m in result.scalars()}


async def _resolve_member_id(
    member_uuid: str | None, uuid_map: dict[str, int]
) -> int | None:
    if member_uuid is None:
        return None
    return uuid_map.get(member_uuid)


# ── Push: client → server ──


async def push_changes(
    db: AsyncSession, family_id: int, data: SyncPushRequest
) -> None:
    member_map = await _member_uuid_map(db, family_id)

    # Members
    for m in data.members:
        existing = await _get_by_uuid(db, FamilyMember, m.uuid)
        if existing:
            if m.updated_at > existing.updated_at:
                _update_fields(existing, m, ["name", "avatar_key", "sort_order",
                    "star_balance", "total_earned", "total_spent", "is_deleted"])
                existing.updated_at = m.updated_at
        else:
            obj = FamilyMember(
                uuid=m.uuid, family_id=family_id,
                name=m.name, avatar_key=m.avatar_key, sort_order=m.sort_order,
                star_balance=m.star_balance, total_earned=m.total_earned,
                total_spent=m.total_spent, is_deleted=m.is_deleted,
                updated_at=m.updated_at,
            )
            db.add(obj)
            await db.flush()
            member_map[m.uuid] = obj.id

    # Events
    for e in data.events:
        existing = await _get_by_uuid(db, Event, e.uuid)
        mid = await _resolve_member_id(e.member_uuid, member_map)
        if existing:
            if e.updated_at > existing.updated_at:
                _update_fields(existing, e, ["title", "description", "location",
                    "color", "date", "start_time", "end_time", "is_all_day",
                    "is_ai_suggestion", "is_deleted"])
                existing.member_id = mid
                existing.updated_at = e.updated_at
        else:
            db.add(Event(
                uuid=e.uuid, family_id=family_id, member_id=mid,
                title=e.title, description=e.description, location=e.location,
                color=e.color, date=e.date, start_time=e.start_time,
                end_time=e.end_time, is_all_day=e.is_all_day,
                is_ai_suggestion=e.is_ai_suggestion, is_deleted=e.is_deleted,
                updated_at=e.updated_at,
            ))

    # Tasks + SubTasks
    for t in data.tasks:
        existing = await _get_by_uuid(db, Task, t.uuid)
        mid = await _resolve_member_id(t.member_uuid, member_map)
        if existing:
            if t.updated_at > existing.updated_at:
                _update_fields(existing, t, ["title", "priority", "is_done",
                    "date", "start_time", "end_time", "is_all_day", "recurrence",
                    "reward_points", "requires_approval", "approval_status", "is_deleted"])
                existing.member_id = mid
                existing.updated_at = t.updated_at
            task_id = existing.id
        else:
            obj = Task(
                uuid=t.uuid, family_id=family_id, member_id=mid,
                title=t.title, priority=t.priority, is_done=t.is_done,
                date=t.date, start_time=t.start_time, end_time=t.end_time,
                is_all_day=t.is_all_day, recurrence=t.recurrence,
                reward_points=t.reward_points, requires_approval=t.requires_approval,
                approval_status=t.approval_status, is_deleted=t.is_deleted,
                updated_at=t.updated_at,
            )
            db.add(obj)
            await db.flush()
            task_id = obj.id

        for st in t.subtasks:
            ex_st = await _get_by_uuid(db, SubTask, st.uuid)
            st_mid = await _resolve_member_id(st.member_uuid, member_map)
            if ex_st:
                if st.updated_at > ex_st.updated_at:
                    _update_fields(ex_st, st, ["text", "is_done", "is_deleted"])
                    ex_st.member_id = st_mid
                    ex_st.updated_at = st.updated_at
            else:
                db.add(SubTask(
                    uuid=st.uuid, task_id=task_id,
                    task_uuid=t.uuid, member_id=st_mid,
                    text=st.text, is_done=st.is_done,
                    is_deleted=st.is_deleted, updated_at=st.updated_at,
                ))

    # Lists + ListItems
    for l in data.lists:
        existing = await _get_by_uuid(db, UserList, l.uuid)
        if existing:
            if l.updated_at > existing.updated_at:
                _update_fields(existing, l, ["name", "icon", "sort_order", "is_deleted"])
                existing.updated_at = l.updated_at
            list_id = existing.id
        else:
            obj = UserList(
                uuid=l.uuid, family_id=family_id,
                name=l.name, icon=l.icon, sort_order=l.sort_order,
                is_deleted=l.is_deleted, updated_at=l.updated_at,
            )
            db.add(obj)
            await db.flush()
            list_id = obj.id

        for item in l.items:
            ex_item = await _get_by_uuid(db, ListItem, item.uuid)
            if ex_item:
                if item.updated_at > ex_item.updated_at:
                    _update_fields(ex_item, item, ["text", "is_done", "section", "is_deleted"])
                    ex_item.updated_at = item.updated_at
            else:
                db.add(ListItem(
                    uuid=item.uuid, list_id=list_id,
                    list_uuid=l.uuid, text=item.text,
                    is_done=item.is_done, section=item.section,
                    is_deleted=item.is_deleted, updated_at=item.updated_at,
                ))

    # Rewards
    for r in data.rewards:
        existing = await _get_by_uuid(db, Reward, r.uuid)
        mid = await _resolve_member_id(r.member_uuid, member_map)
        if existing:
            if r.updated_at > existing.updated_at:
                _update_fields(existing, r, ["title", "star_cost", "icon",
                    "sort_order", "is_deleted"])
                existing.member_id = mid
                existing.updated_at = r.updated_at
        else:
            db.add(Reward(
                uuid=r.uuid, family_id=family_id, member_id=mid,
                title=r.title, star_cost=r.star_cost, icon=r.icon,
                sort_order=r.sort_order, is_deleted=r.is_deleted,
                updated_at=r.updated_at,
            ))

    # StarTransactions
    for tx in data.star_transactions:
        existing = await _get_by_uuid(db, StarTransaction, tx.uuid)
        mid = member_map.get(tx.member_uuid)
        if not existing and mid:
            db.add(StarTransaction(
                uuid=tx.uuid, family_id=family_id, member_id=mid,
                amount=tx.amount, type=tx.type, description=tx.description,
                timestamp=tx.timestamp, task_uuid=tx.task_uuid,
                reward_uuid=tx.reward_uuid, is_deleted=tx.is_deleted,
                updated_at=tx.updated_at,
            ))

    await db.commit()


# ── Pull: server → client ──


async def pull_changes(
    db: AsyncSession, family_id: int, since: datetime | None
) -> SyncPullResponse:
    now = datetime.now(timezone.utc)

    def _since_filter(model):
        base = select(model).where(model.family_id == family_id)
        if since:
            base = base.where(model.updated_at > since)
        return base

    # Members
    result = await db.execute(_since_filter(FamilyMember))
    members = [MemberSync(
        uuid=str(m.uuid), name=m.name, avatar_key=m.avatar_key,
        sort_order=m.sort_order, star_balance=m.star_balance,
        total_earned=m.total_earned, total_spent=m.total_spent,
        is_deleted=m.is_deleted, updated_at=m.updated_at,
    ) for m in result.scalars()]

    # Build reverse map: member_id → uuid
    all_members = await db.execute(
        select(FamilyMember).where(FamilyMember.family_id == family_id)
    )
    id_to_uuid = {m.id: str(m.uuid) for m in all_members.scalars()}

    # Events
    result = await db.execute(_since_filter(Event))
    events = [EventSync(
        uuid=str(e.uuid), member_uuid=id_to_uuid.get(e.member_id),
        title=e.title, description=e.description, location=e.location,
        color=e.color, date=e.date, start_time=e.start_time,
        end_time=e.end_time, is_all_day=e.is_all_day,
        is_ai_suggestion=e.is_ai_suggestion, is_deleted=e.is_deleted,
        updated_at=e.updated_at,
    ) for e in result.scalars()]

    # Tasks with subtasks
    stmt = _since_filter(Task).options(selectinload(Task.subtasks))
    result = await db.execute(stmt)
    tasks = []
    for t in result.scalars():
        subtasks = [SubTaskSync(
            uuid=str(st.uuid), task_uuid=str(t.uuid),
            member_uuid=id_to_uuid.get(st.member_id),
            text=st.text, is_done=st.is_done,
            is_deleted=st.is_deleted, updated_at=st.updated_at,
        ) for st in t.subtasks]
        tasks.append(TaskSync(
            uuid=str(t.uuid), member_uuid=id_to_uuid.get(t.member_id),
            title=t.title, priority=t.priority, is_done=t.is_done,
            date=t.date, start_time=t.start_time, end_time=t.end_time,
            is_all_day=t.is_all_day, recurrence=t.recurrence,
            reward_points=t.reward_points, requires_approval=t.requires_approval,
            approval_status=t.approval_status, subtasks=subtasks,
            is_deleted=t.is_deleted, updated_at=t.updated_at,
        ))

    # Lists with items
    stmt = _since_filter(UserList).options(selectinload(UserList.items))
    result = await db.execute(stmt)
    lists = []
    for l in result.scalars():
        items = [ListItemSync(
            uuid=str(i.uuid), list_uuid=str(l.uuid),
            text=i.text, is_done=i.is_done, section=i.section,
            is_deleted=i.is_deleted, updated_at=i.updated_at,
        ) for i in l.items]
        lists.append(UserListSync(
            uuid=str(l.uuid), name=l.name, icon=l.icon,
            sort_order=l.sort_order, items=items,
            is_deleted=l.is_deleted, updated_at=l.updated_at,
        ))

    # Rewards
    result = await db.execute(_since_filter(Reward))
    rewards = [RewardSync(
        uuid=str(r.uuid), member_uuid=id_to_uuid.get(r.member_id),
        title=r.title, star_cost=r.star_cost, icon=r.icon,
        sort_order=r.sort_order, is_deleted=r.is_deleted,
        updated_at=r.updated_at,
    ) for r in result.scalars()]

    # StarTransactions
    result = await db.execute(_since_filter(StarTransaction))
    transactions = [StarTransactionSync(
        uuid=str(tx.uuid), member_uuid=id_to_uuid.get(tx.member_id, ""),
        amount=tx.amount, type=tx.type, description=tx.description,
        timestamp=tx.timestamp, task_uuid=tx.task_uuid,
        reward_uuid=tx.reward_uuid, is_deleted=tx.is_deleted,
        updated_at=tx.updated_at,
    ) for tx in result.scalars()]

    return SyncPullResponse(
        members=members, events=events, tasks=tasks,
        lists=lists, rewards=rewards, star_transactions=transactions,
        server_time=now,
    )


# ── Utilities ──


async def _get_by_uuid(db: AsyncSession, model, uuid_str: str):
    result = await db.execute(
        select(model).where(model.uuid == uuid_str)
    )
    return result.scalar_one_or_none()


def _update_fields(obj, data, fields: list[str]):
    for f in fields:
        if hasattr(data, f):
            setattr(obj, f, getattr(data, f))
