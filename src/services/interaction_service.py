"""CRUD service for interactions — logs every touchpoint with a lead."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.interaction import Interaction
from src.models.lead import Lead
from src.schemas.interaction import InteractionCreate, InteractionUpdate
from src.services._embed_helper import try_embed


async def get_interactions(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    lead_id: uuid.UUID | None = None,
    interaction_type: str | None = None,
) -> list[Interaction]:
    stmt = select(Interaction)
    if lead_id:
        stmt = stmt.where(Interaction.lead_id == lead_id)
    if interaction_type:
        stmt = stmt.where(Interaction.type == interaction_type)
    result = await session.execute(
        stmt.offset(skip).limit(limit).order_by(Interaction.occurred_at.desc())
    )
    return list(result.scalars().all())


async def get_interaction(
    session: AsyncSession, interaction_id: uuid.UUID
) -> Interaction | None:
    return await session.get(Interaction, interaction_id)


async def create_interaction(
    session: AsyncSession, data: InteractionCreate
) -> Interaction:
    interaction_data = data.model_dump()
    # Map metadata_ to the column name
    metadata = interaction_data.pop("metadata_", None)
    interaction = Interaction(**interaction_data, metadata_=metadata)
    session.add(interaction)
    await session.flush()

    # Update lead's last_activity_at (denormalized for fast queries)
    lead = await session.get(Lead, data.lead_id)
    if lead:
        lead.last_activity_at = datetime.now(timezone.utc)
        await session.flush()

    # Auto-embed for RAG
    await try_embed(session, "interaction", interaction.id, interaction)

    return interaction


async def update_interaction(
    session: AsyncSession, interaction_id: uuid.UUID, data: InteractionUpdate
) -> Interaction | None:
    interaction = await session.get(Interaction, interaction_id)
    if not interaction:
        return None
    update_data = data.model_dump(exclude_unset=True)
    metadata = update_data.pop("metadata_", None)
    for field, value in update_data.items():
        setattr(interaction, field, value)
    if metadata is not None:
        interaction.metadata_ = metadata
    await session.flush()
    await try_embed(session, "interaction", interaction.id, interaction)
    return interaction


async def delete_interaction(session: AsyncSession, interaction_id: uuid.UUID) -> bool:
    interaction = await session.get(Interaction, interaction_id)
    if not interaction:
        return False
    await session.delete(interaction)
    await session.flush()
    return True
