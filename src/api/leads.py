"""API routes for leads — the central pipeline entity."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas.lead import LeadCreate, LeadRead, LeadStatus, LeadUpdate
from src.services import lead_service

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/", response_model=list[LeadRead])
async def list_leads(
    skip: int = 0,
    limit: int = 100,
    status: LeadStatus | None = None,
    source: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    return await lead_service.get_leads(
        session, skip=skip, limit=limit, status=status, source=source
    )


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(
    lead_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    lead = await lead_service.get_lead(session, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/", response_model=LeadRead, status_code=201)
async def create_lead(
    data: LeadCreate,
    session: AsyncSession = Depends(get_session),
):
    return await lead_service.create_lead(session, data)


@router.patch("/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: uuid.UUID,
    data: LeadUpdate,
    session: AsyncSession = Depends(get_session),
):
    lead = await lead_service.update_lead(session, lead_id, data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(
    lead_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    deleted = await lead_service.delete_lead(session, lead_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Lead not found")
