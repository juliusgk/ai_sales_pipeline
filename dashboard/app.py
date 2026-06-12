"""AI Sales Pipeline — Streamlit Dashboard.

Main entry point. Configures the page and renders the sidebar navigation.
Streamlit multipage apps use the pages/ directory for automatic page routing.
"""

import streamlit as st

st.set_page_config(
    page_title="AI Sales Pipeline",
    page_icon="\U0001f4ca",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("\U0001f4ca AI Sales Pipeline")
    st.markdown("---")
    st.markdown(
        """
        **Pages**
        - \U0001f4cb Pipeline Overview
        - \U0001f464 Lead Detail
        - \U0001f4ac Interactions
        - \U0001f4c8 Analytics
        - \U0001f916 Chat Assistant
        - ⚙️ Settings
        """
    )
    st.markdown("---")
    st.caption("v0.1.0 | AI-powered sales management")

# ---------------------------------------------------------------------------
# Home page content
# ---------------------------------------------------------------------------

st.title("Welcome to AI Sales Pipeline")
st.markdown(
    """
    Your AI-powered sales assistant. Use the sidebar to navigate:

    - **Pipeline Overview** — Kanban board of all leads by status
    - **Lead Detail** — Deep-dive into individual leads and their history
    - **Interactions** — Filterable log of all touchpoints
    - **Analytics** — Pipeline metrics and visualizations
    - **Chat Assistant** — Ask questions about your pipeline in natural language
    - **Settings** — Manage integrations, tags, and data exports
    """
)

st.info(
    "Get started by navigating to **Pipeline Overview** in the sidebar, "
    "or ask the **Chat Assistant** a question like: "
    '"Who needs a follow-up this week?"'
)
