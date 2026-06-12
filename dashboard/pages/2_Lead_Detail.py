"""Lead Detail — deep-dive into an individual lead with edit, interactions, and deal info."""

from datetime import datetime

import streamlit as st

from dashboard.api_client import (
    create_interaction,
    get_lead,
    list_leads,
    update_lead,
)

st.set_page_config(page_title="Lead Detail", page_icon="\U0001f464", layout="wide")
st.title("\U0001f464 Lead Detail")

# ---------------------------------------------------------------------------
# Lead selector
# ---------------------------------------------------------------------------

leads = list_leads()
if not leads:
    st.info("No leads yet.")
    st.stop()

lead_options = {
    f"{l['title']} ({l.get('status', '?')})": l["id"] for l in leads
}
selected_label = st.selectbox("Select a lead", list(lead_options.keys()))
lead_id = lead_options[selected_label]

lead = get_lead(lead_id)
if not lead:
    st.error("Lead not found.")
    st.stop()

# ---------------------------------------------------------------------------
# Lead overview
# ---------------------------------------------------------------------------

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(lead.get("title", "Untitled"))

    if lead.get("company"):
        st.markdown(f"**Company:** {lead['company'].get('name', 'N/A')}")
    if lead.get("primary_contact"):
        pc = lead["primary_contact"]
        name = f"{pc.get('first_name', '')} {pc.get('last_name', '')}"
        title = pc.get("job_title", "")
        email = pc.get("email", "")
        st.markdown(f"**Contact:** {name}" + (f" — {title}" if title else "") + (f" ({email})" if email else ""))
    if lead.get("notes"):
        st.markdown(f"**Notes:** {lead['notes']}")

with col2:
    status = lead.get("status", "unknown")
    priority = lead.get("priority", 3)
    value = lead.get("estimated_value")
    source = lead.get("source", "N/A")

    st.markdown(f"**Status:** `{status}`")
    st.markdown(f"**Priority:** {'⭐' * priority} ({priority}/5)")
    st.markdown(f"**Source:** {source}")
    if value:
        st.markdown(f"**Value:** ${float(value):,.2f} {lead.get('currency', 'USD')}")
    if lead.get("tags"):
        tags_str = " ".join(f"`{t['name']}`" for t in lead["tags"])
        st.markdown(f"**Tags:** {tags_str}")

# ---------------------------------------------------------------------------
# Edit lead (collapsible)
# ---------------------------------------------------------------------------

with st.expander("Edit Lead"):
    STATUS_OPTIONS = ["new", "in_progress", "on_hold", "client", "no_deal"]
    current_idx = STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0

    new_status = st.selectbox("Status", STATUS_OPTIONS, index=current_idx, key="edit_status")
    new_priority = st.slider("Priority", 1, 5, priority, key="edit_priority")
    new_notes = st.text_area("Notes", lead.get("notes", ""), key="edit_notes")

    if st.button("Save Changes"):
        update_data = {}
        if new_status != status:
            update_data["status"] = new_status
        if new_priority != priority:
            update_data["priority"] = new_priority
        if new_notes != lead.get("notes", ""):
            update_data["notes"] = new_notes
        if update_data:
            result = update_lead(lead_id, update_data)
            if result:
                st.success("Lead updated!")
                st.rerun()
            else:
                st.error("Failed to update lead.")
        else:
            st.info("No changes to save.")

# ---------------------------------------------------------------------------
# Deal info
# ---------------------------------------------------------------------------

if lead.get("deal"):
    st.markdown("---")
    st.subheader("Deal")
    deal = lead["deal"]
    dcol1, dcol2, dcol3 = st.columns(3)
    dcol1.metric("Stage", deal.get("stage", "N/A"))
    if deal.get("value"):
        dcol2.metric("Value", f"${float(deal['value']):,.2f}")
    if deal.get("expected_close_date"):
        dcol3.metric("Expected Close", deal["expected_close_date"])
    if deal.get("notes"):
        st.markdown(f"**Deal Notes:** {deal['notes']}")

# ---------------------------------------------------------------------------
# Interaction timeline
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Interaction Timeline")

interactions = lead.get("interactions", [])

if not interactions:
    st.caption("No interactions recorded yet.")
else:
    # Sort by occurred_at descending
    interactions_sorted = sorted(
        interactions,
        key=lambda x: x.get("occurred_at", ""),
        reverse=True,
    )

    for ix in interactions_sorted:
        icon_map = {
            "email_sent": "\U0001f4e4",
            "email_received": "\U0001f4e5",
            "call": "\U0001f4de",
            "meeting": "\U0001f91d",
            "linkedin_message": "\U0001f4ac",
            "linkedin_connection": "\U0001f517",
            "note": "\U0001f4dd",
            "deal_update": "\U0001f4b0",
            "other": "\U0001f4cc",
        }
        icon = icon_map.get(ix.get("type", ""), "\U0001f4cc")
        direction = f" ({ix['direction']})" if ix.get("direction") else ""
        date_str = ix.get("occurred_at", "")[:16].replace("T", " ")

        with st.container(border=True):
            st.markdown(f"{icon} **{ix.get('type', 'unknown')}{direction}** — {date_str}")
            if ix.get("subject"):
                st.markdown(f"**Subject:** {ix['subject']}")
            if ix.get("body"):
                st.markdown(ix["body"][:500] + ("..." if len(ix.get("body", "")) > 500 else ""))

# ---------------------------------------------------------------------------
# Add interaction form
# ---------------------------------------------------------------------------

st.markdown("---")
with st.expander("Add Interaction"):
    TYPE_OPTIONS = [
        "email_sent", "email_received", "call", "meeting",
        "linkedin_message", "linkedin_connection", "note", "deal_update", "other",
    ]
    ix_type = st.selectbox("Type", TYPE_OPTIONS, key="add_ix_type")
    ix_direction = st.selectbox("Direction", ["outbound", "inbound", ""], key="add_ix_dir")
    ix_subject = st.text_input("Subject", key="add_ix_subject")
    ix_body = st.text_area("Body / Notes", key="add_ix_body")
    ix_date = st.date_input("Date", key="add_ix_date")

    if st.button("Add Interaction"):
        ix_data = {
            "lead_id": lead_id,
            "type": ix_type,
            "subject": ix_subject or None,
            "body": ix_body or None,
            "occurred_at": datetime.combine(ix_date, datetime.min.time()).isoformat(),
            "source": "manual",
        }
        if ix_direction:
            ix_data["direction"] = ix_direction
        result = create_interaction(ix_data)
        if result:
            st.success("Interaction added!")
            st.rerun()
        else:
            st.error("Failed to add interaction.")
