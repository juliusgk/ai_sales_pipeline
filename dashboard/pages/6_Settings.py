"""Settings — manage integrations, tags, and data exports."""

import json

import streamlit as st

from dashboard.api_client import (
    create_tag,
    delete_tag,
    gmail_authorize_url,
    gmail_status,
    import_linkedin_connections,
    import_linkedin_messages,
    list_leads,
    list_tags,
    sync_gmail,
)

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
st.title("⚙️ Settings")

# ---------------------------------------------------------------------------
# Integration status
# ---------------------------------------------------------------------------

st.subheader("Integrations")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Gmail")
    st.markdown("Sync emails with known contacts to automatically log interactions.")

    # Check authorization status
    try:
        status = gmail_status()
        is_authorized = status.get("authorized", False)
    except Exception:
        is_authorized = False
        st.warning("Could not check Gmail status. Is the API running?")

    if is_authorized:
        st.success("Gmail is connected.")
        if st.button("Sync Gmail Now"):
            with st.spinner("Syncing emails..."):
                result = sync_gmail()
            if result.get("status") == "ok":
                st.success(result.get("message", "Sync complete."))
            else:
                st.error(result.get("message", "Sync failed."))
            st.json(result)
    else:
        st.warning("Gmail not connected.")
        st.markdown(
            "To connect Gmail, you need to set `GMAIL_CLIENT_ID` and "
            "`GMAIL_CLIENT_SECRET` in your `.env` file, then complete the OAuth2 flow."
        )
        if st.button("Get Authorization URL"):
            try:
                url = gmail_authorize_url()
                if url:
                    st.markdown(f"Visit this URL to authorize: [Authorize Gmail]({url})")
                else:
                    st.error("Could not generate auth URL. Check Gmail credentials in .env.")
            except Exception as e:
                st.error(f"Error: {e}")

with col2:
    st.markdown("### LinkedIn")
    st.markdown(
        "Import connections and messages from LinkedIn's data export CSV files."
    )
    st.caption(
        "To export: LinkedIn > Settings > Data Privacy > Get a copy of your data "
        "> Select 'Connections' and 'Messages'"
    )

    import_type = st.radio(
        "Import type",
        ["Connections", "Messages"],
        horizontal=True,
        key="li_import_type",
    )

    uploaded = st.file_uploader(
        f"Upload {import_type}.csv",
        type=["csv"],
        key="linkedin_csv",
    )

    if uploaded:
        csv_bytes = uploaded.read()
        if st.button(f"Import {import_type}"):
            with st.spinner(f"Importing {import_type.lower()}..."):
                if import_type == "Connections":
                    result = import_linkedin_connections(csv_bytes, uploaded.name)
                else:
                    result = import_linkedin_messages(csv_bytes, uploaded.name)

            if result.get("status") == "ok":
                st.success(result.get("message", "Import complete."))
            else:
                st.error(result.get("message", "Import failed."))
            st.json(result)

# ---------------------------------------------------------------------------
# Tag management
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Tag Management")

tags = list_tags()

if tags:
    st.markdown("**Existing tags:**")
    for tag in tags:
        tcol1, tcol2, tcol3 = st.columns([3, 1, 1])
        with tcol1:
            color = tag.get("color", "#888888")
            st.markdown(
                f'<span style="background-color:{color};color:white;padding:2px 8px;'
                f'border-radius:4px;">{tag["name"]}</span>',
                unsafe_allow_html=True,
            )
        with tcol2:
            st.caption(color)
        with tcol3:
            if st.button("Delete", key=f"del_tag_{tag['id']}"):
                delete_tag(tag["id"])
                st.rerun()
else:
    st.caption("No tags yet.")

st.markdown("**Add a new tag:**")
with st.form("add_tag_form"):
    tag_col1, tag_col2 = st.columns(2)
    with tag_col1:
        new_tag_name = st.text_input("Tag name")
    with tag_col2:
        new_tag_color = st.color_picker("Color", "#4444FF")

    if st.form_submit_button("Add Tag"):
        if new_tag_name:
            result = create_tag({"name": new_tag_name, "color": new_tag_color})
            if result:
                st.success(f"Tag '{new_tag_name}' created!")
                st.rerun()
            else:
                st.error("Failed to create tag.")
        else:
            st.warning("Tag name is required.")

# ---------------------------------------------------------------------------
# Data export
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("Data Export")

leads = list_leads()

if leads:
    leads_json = json.dumps(leads, indent=2, default=str)
    st.download_button(
        label="Download leads as JSON",
        data=leads_json,
        file_name="leads_export.json",
        mime="application/json",
    )
else:
    st.caption("No leads to export.")
