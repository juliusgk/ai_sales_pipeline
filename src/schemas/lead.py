"""Pydantic schemas for Lead."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.company import CompanyRead
from src.schemas.contact import ContactRead
from src.schemas.tag import TagRead


class LeadStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    CLIENT = "client"
    NO_DEAL = "no_deal"


class LeadSource(str, Enum):
    LINKEDIN = "linkedin"
    GMAIL = "gmail"
    REFERRAL = "referral"
    COLD_OUTREACH = "cold_outreach"
    WEBSITE = "website"
    OTHER = "other"


class LeadBase(BaseModel):
    company_id: uuid.UUID | None = None
    primary_contact_id: uuid.UUID | None = None
    title: str
    status: LeadStatus = LeadStatus.NEW
    source: LeadSource | None = None
    priority: int = Field(default=3, ge=1, le=5)
    estimated_value: float | None = None
    currency: str = "USD"
    notes: str | None = None


class LeadCreate(LeadBase):
    tag_ids: list[uuid.UUID] = []


class LeadUpdate(BaseModel):
    company_id: uuid.UUID | None = None
    primary_contact_id: uuid.UUID | None = None
    title: str | None = None
    status: LeadStatus | None = None
    source: LeadSource | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    estimated_value: float | None = None
    currency: str | None = None
    notes: str | None = None
    tag_ids: list[uuid.UUID] | None = None


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    last_activity_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    company: CompanyRead | None = None
    primary_contact: ContactRead | None = None
    tags: list[TagRead] = []
