"""SQLAlchemy models — import all models here so Alembic can discover them."""

from src.models.base import Base
from src.models.company import Company
from src.models.contact import Contact
from src.models.deal import Deal
from src.models.embedding import Embedding
from src.models.interaction import Interaction
from src.models.lead import Lead
from src.models.tag import Tag, lead_tags

__all__ = [
    "Base",
    "Company",
    "Contact",
    "Deal",
    "Embedding",
    "Interaction",
    "Lead",
    "Tag",
    "lead_tags",
]
