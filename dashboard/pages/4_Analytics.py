"""Analytics — pipeline metrics, funnel visualization, and activity charts."""

from collections import Counter
from datetime import datetime

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.api_client import list_deals, list_interactions, list_leads

st.set_page_config(page_title="Analytics", page_icon="\U0001f4c8", layout="wide")
st.title("\U0001f4c8 Analytics")

# ---------------------------------------------------------------------------
# Fetch data
# ---------------------------------------------------------------------------

leads = list_leads()
interactions = list_interactions()
deals = list_deals()

if not leads:
    st.info("No data yet. Add leads to see analytics.")
    st.stop()

# ---------------------------------------------------------------------------
# Pipeline funnel
# ---------------------------------------------------------------------------

st.subheader("Pipeline Funnel")

STATUS_ORDER = ["new", "in_progress", "on_hold", "client", "no_deal"]
STATUS_LABELS = {
    "new": "New",
    "in_progress": "In Progress",
    "on_hold": "On Hold",
    "client": "Client",
    "no_deal": "No Deal",
}

status_counts = Counter(l.get("status", "unknown") for l in leads)
funnel_data = [
    {"Stage": STATUS_LABELS.get(s, s), "Count": status_counts.get(s, 0)}
    for s in STATUS_ORDER
]

fig_funnel = go.Figure(go.Funnel(
    y=[d["Stage"] for d in funnel_data],
    x=[d["Count"] for d in funnel_data],
    textinfo="value+percent initial",
))
fig_funnel.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig_funnel, use_container_width=True)

# ---------------------------------------------------------------------------
# Key metrics
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Key Metrics")

col1, col2, col3, col4 = st.columns(4)

total_value = sum(float(l.get("estimated_value") or 0) for l in leads)
won_value = sum(float(d.get("value") or 0) for d in deals if d.get("stage") == "closed_won")
active_count = sum(1 for l in leads if l.get("status") in ("new", "in_progress"))

col1.metric("Total Pipeline Value", f"${total_value:,.0f}")
col2.metric("Won Revenue", f"${won_value:,.0f}")
col3.metric("Active Leads", active_count)
col4.metric("Total Interactions", len(interactions))

# ---------------------------------------------------------------------------
# Leads by source
# ---------------------------------------------------------------------------

st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Leads by Source")
    source_counts = Counter(l.get("source", "unknown") for l in leads)
    if source_counts:
        fig_source = px.pie(
            names=list(source_counts.keys()),
            values=list(source_counts.values()),
            hole=0.4,
        )
        fig_source.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_source, use_container_width=True)

# ---------------------------------------------------------------------------
# Leads by priority
# ---------------------------------------------------------------------------

with col_right:
    st.subheader("Leads by Priority")
    priority_counts = Counter(l.get("priority", 3) for l in leads)
    priorities = sorted(priority_counts.keys())
    fig_priority = px.bar(
        x=[f"P{p}" for p in priorities],
        y=[priority_counts[p] for p in priorities],
        labels={"x": "Priority", "y": "Count"},
    )
    fig_priority.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_priority, use_container_width=True)

# ---------------------------------------------------------------------------
# Activity over time
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Activity Over Time")

if interactions:
    dates = []
    for ix in interactions:
        date_str = ix.get("occurred_at", "")
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                dates.append(dt.strftime("%Y-%m-%d"))
            except (ValueError, TypeError):
                pass

    if dates:
        date_counts = Counter(dates)
        sorted_dates = sorted(date_counts.keys())
        fig_activity = px.bar(
            x=sorted_dates,
            y=[date_counts[d] for d in sorted_dates],
            labels={"x": "Date", "y": "Interactions"},
        )
        fig_activity.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_activity, use_container_width=True)
    else:
        st.caption("No dated interactions to chart.")
else:
    st.caption("No interactions yet.")

# ---------------------------------------------------------------------------
# Top leads by value
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Top Leads by Estimated Value")

valued_leads = [l for l in leads if l.get("estimated_value")]
valued_leads.sort(key=lambda l: float(l["estimated_value"]), reverse=True)

if valued_leads:
    fig_top = px.bar(
        x=[l["title"][:30] for l in valued_leads[:10]],
        y=[float(l["estimated_value"]) for l in valued_leads[:10]],
        labels={"x": "Lead", "y": "Value ($)"},
    )
    fig_top.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_top, use_container_width=True)
else:
    st.caption("No leads with estimated values.")
