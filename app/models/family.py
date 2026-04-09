import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Family(Base):
    __tablename__ = "families"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # relationships
    users = relationship("User", back_populates="family")
    members = relationship("FamilyMember", back_populates="family")
    events = relationship("Event", back_populates="family")
    tasks = relationship("Task", back_populates="family")
    lists = relationship("UserList", back_populates="family")
    rewards = relationship("Reward", back_populates="family")
