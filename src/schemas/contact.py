"""Pydantic schemas for Contact."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContactBase(BaseModel):
    company_id: uuid.UUID | None = None
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    job_title: str | None = None
    is_primary: bool = False
    notes: str | None = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    company_id: uuid.UUID | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    job_title: str | None = None
    is_primary: bool | None = None
    notes: str | None = None


class ContactRead(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
