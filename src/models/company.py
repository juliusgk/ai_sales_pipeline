"""Company model."""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Company(Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(100))
    size_range: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    contacts: Mapped[list["Contact"]] = relationship(  # noqa: F821
        back_populates="company", lazy="selectin"
    )
    leads: Mapped[list["Lead"]] = relationship(  # noqa: F821
        back_populates="company", lazy="selectin"
    )

    __table_args__ = (Index("ix_companies_name", "name"),)
