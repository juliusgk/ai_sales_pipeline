"""Contact model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, UUIDType


class Contact(Base):
    __tablename__ = "contacts"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType(), ForeignKey("companies.id", ondelete="SET NULL")
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    job_title: Mapped[str | None] = mapped_column(String(200))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    company: Mapped["Company | None"] = relationship(  # noqa: F821
        back_populates="contacts"
    )
    interactions: Mapped[list["Interaction"]] = relationship(  # noqa: F821
        back_populates="contact", lazy="selectin"
    )

    __table_args__ = (Index("ix_contacts_email", "email"),)
