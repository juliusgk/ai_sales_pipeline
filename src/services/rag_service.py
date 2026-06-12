"""RAG service — embedding, retrieval, and LLM query orchestration.

This is the core intelligence layer:
1. Converts pipeline records into natural language text
2. Chunks long content (emails, notes)
3. Embeds text via Ollama (nomic-embed-text)
4. Stores embeddings in pgvector
5. Retrieves relevant context for user questions
6. Queries Llama 3 via Ollama with the context
"""

import uuid
import logging

import httpx
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.company import Company
from src.models.contact import Contact
from src.models.embedding import Embedding
from src.models.interaction import Interaction
from src.models.lead import Lead

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Text templating — convert DB records into natural language for embedding
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an AI sales pipeline assistant. Answer questions about leads, contacts, "
    "interactions, and deals using ONLY the provided context. Be concise and specific. "
    "Include relevant names, dates, and statuses. If the context does not contain enough "
    "information to answer, say so clearly — do not make up information."
)


def _lead_to_text(lead: Lead) -> str:
    """Convert a lead record to a natural language description."""
    parts = [f"Lead: {lead.title}."]
    if lead.company:
        parts.append(f"Company: {lead.company.name}.")
    if lead.primary_contact:
        c = lead.primary_contact
        contact_str = f"{c.first_name} {c.last_name}"
        if c.job_title:
            contact_str += f", {c.job_title}"
        parts.append(f"Primary contact: {contact_str}.")
    parts.append(f"Status: {lead.status}.")
    parts.append(f"Priority: {lead.priority}/5.")
    if lead.source:
        parts.append(f"Source: {lead.source}.")
    if lead.estimated_value:
        parts.append(f"Estimated value: {lead.currency} {lead.estimated_value:,.2f}.")
    if lead.notes:
        parts.append(f"Notes: {lead.notes}")
    if lead.tags:
        tag_names = ", ".join(t.name for t in lead.tags)
        parts.append(f"Tags: {tag_names}.")
    return " ".join(parts)


def _interaction_to_text(interaction: Interaction) -> str:
    """Convert an interaction record to natural language."""
    date_str = interaction.occurred_at.strftime("%Y-%m-%d %H:%M")
    parts = [f"On {date_str}, {interaction.type}"]
    if interaction.direction:
        parts[0] += f" ({interaction.direction})"
    if interaction.contact:
        c = interaction.contact
        parts.append(f"with {c.first_name} {c.last_name}")
    if interaction.lead:
        parts.append(f"regarding lead '{interaction.lead.title}'")
    parts.append(".")
    if interaction.subject:
        parts.append(f"Subject: {interaction.subject}.")
    if interaction.body:
        parts.append(interaction.body)
    return " ".join(parts)


def _company_to_text(company: Company) -> str:
    """Convert a company record to natural language."""
    parts = [f"Company: {company.name}."]
    if company.industry:
        parts.append(f"Industry: {company.industry}.")
    if company.size_range:
        parts.append(f"Size: {company.size_range} employees.")
    if company.domain:
        parts.append(f"Website: {company.domain}.")
    if company.notes:
        parts.append(f"Notes: {company.notes}")
    return " ".join(parts)


def _contact_to_text(contact: Contact) -> str:
    """Convert a contact record to natural language."""
    parts = [f"Contact: {contact.first_name} {contact.last_name}."]
    if contact.job_title:
        parts.append(f"Title: {contact.job_title}.")
    if contact.email:
        parts.append(f"Email: {contact.email}.")
    if contact.company:
        parts.append(f"Company: {contact.company.name}.")
    if contact.notes:
        parts.append(f"Notes: {contact.notes}")
    return " ".join(parts)


def _record_to_text(source_type: str, record) -> str:
    """Dispatch to the appropriate text template."""
    converters = {
        "lead": _lead_to_text,
        "interaction": _interaction_to_text,
        "company": _company_to_text,
        "contact": _contact_to_text,
    }
    converter = converters.get(source_type)
    if not converter:
        raise ValueError(f"Unknown source_type: {source_type}")
    return converter(record)


# ---------------------------------------------------------------------------
# Chunking — split long text into manageable pieces
# ---------------------------------------------------------------------------


def _chunk_text(text_content: str, max_tokens: int = 500, overlap: int = 50) -> list[str]:
    """Simple sentence-based chunking.

    Splits on sentence boundaries ('. ') and groups into chunks
    of approximately max_tokens words with overlap.
    """
    # Simple word-based approximation (1 token ≈ 0.75 words for English)
    max_words = int(max_tokens * 0.75)
    overlap_words = int(overlap * 0.75)

    words = text_content.split()

    if len(words) <= max_words:
        return [text_content]

    chunks = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap_words

    return chunks


# ---------------------------------------------------------------------------
# Embedding — call Ollama to generate vector embeddings
# ---------------------------------------------------------------------------


async def _get_embedding(text_content: str) -> list[float]:
    """Call Ollama embedding endpoint to get a vector."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/embeddings",
            json={
                "model": settings.ollama_embed_model,
                "prompt": text_content,
            },
        )
        response.raise_for_status()
        return response.json()["embedding"]


# ---------------------------------------------------------------------------
# Embed a record — the main entry point for auto-embedding
# ---------------------------------------------------------------------------


async def embed_record(
    session: AsyncSession,
    source_type: str,
    source_id: uuid.UUID,
    record=None,
) -> int:
    """Embed (or re-embed) a pipeline record into pgvector.

    1. Delete any existing embeddings for this record
    2. Generate text from the record
    3. Chunk if needed
    4. Embed each chunk
    5. Store in the embeddings table

    Returns the number of embedding chunks created.
    """
    # Delete old embeddings for this record
    await session.execute(
        delete(Embedding).where(
            Embedding.source_type == source_type,
            Embedding.source_id == source_id,
        )
    )

    # Fetch the record if not provided
    if record is None:
        model_map = {
            "lead": Lead,
            "interaction": Interaction,
            "company": Company,
            "contact": Contact,
        }
        model_class = model_map.get(source_type)
        if not model_class:
            raise ValueError(f"Unknown source_type: {source_type}")
        record = await session.get(model_class, source_id)
        if not record:
            logger.warning(f"Record not found: {source_type}/{source_id}")
            return 0

    # Generate text
    try:
        full_text = _record_to_text(source_type, record)
    except Exception as e:
        logger.error(f"Failed to convert record to text: {e}")
        return 0

    # Chunk
    chunks = _chunk_text(full_text)

    # Embed and store each chunk
    count = 0
    for i, chunk_text in enumerate(chunks):
        try:
            embedding_vector = await _get_embedding(chunk_text)
        except Exception as e:
            logger.error(f"Failed to embed chunk {i} for {source_type}/{source_id}: {e}")
            continue

        embedding = Embedding(
            source_type=source_type,
            source_id=source_id,
            chunk_index=i,
            content_text=chunk_text,
            embedding=embedding_vector,
        )
        session.add(embedding)
        count += 1

    await session.flush()
    logger.info(f"Embedded {count} chunks for {source_type}/{source_id}")
    return count


# ---------------------------------------------------------------------------
# Retrieval — find relevant context for a question
# ---------------------------------------------------------------------------


async def retrieve_context(
    session: AsyncSession,
    question: str,
    top_k: int = 10,
) -> list[dict]:
    """Embed the question and find the top-K most relevant chunks.

    Returns a list of dicts with keys: content_text, source_type, source_id, score.
    """
    question_embedding = await _get_embedding(question)

    # pgvector cosine distance query (lower distance = more similar)
    result = await session.execute(
        text("""
            SELECT
                content_text,
                source_type,
                source_id::text,
                1 - (embedding <=> :query_embedding::vector) AS score
            FROM embeddings
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :top_k
        """),
        {
            "query_embedding": str(question_embedding),
            "top_k": top_k,
        },
    )

    rows = result.fetchall()
    return [
        {
            "content_text": row[0],
            "source_type": row[1],
            "source_id": row[2],
            "score": float(row[3]),
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Query — ask the LLM with retrieved context
# ---------------------------------------------------------------------------


async def query(
    session: AsyncSession,
    question: str,
    top_k: int = 10,
) -> dict:
    """Full RAG query: retrieve context, build prompt, query Llama 3.

    Returns dict with 'answer' and 'sources'.
    """
    # 1. Retrieve relevant context
    context_chunks = await retrieve_context(session, question, top_k=top_k)

    if not context_chunks:
        return {
            "answer": "I don't have any data in the pipeline yet to answer that question. "
            "Try adding some leads, contacts, or interactions first.",
            "sources": [],
        }

    # 2. Build the context string
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        context_parts.append(f"[{i}] ({chunk['source_type']}) {chunk['content_text']}")
    context_str = "\n\n".join(context_parts)

    # 3. Build the prompt
    user_prompt = (
        f"Context from the sales pipeline:\n\n{context_str}\n\n"
        f"Question: {question}\n\n"
        "Answer based on the context above:"
    )

    # 4. Query Ollama (Llama 3)
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_llm_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            },
        )
        response.raise_for_status()
        answer = response.json()["message"]["content"]

    # 5. Build sources list (deduplicated)
    seen = set()
    sources = []
    for chunk in context_chunks:
        key = f"{chunk['source_type']}/{chunk['source_id']}"
        if key not in seen:
            seen.add(key)
            sources.append(
                {
                    "source_type": chunk["source_type"],
                    "source_id": chunk["source_id"],
                    "score": chunk["score"],
                }
            )

    return {"answer": answer, "sources": sources}
