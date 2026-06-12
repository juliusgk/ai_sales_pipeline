"""Interactions Log — filterable table of all interactions across all leads."""

import pandas as pd
import streamlit as st

from dashboard.api_client import list_interactions, list_leads

st.set_page_config(page_title="Interactions", page_icon="\U0001f4ac", layout="wide")
st.title("\U0001f4ac Interactions Log")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    leads = list_leads()
    lead_options = {"All Leads": None}
    for l in leads:
        lead_options[l.get("title", "Untitled")] = l["id"]
    selected_lead_label = st.selectbox("Lead", list(lead_options.keys()))
    selected_lead_id = lead_options[selected_lead_label]

with col2:
    type_options = [
        "All Types", "email_sent", "email_received", "call", "meeting",
        "linkedin_message", "linkedin_connection", "note", "deal_update", "other",
    ]
    selected_type = st.selectbox("Type", type_options)

# ---------------------------------------------------------------------------
# Fetch and display
# ---------------------------------------------------------------------------

interactions = list_interactions(
    lead_id=selected_lead_id,
    type_filter=selected_type if selected_type != "All Types" else None,
)

if not interactions:
    st.info("No interactions found with these filters.")
    st.stop()

st.metric("Total Interactions", len(interactions))

# Build a DataFrame for display
rows = []
for ix in interactions:
    rows.append({
        "Date": ix.get("occurred_at", "")[:16].replace("T", " "),
        "Type": ix.get("type", ""),
        "Direction": ix.get("direction", ""),
        "Subject": ix.get("subject", ""),
        "Body (preview)": (ix.get("body") or "")[:100],
        "Source": ix.get("source", ""),
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Expandable detail view
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Detail View")

for ix in interactions:
    date_str = ix.get("occurred_at", "")[:16].replace("T", " ")
    label = f"{ix.get('type', '?')} — {date_str}"
    if ix.get("subject"):
        label += f" — {ix['subject']}"

    with st.expander(label):
        if ix.get("direction"):
            st.markdown(f"**Direction:** {ix['direction']}")
        if ix.get("body"):
            st.markdown(ix["body"])
        if ix.get("source"):
            st.caption(f"Source: {ix['source']}")
        if ix.get("external_id"):
            st.caption(f"External ID: {ix['external_id']}")
