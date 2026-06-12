"""Interaction model — logs every touchpoint with a lead."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Interaction(Base):
    __tablename__ = "interactions"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL")
    )
    type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # email_sent, email_received, call, meeting, linkedin_message, etc.
    direction: Mapped[str | None] = mapped_column(String(10))  # inbound / outbound
    subject: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    source: Mapped[str | None] = mapped_column(String(50))  # manual, gmail_sync, linkedin_sync
    external_id: Mapped[str | None] = mapped_column(
        String(255)
    )  # for deduplication (Gmail/LinkedIn message ID)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)

    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="interactions")  # noqa: F821
    contact: Mapped["Contact | None"] = relationship(  # noqa: F821
        back_populates="interactions"
    )

    __table_args__ = (Index("ix_interactions_lead_id", "lead_id"),)
