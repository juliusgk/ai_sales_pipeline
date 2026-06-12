"""Pydantic schemas for Deal."""

import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DealStage(str, Enum):
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    VERBAL_YES = "verbal_yes"
    CONTRACT_SENT = "contract_sent"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class DealBase(BaseModel):
    lead_id: uuid.UUID
    stage: DealStage
    value: float | None = None
    currency: str = "USD"
    expected_close_date: date | None = None
    actual_close_date: date | None = None
    notes: str | None = None


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    stage: DealStage | None = None
    value: float | None = None
    currency: str | None = None
    expected_close_date: date | None = None
    actual_close_date: date | None = None
    notes: str | None = None


class DealRead(DealBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
