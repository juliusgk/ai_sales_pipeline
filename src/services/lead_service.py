"""CRUD service for leads — the central pipeline entity."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.lead import Lead
from src.models.tag import Tag
from src.schemas.lead import LeadCreate, LeadStatus, LeadUpdate
from src.services._embed_helper import try_embed

logger = logging.getLogger(__name__)


async def get_leads(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: LeadStatus | None = None,
    source: str | None = None,
) -> list[Lead]:
    stmt = select(Lead).options(
        selectinload(Lead.company),
        selectinload(Lead.primary_contact),
        selectinload(Lead.tags),
        selectinload(Lead.deal),
    )
    if status:
        stmt = stmt.where(Lead.status == status.value)
    if source:
        stmt = stmt.where(Lead.source == source)
    result = await session.execute(
        stmt.offset(skip).limit(limit).order_by(Lead.created_at.desc())
    )
    return list(result.scalars().unique().all())


async def get_lead(session: AsyncSession, lead_id: uuid.UUID) -> Lead | None:
    stmt = (
        select(Lead)
        .options(
            selectinload(Lead.company),
            selectinload(Lead.primary_contact),
            selectinload(Lead.tags),
            selectinload(Lead.deal),
            selectinload(Lead.interactions),
        )
        .where(Lead.id == lead_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_lead(session: AsyncSession, data: LeadCreate) -> Lead:
    lead_data = data.model_dump(exclude={"tag_ids"})
    lead = Lead(**lead_data)

    # Attach tags if provided
    if data.tag_ids:
        result = await session.execute(select(Tag).where(Tag.id.in_(data.tag_ids)))
        lead.tags = list(result.scalars().all())

    session.add(lead)
    await session.flush()

    # Auto-embed for RAG
    await try_embed(session, "lead", lead.id, lead)

    # Re-fetch with relationships loaded
    return await get_lead(session, lead.id)  # type: ignore[return-value]


async def update_lead(
    session: AsyncSession, lead_id: uuid.UUID, data: LeadUpdate
) -> Lead | None:
    lead = await get_lead(session, lead_id)
    if not lead:
        return None

    update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
    for field, value in update_data.items():
        setattr(lead, field, value)

    # Update tags if provided
    if data.tag_ids is not None:
        result = await session.execute(select(Tag).where(Tag.id.in_(data.tag_ids)))
        lead.tags = list(result.scalars().all())

    await session.flush()

    # Re-embed for RAG
    refreshed = await get_lead(session, lead_id)
    if refreshed:
        await try_embed(session, "lead", lead_id, refreshed)

    return refreshed


async def delete_lead(session: AsyncSession, lead_id: uuid.UUID) -> bool:
    lead = await session.get(Lead, lead_id)
    if not lead:
        return False
    await session.delete(lead)
    await session.flush()
    return True
