"""Lead model — the central entity of the pipeline."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, UUIDType
from src.models.tag import lead_tags


class Lead(Base):
    __tablename__ = "leads"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("companies.id", ondelete="SET NULL")
    )
    primary_contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("contacts.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="new", nullable=False
    )  # new, in_progress, on_hold, client, no_deal
    source: Mapped[str | None] = mapped_column(
        String(100)
    )  # linkedin, gmail, referral, cold_outreach, website, other
    priority: Mapped[int] = mapped_column(SmallInteger, default=3)  # 1-5
    estimated_value: Mapped[float | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    notes: Mapped[str | None] = mapped_column(Text)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    company: Mapped["Company | None"] = relationship(  # noqa: F821
        back_populates="leads"
    )
    primary_contact: Mapped["Contact | None"] = relationship(lazy="selectin")  # noqa: F821
    interactions: Mapped[list["Interaction"]] = relationship(  # noqa: F821
        back_populates="lead", lazy="selectin"
    )
    deal: Mapped["Deal | None"] = relationship(  # noqa: F821
        back_populates="lead", uselist=False, lazy="selectin"
    )
    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        secondary=lead_tags, back_populates="leads", lazy="selectin"
    )

    __table_args__ = (Index("ix_leads_status", "status"),)
