import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    device_type: Mapped[str] = mapped_column(String(20))  # "tablet" or "phone"
    device_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    push_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user = relationship("User", back_populates="devices")
