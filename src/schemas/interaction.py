"""Pydantic schemas for Interaction."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class InteractionType(str, Enum):
    EMAIL_SENT = "email_sent"
    EMAIL_RECEIVED = "email_received"
    CALL = "call"
    MEETING = "meeting"
    LINKEDIN_MESSAGE = "linkedin_message"
    LINKEDIN_CONNECTION = "linkedin_connection"
    NOTE = "note"
    DEAL_UPDATE = "deal_update"
    OTHER = "other"


class InteractionDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class InteractionBase(BaseModel):
    lead_id: uuid.UUID
    contact_id: uuid.UUID | None = None
    type: InteractionType
    direction: InteractionDirection | None = None
    subject: str | None = None
    body: str | None = None
    occurred_at: datetime
    source: str | None = "manual"
    external_id: str | None = None
    metadata_: dict[str, Any] | None = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    contact_id: uuid.UUID | None = None
    type: InteractionType | None = None
    direction: InteractionDirection | None = None
    subject: str | None = None
    body: str | None = None
    occurred_at: datetime | None = None
    source: str | None = None
    metadata_: dict[str, Any] | None = None


class InteractionRead(InteractionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
