"""Embedding model for RAG — stores pgvector embeddings of pipeline data."""

import uuid

from sqlalchemy import Index, LargeBinary, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.config import settings
from src.models.base import Base, UUIDType

# Use pgvector Vector type when available (PostgreSQL), fall back to LargeBinary (SQLite/testing)
try:
    from pgvector.sqlalchemy import Vector

    _embedding_type = Vector(settings.embedding_dimension)
except ImportError:
    _embedding_type = LargeBinary  # type: ignore[assignment]


class Embedding(Base):
    __tablename__ = "embeddings"

    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # lead, interaction, contact, company
    source_id: Mapped[uuid.UUID] = mapped_column(UUIDType(), nullable=False)
    chunk_index: Mapped[int] = mapped_column(SmallInteger, default=0)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[bytes | list[float]] = mapped_column(
        _embedding_type, nullable=False
    )

    __table_args__ = (
        Index(
            "ix_embeddings_source",
            "source_type",
            "source_id",
        ),
    )
