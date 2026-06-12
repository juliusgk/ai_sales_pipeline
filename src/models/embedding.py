"""Embedding model for RAG — stores pgvector embeddings of pipeline data."""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.config import settings
from src.models.base import Base


class Embedding(Base):
    __tablename__ = "embeddings"

    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # lead, interaction, contact, company
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    chunk_index: Mapped[int] = mapped_column(SmallInteger, default=0)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.embedding_dimension), nullable=False
    )

    __table_args__ = (
        Index(
            "ix_embeddings_source",
            "source_type",
            "source_id",
        ),
        # IVFFlat index for cosine similarity search
        # Note: this index requires data to exist before creation in production.
        # For initial setup, the HNSW index below is preferred as it works on empty tables.
        Index(
            "ix_embeddings_vector",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
