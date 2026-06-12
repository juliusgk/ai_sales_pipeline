"""Pipeline Overview — Kanban board of leads by status with summary metrics."""

import streamlit as st

from dashboard.api_client import list_leads

st.set_page_config(page_title="Pipeline Overview", page_icon="\U0001f4cb", layout="wide")
st.title("\U0001f4cb Pipeline Overview")

# ---------------------------------------------------------------------------
# Fetch data
# ---------------------------------------------------------------------------

leads = list_leads()

if not leads:
    st.info("No leads yet. Add some via the API or seed the database.")
    st.stop()

# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------

status_counts = {}
total_value = 0.0
stale_count = 0

for lead in leads:
    s = lead.get("status", "unknown")
    status_counts[s] = status_counts.get(s, 0) + 1
    val = lead.get("estimated_value")
    if val:
        total_value += float(val)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Leads", len(leads))
col2.metric("In Progress", status_counts.get("in_progress", 0))
col3.metric("New", status_counts.get("new", 0))
col4.metric("Clients", status_counts.get("client", 0))
col5.metric("Pipeline Value", f"${total_value:,.0f}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

with st.expander("Filters", expanded=False):
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        source_filter = st.selectbox(
            "Source",
            ["All"] + sorted({l.get("source", "") for l in leads if l.get("source")}),
        )
    with filter_col2:
        priority_filter = st.selectbox("Min Priority", [1, 2, 3, 4, 5], index=0)
    with filter_col3:
        search_term = st.text_input("Search title")

# Apply filters
filtered = leads
if source_filter != "All":
    filtered = [l for l in filtered if l.get("source") == source_filter]
if priority_filter > 1:
    filtered = [l for l in filtered if (l.get("priority") or 0) >= priority_filter]
if search_term:
    term = search_term.lower()
    filtered = [l for l in filtered if term in (l.get("title") or "").lower()]

# ---------------------------------------------------------------------------
# Kanban board
# ---------------------------------------------------------------------------

STATUS_ORDER = ["new", "in_progress", "on_hold", "client", "no_deal"]
STATUS_LABELS = {
    "new": "\U0001f7e2 New",
    "in_progress": "\U0001f535 In Progress",
    "on_hold": "\U0001f7e1 On Hold",
    "client": "✅ Client",
    "no_deal": "❌ No Deal",
}

cols = st.columns(len(STATUS_ORDER))

for col, status in zip(cols, STATUS_ORDER):
    with col:
        st.subheader(STATUS_LABELS.get(status, status))
        status_leads = [l for l in filtered if l.get("status") == status]

        if not status_leads:
            st.caption("No leads")
            continue

        for lead in status_leads:
            company_name = ""
            if lead.get("company") and lead["company"].get("name"):
                company_name = lead["company"]["name"]

            contact_name = ""
            if lead.get("primary_contact"):
                pc = lead["primary_contact"]
                contact_name = f"{pc.get('first_name', '')} {pc.get('last_name', '')}"

            priority_stars = "⭐" * (lead.get("priority") or 0)
            value_str = ""
            if lead.get("estimated_value"):
                value_str = f"${float(lead['estimated_value']):,.0f}"

            tags_str = ""
            if lead.get("tags"):
                tags_str = " ".join(f"`{t['name']}`" for t in lead["tags"])

            with st.container(border=True):
                st.markdown(f"**{lead.get('title', 'Untitled')}**")
                if company_name:
                    st.caption(f"\U0001f3e2 {company_name}")
                if contact_name.strip():
                    st.caption(f"\U0001f464 {contact_name}")
                meta_parts = []
                if priority_stars:
                    meta_parts.append(priority_stars)
                if value_str:
                    meta_parts.append(value_str)
                if meta_parts:
                    st.caption(" | ".join(meta_parts))
                if tags_str:
                    st.markdown(tags_str)
