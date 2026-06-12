"""API routes for contacts."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas.contact import ContactCreate, ContactRead, ContactUpdate
from src.services import contact_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactRead])
async def list_contacts(
    skip: int = 0,
    limit: int = 100,
    company_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
):
    return await contact_service.get_contacts(
        session, skip=skip, limit=limit, company_id=company_id
    )


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact(
    contact_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    contact = await contact_service.get_contact(session, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactRead, status_code=201)
async def create_contact(
    data: ContactCreate,
    session: AsyncSession = Depends(get_session),
):
    return await contact_service.create_contact(session, data)


@router.patch("/{contact_id}", response_model=ContactRead)
async def update_contact(
    contact_id: uuid.UUID,
    data: ContactUpdate,
    session: AsyncSession = Depends(get_session),
):
    contact = await contact_service.update_contact(session, contact_id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    deleted = await contact_service.delete_contact(session, contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
