"""Integration endpoints for Gmail and LinkedIn."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.services import gmail_service, linkedin_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


# ---------------------------------------------------------------------------
# Gmail
# ---------------------------------------------------------------------------


@router.get("/gmail/status")
async def gmail_status():
    """Check if Gmail OAuth is authorized."""
    return {
        "authorized": gmail_service.is_authorized(),
        "message": "Gmail is connected." if gmail_service.is_authorized() else "Gmail not connected. Complete OAuth2 flow.",
    }


@router.get("/gmail/authorize")
async def gmail_authorize(request: Request):
    """Get the OAuth2 authorization URL. User must visit this URL to grant access."""
    redirect_uri = str(request.url_for("gmail_callback"))
    try:
        auth_url = gmail_service.get_authorize_url(redirect_uri)
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate auth URL. Ensure GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET are set. Error: {e}",
        )


@router.get("/gmail/callback")
async def gmail_callback(
    request: Request,
    code: str = Query(..., description="OAuth2 authorization code"),
):
    """OAuth2 callback — exchanges the authorization code for tokens."""
    redirect_uri = str(request.url_for("gmail_callback"))
    try:
        result = gmail_service.exchange_code(code, redirect_uri)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth2 token exchange failed: {e}")


@router.post("/gmail/sync")
async def sync_gmail(
    max_results: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    """Trigger Gmail sync — fetches recent emails and creates interaction records."""
    try:
        result = await gmail_service.sync_emails(session, max_results=max_results)
        return result
    except Exception as e:
        logger.error(f"Gmail sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Gmail sync failed: {e}")


# ---------------------------------------------------------------------------
# LinkedIn
# ---------------------------------------------------------------------------


@router.post("/linkedin/import/connections")
async def import_linkedin_connections(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
):
    """Import LinkedIn connections from a CSV export.

    Upload the Connections.csv file from LinkedIn's data export.
    Expected columns: First Name, Last Name, Email Address, Company, Position, Connected On
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    content = (await file.read()).decode("utf-8", errors="replace")
    try:
        result = await linkedin_service.import_connections(session, content)
        return result
    except Exception as e:
        logger.error(f"LinkedIn connections import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {e}")


@router.post("/linkedin/import/messages")
async def import_linkedin_messages(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
):
    """Import LinkedIn messages from a CSV export.

    Upload the Messages.csv file from LinkedIn's data export.
    Expected columns: CONVERSATION ID, CONVERSATION TITLE, FROM, TO, DATE, SUBJECT, CONTENT
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    content = (await file.read()).decode("utf-8", errors="replace")
    try:
        result = await linkedin_service.import_messages(session, content)
        return result
    except Exception as e:
        logger.error(f"LinkedIn messages import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {e}")
