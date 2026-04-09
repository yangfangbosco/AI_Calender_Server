from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SyncMixin


class Reward(SyncMixin, Base):
    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    member_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    star_cost: Mapped[int] = mapped_column(Integer)
    icon: Mapped[str] = mapped_column(String(50), default="star")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    family = relationship("Family", back_populates="rewards")
    member = relationship("FamilyMember")


class StarTransaction(SyncMixin, Base):
    __tablename__ = "star_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"))
    amount: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(10))  # EARN, SPEND, DEDUCT
    description: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[int] = mapped_column(BigInteger)
    task_uuid: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reward_uuid: Mapped[str | None] = mapped_column(String(36), nullable=True)

    member = relationship("FamilyMember")
