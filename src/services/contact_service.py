"""CRUD service for contacts."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.contact import Contact
from src.schemas.contact import ContactCreate, ContactUpdate
from src.services._embed_helper import try_embed


async def get_contacts(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    company_id: uuid.UUID | None = None,
) -> list[Contact]:
    stmt = select(Contact)
    if company_id:
        stmt = stmt.where(Contact.company_id == company_id)
    result = await session.execute(
        stmt.offset(skip).limit(limit).order_by(Contact.created_at.desc())
    )
    return list(result.scalars().all())


async def get_contact(session: AsyncSession, contact_id: uuid.UUID) -> Contact | None:
    return await session.get(Contact, contact_id)


async def get_contact_by_email(session: AsyncSession, email: str) -> Contact | None:
    result = await session.execute(select(Contact).where(Contact.email == email))
    return result.scalar_one_or_none()


async def create_contact(session: AsyncSession, data: ContactCreate) -> Contact:
    contact = Contact(**data.model_dump())
    session.add(contact)
    await session.flush()
    await try_embed(session, "contact", contact.id, contact)
    return contact


async def update_contact(
    session: AsyncSession, contact_id: uuid.UUID, data: ContactUpdate
) -> Contact | None:
    contact = await session.get(Contact, contact_id)
    if not contact:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    await session.flush()
    await try_embed(session, "contact", contact.id, contact)
    return contact


async def delete_contact(session: AsyncSession, contact_id: uuid.UUID) -> bool:
    contact = await session.get(Contact, contact_id)
    if not contact:
        return False
    await session.delete(contact)
    await session.flush()
    return True
