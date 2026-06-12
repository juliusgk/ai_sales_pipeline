"""Helper to silently attempt embedding — Ollama may not be running during dev."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def try_embed(
    session: AsyncSession,
    source_type: str,
    source_id: uuid.UUID,
    record=None,
) -> None:
    """Attempt to embed a record. Logs and swallows errors if Ollama is unavailable."""
    try:
        from src.services.rag_service import embed_record

        await embed_record(session, source_type, source_id, record)
    except Exception as e:
        logger.warning(
            f"Auto-embed skipped for {source_type}/{source_id}: {e}. "
            "This is expected if Ollama is not running."
        )
