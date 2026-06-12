"""API routes for interactions."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas.interaction import InteractionCreate, InteractionRead, InteractionUpdate
from src.services import interaction_service

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.get("/", response_model=list[InteractionRead])
async def list_interactions(
    skip: int = 0,
    limit: int = 100,
    lead_id: uuid.UUID | None = None,
    type: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    return await interaction_service.get_interactions(
        session, skip=skip, limit=limit, lead_id=lead_id, interaction_type=type
    )


@router.get("/{interaction_id}", response_model=InteractionRead)
async def get_interaction(
    interaction_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    interaction = await interaction_service.get_interaction(session, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.post("/", response_model=InteractionRead, status_code=201)
async def create_interaction(
    data: InteractionCreate,
    session: AsyncSession = Depends(get_session),
):
    return await interaction_service.create_interaction(session, data)


@router.patch("/{interaction_id}", response_model=InteractionRead)
async def update_interaction(
    interaction_id: uuid.UUID,
    data: InteractionUpdate,
    session: AsyncSession = Depends(get_session),
):
    interaction = await interaction_service.update_interaction(
        session, interaction_id, data
    )
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.delete("/{interaction_id}", status_code=204)
async def delete_interaction(
    interaction_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    deleted = await interaction_service.delete_interaction(session, interaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Interaction not found")
