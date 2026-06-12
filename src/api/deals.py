"""API routes for deals."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas.deal import DealCreate, DealRead, DealUpdate
from src.services import deal_service

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("/", response_model=list[DealRead])
async def list_deals(
    skip: int = 0,
    limit: int = 100,
    stage: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    return await deal_service.get_deals(session, skip=skip, limit=limit, stage=stage)


@router.get("/{deal_id}", response_model=DealRead)
async def get_deal(
    deal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    deal = await deal_service.get_deal(session, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.post("/", response_model=DealRead, status_code=201)
async def create_deal(
    data: DealCreate,
    session: AsyncSession = Depends(get_session),
):
    return await deal_service.create_deal(session, data)


@router.patch("/{deal_id}", response_model=DealRead)
async def update_deal(
    deal_id: uuid.UUID,
    data: DealUpdate,
    session: AsyncSession = Depends(get_session),
):
    deal = await deal_service.update_deal(session, deal_id, data)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.delete("/{deal_id}", status_code=204)
async def delete_deal(
    deal_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    deleted = await deal_service.delete_deal(session, deal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Deal not found")
