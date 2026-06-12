"""CRUD service for companies."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.company import Company
from src.schemas.company import CompanyCreate, CompanyUpdate
from src.services._embed_helper import try_embed


async def get_companies(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> list[Company]:
    result = await session.execute(
        select(Company).offset(skip).limit(limit).order_by(Company.created_at.desc())
    )
    return list(result.scalars().all())


async def get_company(session: AsyncSession, company_id: uuid.UUID) -> Company | None:
    return await session.get(Company, company_id)


async def create_company(session: AsyncSession, data: CompanyCreate) -> Company:
    company = Company(**data.model_dump())
    session.add(company)
    await session.flush()
    await try_embed(session, "company", company.id, company)
    return company


async def update_company(
    session: AsyncSession, company_id: uuid.UUID, data: CompanyUpdate
) -> Company | None:
    company = await session.get(Company, company_id)
    if not company:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    await session.flush()
    await try_embed(session, "company", company.id, company)
    return company


async def delete_company(session: AsyncSession, company_id: uuid.UUID) -> bool:
    company = await session.get(Company, company_id)
    if not company:
        return False
    await session.delete(company)
    await session.flush()
    return True
