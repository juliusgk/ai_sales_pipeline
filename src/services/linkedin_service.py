"""LinkedIn integration service — CSV import for connections and messages.

LinkedIn doesn't provide API access to messages for most apps, so we support
importing data from LinkedIn's "Download Your Data" CSV exports:

1. Connections.csv — creates/updates contacts
2. Messages.csv — creates interaction records linked to matching contacts/leads

Export instructions:
- Go to LinkedIn > Settings > Data Privacy > Get a copy of your data
- Select "Connections" and "Messages"
- Download the ZIP and extract the CSV files
"""

import csv
import io
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.company import Company
from src.models.contact import Contact
from src.models.interaction import Interaction
from src.models.lead import Lead
from src.services._embed_helper import try_embed

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connections CSV import
# ---------------------------------------------------------------------------


async def import_connections(
    session: AsyncSession,
    csv_content: str,
) -> dict:
    """Import LinkedIn connections from a CSV export.

    Expected columns (LinkedIn standard export):
    - First Name, Last Name, Email Address, Company, Position, Connected On

    Returns a summary of the import.
    """
    reader = csv.DictReader(io.StringIO(csv_content))

    created = 0
    updated = 0
    skipped = 0

    for row in reader:
        first_name = (row.get("First Name") or "").strip()
        last_name = (row.get("Last Name") or "").strip()
        email = (row.get("Email Address") or "").strip().lower()
        company_name = (row.get("Company") or "").strip()
        position = (row.get("Position") or "").strip()
        connected_on = (row.get("Connected On") or "").strip()

        if not first_name or not last_name:
            skipped += 1
            continue

        # Find or create company
        company_id = None
        if company_name:
            result = await session.execute(
                select(Company).where(Company.name == company_name)
            )
            company = result.scalar_one_or_none()
            if not company:
                company = Company(name=company_name)
                session.add(company)
                await session.flush()
                await try_embed(session, "company", company.id, company)
            company_id = company.id

        # Check if contact exists (by email or name+company)
        existing_contact = None
        if email:
            result = await session.execute(
                select(Contact).where(Contact.email == email)
            )
            existing_contact = result.scalar_one_or_none()

        if not existing_contact and company_id:
            result = await session.execute(
                select(Contact).where(
                    Contact.first_name == first_name,
                    Contact.last_name == last_name,
                    Contact.company_id == company_id,
                )
            )
            existing_contact = result.scalar_one_or_none()

        if existing_contact:
            # Update with LinkedIn data if missing
            changed = False
            if not existing_contact.linkedin_url and email:
                existing_contact.email = existing_contact.email or email
                changed = True
            if not existing_contact.job_title and position:
                existing_contact.job_title = position
                changed = True
            if not existing_contact.company_id and company_id:
                existing_contact.company_id = company_id
                changed = True
            if changed:
                await session.flush()
                await try_embed(session, "contact", existing_contact.id, existing_contact)
                updated += 1
            else:
                skipped += 1
        else:
            # Create new contact
            contact = Contact(
                company_id=company_id,
                first_name=first_name,
                last_name=last_name,
                email=email or None,
                job_title=position or None,
                notes=f"Imported from LinkedIn. Connected on: {connected_on}" if connected_on else "Imported from LinkedIn.",
            )
            session.add(contact)
            await session.flush()
            await try_embed(session, "contact", contact.id, contact)
            created += 1

    await session.commit()

    return {
        "status": "ok",
        "type": "connections",
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "message": f"Imported {created} new contacts, updated {updated}, skipped {skipped}.",
    }


# ---------------------------------------------------------------------------
# Messages CSV import
# ---------------------------------------------------------------------------


async def import_messages(
    session: AsyncSession,
    csv_content: str,
) -> dict:
    """Import LinkedIn messages from a CSV export.

    Expected columns (LinkedIn standard export):
    - CONVERSATION ID, CONVERSATION TITLE, FROM, SENDER PROFILE URL,
      TO, DATE, SUBJECT, CONTENT

    Returns a summary of the import.
    """
    reader = csv.DictReader(io.StringIO(csv_content))

    created = 0
    skipped = 0

    for row in reader:
        sender = (row.get("FROM") or "").strip()
        content = (row.get("CONTENT") or "").strip()
        subject = (row.get("SUBJECT") or "").strip()
        date_str = (row.get("DATE") or "").strip()
        conversation_id = (row.get("CONVERSATION ID") or "").strip()

        if not content or not sender:
            skipped += 1
            continue

        # Build external_id for deduplication
        external_id = f"linkedin_msg_{conversation_id}_{hash(content[:100])}"

        # Check for duplicate
        existing = await session.execute(
            select(Interaction).where(Interaction.external_id == external_id)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        # Try to match sender to a contact (by name — LinkedIn doesn't provide emails in messages)
        name_parts = sender.split(maxsplit=1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        contact = None
        if first_name and last_name:
            result = await session.execute(
                select(Contact).where(
                    Contact.first_name == first_name,
                    Contact.last_name == last_name,
                )
            )
            contact = result.scalar_one_or_none()

        if not contact:
            skipped += 1
            continue

        # Find associated lead
        lead_id = None

        # Check existing interactions for this contact
        lead_result = await session.execute(
            select(Interaction.lead_id)
            .where(Interaction.contact_id == contact.id)
            .limit(1)
        )
        lead_row = lead_result.first()

        if lead_row:
            lead_id = lead_row[0]
        elif contact.company_id:
            # Find a lead via company
            lead_result = await session.execute(
                select(Lead.id).where(Lead.company_id == contact.company_id).limit(1)
            )
            lead_row = lead_result.first()
            if lead_row:
                lead_id = lead_row[0]

        if not lead_id:
            skipped += 1
            continue

        # Parse date
        try:
            occurred_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            try:
                # LinkedIn sometimes uses "YYYY-MM-DD HH:MM:SS UTC"
                occurred_at = datetime.strptime(
                    date_str.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                occurred_at = datetime.now(timezone.utc)

        # Create interaction
        interaction = Interaction(
            lead_id=lead_id,
            contact_id=contact.id,
            type="linkedin_message",
            direction="inbound",  # Can't reliably determine from CSV
            subject=subject[:500] if subject else None,
            body=content,
            occurred_at=occurred_at,
            source="linkedin_sync",
            external_id=external_id,
            metadata_={"linkedin_conversation_id": conversation_id},
        )
        session.add(interaction)
        await session.flush()
        await try_embed(session, "interaction", interaction.id, interaction)

        # Update lead's last_activity_at
        lead = await session.get(Lead, lead_id)
        if lead and (not lead.last_activity_at or occurred_at > lead.last_activity_at):
            lead.last_activity_at = occurred_at
            await session.flush()

        created += 1

    await session.commit()

    return {
        "status": "ok",
        "type": "messages",
        "created": created,
        "skipped": skipped,
        "message": f"Imported {created} messages, skipped {skipped} (duplicates or unmatched).",
    }
