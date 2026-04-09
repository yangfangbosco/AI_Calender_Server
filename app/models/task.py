from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin


class Task(SyncMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    member_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    priority: Mapped[str] = mapped_column(String(10))  # HIGH, MEDIUM, LOW
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    start_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    end_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence: Mapped[str] = mapped_column(String(10), default="NONE")
    reward_points: Mapped[int] = mapped_column(Integer, default=0)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_status: Mapped[str] = mapped_column(String(10), default="NONE")

    family = relationship("Family", back_populates="tasks")
    member = relationship("FamilyMember")
    subtasks = relationship("SubTask", back_populates="task", cascade="all, delete-orphan")


class SubTask(SyncMixin, Base):
    __tablename__ = "subtasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    task_uuid: Mapped[str] = mapped_column(String(36), index=True)
    member_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id"), nullable=True
    )
    text: Mapped[str] = mapped_column(String(500))
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)

    task = relationship("Task", back_populates="subtasks")
    member = relationship("FamilyMember")
