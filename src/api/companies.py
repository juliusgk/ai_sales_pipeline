"""API routes for companies."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from src.services import company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=list[CompanyRead])
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    return await company_service.get_companies(session, skip=skip, limit=limit)


@router.get("/{company_id}", response_model=CompanyRead)
async def get_company(
    company_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    company = await company_service.get_company(session, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/", response_model=CompanyRead, status_code=201)
async def create_company(
    data: CompanyCreate,
    session: AsyncSession = Depends(get_session),
):
    return await company_service.create_company(session, data)


@router.patch("/{company_id}", response_model=CompanyRead)
async def update_company(
    company_id: uuid.UUID,
    data: CompanyUpdate,
    session: AsyncSession = Depends(get_session),
):
    company = await company_service.update_company(session, company_id, data)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.delete("/{company_id}", status_code=204)
async def delete_company(
    company_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    deleted = await company_service.delete_company(session, company_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Company not found")
