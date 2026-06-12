"""Seed the database with sample data for development and testing.

Usage:
    python -m scripts.seed_data

Requires: DATABASE_URL set in .env (or environment), PostgreSQL running.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from src.database import async_session_factory, engine
from src.models import Base
from src.models.company import Company
from src.models.contact import Contact
from src.models.deal import Deal
from src.models.interaction import Interaction
from src.models.lead import Lead
from src.models.tag import Tag


async def seed():
    # Create tables (for dev — in prod use Alembic)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        now = datetime.now(timezone.utc)

        # --- Tags ---
        tags = {
            "hot": Tag(name="hot", color="#FF4444"),
            "enterprise": Tag(name="enterprise", color="#4444FF"),
            "startup": Tag(name="startup", color="#44FF44"),
            "referral": Tag(name="referral", color="#FF8844"),
            "follow-up": Tag(name="follow-up", color="#FFAA00"),
        }
        for tag in tags.values():
            session.add(tag)
        await session.flush()

        # --- Companies ---
        acme = Company(
            name="Acme Corp",
            domain="acme.com",
            industry="Technology",
            size_range="51-200",
            notes="Mid-size SaaS company. Strong growth trajectory.",
        )
        globex = Company(
            name="Globex International",
            domain="globex.io",
            industry="Manufacturing",
            size_range="201-500",
            linkedin_url="https://linkedin.com/company/globex",
            notes="Enterprise manufacturing firm. Long sales cycles.",
        )
        initech = Company(
            name="Initech Solutions",
            domain="initech.co",
            industry="Consulting",
            size_range="11-50",
            notes="Small consultancy. Quick decision maker.",
        )
        umbrella = Company(
            name="Umbrella Ventures",
            domain="umbrella.vc",
            industry="Finance",
            size_range="11-50",
            notes="VC firm. Potential partnership opportunity.",
        )
        session.add_all([acme, globex, initech, umbrella])
        await session.flush()

        # --- Contacts ---
        alice = Contact(
            company_id=acme.id,
            first_name="Alice",
            last_name="Johnson",
            email="alice@acme.com",
            job_title="VP of Engineering",
            is_primary=True,
            notes="Technical decision maker. Prefers email.",
        )
        bob = Contact(
            company_id=acme.id,
            first_name="Bob",
            last_name="Smith",
            email="bob@acme.com",
            job_title="CTO",
            notes="Final sign-off authority.",
        )
        carol = Contact(
            company_id=globex.id,
            first_name="Carol",
            last_name="Williams",
            email="carol.w@globex.io",
            job_title="Head of Procurement",
            is_primary=True,
            notes="Careful evaluator. Needs detailed proposals.",
        )
        dave = Contact(
            company_id=initech.id,
            first_name="Dave",
            last_name="Brown",
            email="dave@initech.co",
            job_title="Founder & CEO",
            is_primary=True,
            notes="Hands-on founder. Responds fast on LinkedIn.",
        )
        eve = Contact(
            company_id=umbrella.id,
            first_name="Eve",
            last_name="Martinez",
            email="eve@umbrella.vc",
            job_title="Managing Partner",
            is_primary=True,
        )
        session.add_all([alice, bob, carol, dave, eve])
        await session.flush()

        # --- Leads ---
        lead1 = Lead(
            company_id=acme.id,
            primary_contact_id=alice.id,
            title="Acme Corp — AI Platform Integration",
            status="in_progress",
            source="linkedin",
            priority=5,
            estimated_value=75000.00,
            notes="Interested in our AI analytics module. Demo scheduled.",
            last_activity_at=now - timedelta(days=1),
        )
        lead1.tags = [tags["hot"], tags["enterprise"]]

        lead2 = Lead(
            company_id=globex.id,
            primary_contact_id=carol.id,
            title="Globex — Enterprise Data Pipeline",
            status="new",
            source="referral",
            priority=4,
            estimated_value=120000.00,
            notes="Referred by an existing client. Initial meeting pending.",
            last_activity_at=now - timedelta(days=5),
        )
        lead2.tags = [tags["enterprise"], tags["referral"]]

        lead3 = Lead(
            company_id=initech.id,
            primary_contact_id=dave.id,
            title="Initech — Consulting Tool License",
            status="on_hold",
            source="cold_outreach",
            priority=3,
            estimated_value=15000.00,
            notes="Budget review in Q3. Follow up in August.",
            last_activity_at=now - timedelta(days=14),
        )
        lead3.tags = [tags["startup"], tags["follow-up"]]

        lead4 = Lead(
            company_id=umbrella.id,
            primary_contact_id=eve.id,
            title="Umbrella Ventures — Strategic Partnership",
            status="client",
            source="referral",
            priority=5,
            estimated_value=50000.00,
            notes="Partnership agreement signed. Ongoing relationship.",
            last_activity_at=now - timedelta(days=2),
        )
        lead4.tags = [tags["hot"]]

        session.add_all([lead1, lead2, lead3, lead4])
        await session.flush()

        # --- Deals ---
        deal1 = Deal(
            lead_id=lead4.id,
            stage="closed_won",
            value=50000.00,
            expected_close_date=(now - timedelta(days=10)).date(),
            actual_close_date=(now - timedelta(days=3)).date(),
            notes="Partnership deal closed. Annual renewal.",
        )
        session.add(deal1)
        await session.flush()

        # --- Interactions ---
        interactions = [
            Interaction(
                lead_id=lead1.id,
                contact_id=alice.id,
                type="linkedin_connection",
                direction="outbound",
                subject="Initial connection request",
                body="Connected with Alice Johnson on LinkedIn. She accepted within 2 hours.",
                occurred_at=now - timedelta(days=30),
                source="manual",
            ),
            Interaction(
                lead_id=lead1.id,
                contact_id=alice.id,
                type="email_sent",
                direction="outbound",
                subject="Introduction to our AI Platform",
                body="Hi Alice, great connecting on LinkedIn! I wanted to introduce our AI analytics platform that's helping companies like Acme streamline their data workflows. Would you be open to a 15-minute call next week?",
                occurred_at=now - timedelta(days=25),
                source="manual",
            ),
            Interaction(
                lead_id=lead1.id,
                contact_id=alice.id,
                type="email_received",
                direction="inbound",
                subject="Re: Introduction to our AI Platform",
                body="Hi, thanks for reaching out! This sounds interesting. We're currently evaluating tools for our Q3 roadmap. Can we schedule a demo for next Thursday?",
                occurred_at=now - timedelta(days=23),
                source="manual",
            ),
            Interaction(
                lead_id=lead1.id,
                contact_id=alice.id,
                type="meeting",
                direction="outbound",
                subject="Product demo — Acme Corp",
                body="Conducted a 45-minute demo for Alice and Bob. They were impressed with the real-time analytics dashboard. Key concern: data privacy and SOC2 compliance. Next step: send compliance documentation and proposal.",
                occurred_at=now - timedelta(days=18),
                source="manual",
            ),
            Interaction(
                lead_id=lead1.id,
                contact_id=alice.id,
                type="email_sent",
                direction="outbound",
                subject="Follow-up: Proposal and compliance docs",
                body="Hi Alice, attached is our proposal for $75,000/year along with SOC2 compliance documentation. Happy to discuss any questions.",
                occurred_at=now - timedelta(days=15),
                source="manual",
            ),
            Interaction(
                lead_id=lead1.id,
                contact_id=bob.id,
                type="call",
                direction="inbound",
                subject="Technical questions from CTO",
                body="Bob called with questions about API rate limits, data retention policies, and integration with their existing Snowflake setup. Provided detailed answers. He seemed satisfied.",
                occurred_at=now - timedelta(days=1),
                source="manual",
            ),
            # Globex interactions
            Interaction(
                lead_id=lead2.id,
                contact_id=carol.id,
                type="email_sent",
                direction="outbound",
                subject="Introduction via mutual connection",
                body="Hi Carol, John from DataFlow recommended I reach out. We specialize in enterprise data pipelines and I'd love to discuss how we can help Globex.",
                occurred_at=now - timedelta(days=5),
                source="manual",
            ),
            # Initech interactions
            Interaction(
                lead_id=lead3.id,
                contact_id=dave.id,
                type="linkedin_message",
                direction="outbound",
                subject="Cold outreach on LinkedIn",
                body="Hey Dave, saw your post about scaling consulting operations. We built a tool that might help — mind if I share a quick overview?",
                occurred_at=now - timedelta(days=21),
                source="manual",
            ),
            Interaction(
                lead_id=lead3.id,
                contact_id=dave.id,
                type="call",
                direction="outbound",
                subject="Discovery call",
                body="30-minute discovery call with Dave. Interested but budget is locked until Q3. Agreed to reconnect in August. He asked to see a case study.",
                occurred_at=now - timedelta(days=14),
                source="manual",
            ),
            # Umbrella interactions
            Interaction(
                lead_id=lead4.id,
                contact_id=eve.id,
                type="meeting",
                direction="outbound",
                subject="Partnership negotiation",
                body="Met with Eve to finalize partnership terms. Agreed on $50K annual partnership with co-marketing benefits. Contract to be signed by EOW.",
                occurred_at=now - timedelta(days=10),
                source="manual",
            ),
            Interaction(
                lead_id=lead4.id,
                contact_id=eve.id,
                type="note",
                subject="Contract signed",
                body="Partnership agreement signed and countersigned. Annual renewal clause. Kickoff meeting scheduled for next week.",
                occurred_at=now - timedelta(days=3),
                source="manual",
            ),
        ]
        session.add_all(interactions)
        await session.commit()

        print("Seed data created successfully!")
        print(f"  - {len(tags)} tags")
        print(f"  - 4 companies")
        print(f"  - 5 contacts")
        print(f"  - 4 leads")
        print(f"  - 1 deal")
        print(f"  - {len(interactions)} interactions")


if __name__ == "__main__":
    asyncio.run(seed())
