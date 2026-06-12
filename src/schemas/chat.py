"""Pydantic schemas for RAG chat endpoint."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    top_k: int = 10


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []
