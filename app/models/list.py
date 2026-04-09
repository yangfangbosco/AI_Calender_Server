from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin


class UserList(SyncMixin, Base):
    __tablename__ = "user_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    icon: Mapped[str] = mapped_column(String(50), default="list")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    family = relationship("Family", back_populates="lists")
    items = relationship("ListItem", back_populates="user_list", cascade="all, delete-orphan")


class ListItem(SyncMixin, Base):
    __tablename__ = "list_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(
        ForeignKey("user_lists.id", ondelete="CASCADE")
    )
    list_uuid: Mapped[str] = mapped_column(String(36), index=True)
    text: Mapped[str] = mapped_column(String(500))
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    section: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user_list = relationship("UserList", back_populates="items")
