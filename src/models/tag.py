"""Tag model and lead_tags junction table."""

import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

# Junction table for many-to-many leads <-> tags
lead_tags = Table(
    "lead_tags",
    Base.metadata,
    Column(
        "lead_id",
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Tag(Base):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(7))  # hex color, e.g. #FF5733

    # Relationship
    leads: Mapped[list["Lead"]] = relationship(  # noqa: F821
        secondary=lead_tags, back_populates="tags", lazy="selectin"
    )
