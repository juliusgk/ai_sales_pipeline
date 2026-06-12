"""CRUD service for deals — one deal per lead."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.deal import Deal
from src.schemas.deal import DealCreate, DealUpdate


async def get_deals(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    stage: str | None = None,
) -> list[Deal]:
    stmt = select(Deal)
    if stage:
        stmt = stmt.where(Deal.stage == stage)
    result = await session.execute(
        stmt.offset(skip).limit(limit).order_by(Deal.created_at.desc())
    )
    return list(result.scalars().all())


async def get_deal(session: AsyncSession, deal_id: uuid.UUID) -> Deal | None:
    return await session.get(Deal, deal_id)


async def get_deal_by_lead(session: AsyncSession, lead_id: uuid.UUID) -> Deal | None:
    result = await session.execute(select(Deal).where(Deal.lead_id == lead_id))
    return result.scalar_one_or_none()


async def create_deal(session: AsyncSession, data: DealCreate) -> Deal:
    deal = Deal(**data.model_dump())
    session.add(deal)
    await session.flush()
    return deal


async def update_deal(
    session: AsyncSession, deal_id: uuid.UUID, data: DealUpdate
) -> Deal | None:
    deal = await session.get(Deal, deal_id)
    if not deal:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(deal, field, value)
    await session.flush()
    return deal


async def delete_deal(session: AsyncSession, deal_id: uuid.UUID) -> bool:
    deal = await session.get(Deal, deal_id)
    if not deal:
        return False
    await session.delete(deal)
    await session.flush()
    return True
