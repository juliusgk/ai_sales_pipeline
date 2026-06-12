"""RAG chat endpoint — query the SLM about your sales pipeline."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas.chat import ChatRequest, ChatResponse
from src.services import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    """Ask a natural language question about your sales pipeline.

    The question is embedded, relevant context is retrieved from the database
    via pgvector similarity search, and Llama 3 generates an answer.
    """
    try:
        result = await rag_service.query(
            session,
            question=request.question,
            top_k=request.top_k,
        )
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
        )
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=(
                "Failed to query the AI assistant. "
                "Ensure Ollama is running and models are pulled. "
                f"Error: {str(e)}"
            ),
        )
