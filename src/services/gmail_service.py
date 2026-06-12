"""Gmail integration service — OAuth2 auth, message fetching, and interaction creation.

Flow:
1. User completes OAuth2 consent via /api/integrations/gmail/authorize
2. Callback stores encrypted refresh token
3. /api/integrations/gmail/sync fetches recent emails, matches to known contacts,
   creates interaction records with deduplication via external_id (Gmail message ID)
"""

import base64
import json
import logging
import os
from datetime import datetime, timezone
from email.utils import parseaddr
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.contact import Contact
from src.models.interaction import Interaction
from src.services._embed_helper import try_embed

logger = logging.getLogger(__name__)

# Path to store OAuth tokens (encrypted at rest via VM disk encryption)
TOKEN_PATH = Path(os.getenv("GMAIL_TOKEN_PATH", "/app/data/gmail_token.json"))
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


# ---------------------------------------------------------------------------
# OAuth2 helpers
# ---------------------------------------------------------------------------


def get_oauth_flow(redirect_uri: str) -> Flow:
    """Create an OAuth2 flow for Gmail API authorization."""
    client_config = {
        "web": {
            "client_id": settings.gmail_client_id,
            "client_secret": settings.gmail_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    return Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=redirect_uri)


def get_authorize_url(redirect_uri: str) -> str:
    """Generate the OAuth2 authorization URL for the user to visit."""
    flow = get_oauth_flow(redirect_uri)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code(code: str, redirect_uri: str) -> dict:
    """Exchange the authorization code for tokens and save them."""
    flow = get_oauth_flow(redirect_uri)
    flow.fetch_token(code=code)
    creds = flow.credentials

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }

    # Ensure directory exists
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(token_data))

    return {"status": "authorized", "message": "Gmail connected successfully."}


def _get_credentials() -> Credentials | None:
    """Load stored credentials, refresh if needed."""
    if not TOKEN_PATH.exists():
        return None

    token_data = json.loads(TOKEN_PATH.read_text())
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Save refreshed token
            token_data["token"] = creds.token
            TOKEN_PATH.write_text(json.dumps(token_data))
        except Exception as e:
            logger.error(f"Failed to refresh Gmail token: {e}")
            return None

    return creds


def is_authorized() -> bool:
    """Check if Gmail OAuth tokens are stored and valid."""
    creds = _get_credentials()
    return creds is not None and creds.valid


# ---------------------------------------------------------------------------
# Email fetching and sync
# ---------------------------------------------------------------------------


def _decode_body(payload: dict) -> str:
    """Extract plain text body from Gmail message payload."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    # Multipart — look for text/plain part
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        # Nested multipart
        if part.get("parts"):
            result = _decode_body(part)
            if result:
                return result

    return ""


def _get_header(headers: list[dict], name: str) -> str:
    """Get a specific header value from Gmail message headers."""
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


async def sync_emails(
    session: AsyncSession,
    max_results: int = 50,
) -> dict:
    """Fetch recent emails and create interaction records for known contacts.

    Returns a summary of the sync operation.
    """
    creds = _get_credentials()
    if not creds or not creds.valid:
        return {
            "status": "error",
            "message": "Gmail not authorized. Complete OAuth2 flow first.",
            "synced": 0,
            "skipped": 0,
        }

    # Build Gmail API client
    service = build("gmail", "v1", credentials=creds)

    # Fetch recent messages
    results = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_results, q="in:inbox OR in:sent")
        .execute()
    )
    messages = results.get("messages", [])

    if not messages:
        return {"status": "ok", "message": "No messages found.", "synced": 0, "skipped": 0}

    # Load all known contact emails for matching
    contact_result = await session.execute(
        select(Contact).where(Contact.email.isnot(None))
    )
    contacts = contact_result.scalars().all()
    email_to_contact = {c.email.lower(): c for c in contacts if c.email}

    synced = 0
    skipped = 0

    for msg_summary in messages:
        msg_id = msg_summary["id"]

        # Check for duplicate via external_id
        existing = await session.execute(
            select(Interaction).where(Interaction.external_id == msg_id)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        # Fetch full message
        try:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
        except Exception as e:
            logger.warning(f"Failed to fetch message {msg_id}: {e}")
            skipped += 1
            continue

        headers = msg.get("payload", {}).get("headers", [])
        from_email = parseaddr(_get_header(headers, "From"))[1].lower()
        to_email = parseaddr(_get_header(headers, "To"))[1].lower()
        subject = _get_header(headers, "Subject")
        date_str = _get_header(headers, "Date")

        # Determine if this is sent or received
        # Match against known contacts
        contact = email_to_contact.get(from_email) or email_to_contact.get(to_email)
        if not contact:
            skipped += 1
            continue

        # Determine direction
        if from_email in email_to_contact:
            direction = "inbound"
            interaction_type = "email_received"
        else:
            direction = "outbound"
            interaction_type = "email_sent"

        # Find associated lead (via contact's company or direct association)
        # Look for any lead that has this contact
        lead_result = await session.execute(
            select(Interaction.lead_id)
            .where(Interaction.contact_id == contact.id)
            .limit(1)
        )
        lead_id_row = lead_result.first()

        if not lead_id_row:
            # Try to find a lead via company
            from src.models.lead import Lead

            if contact.company_id:
                lead_result = await session.execute(
                    select(Lead.id).where(Lead.company_id == contact.company_id).limit(1)
                )
                lead_id_row = lead_result.first()

        if not lead_id_row:
            skipped += 1
            continue

        lead_id = lead_id_row[0]

        # Parse date
        try:
            from email.utils import parsedate_to_datetime

            occurred_at = parsedate_to_datetime(date_str).astimezone(timezone.utc)
        except Exception:
            occurred_at = datetime.now(timezone.utc)

        # Extract body
        body = _decode_body(msg.get("payload", {}))
        if len(body) > 5000:
            body = body[:5000] + "\n\n[... truncated]"

        # Create interaction
        interaction = Interaction(
            lead_id=lead_id,
            contact_id=contact.id,
            type=interaction_type,
            direction=direction,
            subject=subject[:500] if subject else None,
            body=body or None,
            occurred_at=occurred_at,
            source="gmail_sync",
            external_id=msg_id,
            metadata_={"gmail_thread_id": msg.get("threadId")},
        )
        session.add(interaction)
        await session.flush()

        # Auto-embed
        await try_embed(session, "interaction", interaction.id, interaction)

        # Update lead's last_activity_at
        from src.models.lead import Lead

        lead = await session.get(Lead, lead_id)
        if lead and (not lead.last_activity_at or occurred_at > lead.last_activity_at):
            lead.last_activity_at = occurred_at
            await session.flush()

        synced += 1

    await session.commit()

    return {
        "status": "ok",
        "message": f"Synced {synced} emails, skipped {skipped} (duplicates or unmatched).",
        "synced": synced,
        "skipped": skipped,
    }
