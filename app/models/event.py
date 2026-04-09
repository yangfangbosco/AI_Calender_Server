from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin


class Event(SyncMixin, Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    member_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    color: Mapped[str] = mapped_column(String(20))
    date: Mapped[str] = mapped_column(String(10))  # yyyy-MM-dd
    start_time: Mapped[str] = mapped_column(String(5))  # HH:mm
    end_time: Mapped[str] = mapped_column(String(5))  # HH:mm
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    is_ai_suggestion: Mapped[bool] = mapped_column(Boolean, default=False)

    family = relationship("Family", back_populates="events")
    member = relationship("FamilyMember")
