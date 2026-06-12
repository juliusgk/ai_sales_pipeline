"""Re-embed all records in the database.

Run this after seeding data or if you change the embedding model.

Usage:
    python -m scripts.embed_all

Requires: DATABASE_URL set, PostgreSQL + Ollama running with models pulled.
"""

import asyncio
import logging

from sqlalchemy import func, select

from src.database import async_session_factory
from src.models.company import Company
from src.models.contact import Contact
from src.models.interaction import Interaction
from src.models.lead import Lead
from src.services.rag_service import embed_record

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models to embed with their source_type labels
MODELS = [
    ("company", Company),
    ("contact", Contact),
    ("lead", Lead),
    ("interaction", Interaction),
]


async def embed_all():
    async with async_session_factory() as session:
        total_chunks = 0

        for source_type, model_class in MODELS:
            # Count records
            count_result = await session.execute(
                select(func.count()).select_from(model_class)
            )
            count = count_result.scalar() or 0
            logger.info(f"Embedding {count} {source_type} records...")

            # Fetch all records
            result = await session.execute(select(model_class))
            records = result.scalars().all()

            for record in records:
                try:
                    chunks = await embed_record(session, source_type, record.id, record)
                    total_chunks += chunks
                except Exception as e:
                    logger.error(f"Failed to embed {source_type}/{record.id}: {e}")

        await session.commit()
        logger.info(f"Done! Embedded {total_chunks} total chunks across all records.")


if __name__ == "__main__":
    asyncio.run(embed_all())
