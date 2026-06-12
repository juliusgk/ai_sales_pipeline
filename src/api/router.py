"""Main API router — aggregates all sub-routers."""

from fastapi import APIRouter

from src.api.chat import router as chat_router
from src.api.companies import router as companies_router
from src.api.contacts import router as contacts_router
from src.api.deals import router as deals_router
from src.api.integrations import router as integrations_router
from src.api.interactions import router as interactions_router
from src.api.leads import router as leads_router
from src.api.tags import router as tags_router

api_router = APIRouter()

api_router.include_router(companies_router)
api_router.include_router(contacts_router)
api_router.include_router(leads_router)
api_router.include_router(interactions_router)
api_router.include_router(deals_router)
api_router.include_router(tags_router)
api_router.include_router(chat_router)
api_router.include_router(integrations_router)
