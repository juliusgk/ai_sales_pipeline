"""Chat Assistant — ask natural language questions about your sales pipeline."""

import streamlit as st

from dashboard.api_client import chat_query

st.set_page_config(page_title="Chat Assistant", page_icon="\U0001f916", layout="wide")
st.title("\U0001f916 Chat Assistant")
st.caption("Ask questions about your leads, contacts, interactions, and deals.")

# ---------------------------------------------------------------------------
# Initialize chat history
# ---------------------------------------------------------------------------

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ---------------------------------------------------------------------------
# Suggested questions
# ---------------------------------------------------------------------------

st.markdown("**Suggested questions:**")
suggestions = [
    "Who needs a follow-up this week?",
    "Summarize my current pipeline",
    "What happened with Acme Corp recently?",
    "Which leads are on hold and why?",
    "What are my highest-value opportunities?",
]

suggestion_cols = st.columns(len(suggestions))
for i, (col, suggestion) in enumerate(zip(suggestion_cols, suggestions)):
    with col:
        if st.button(suggestion, key=f"suggest_{i}", use_container_width=True):
            st.session_state.pending_question = suggestion

st.markdown("---")

# ---------------------------------------------------------------------------
# Chat history display
# ---------------------------------------------------------------------------

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for src in msg["sources"]:
                    st.caption(f"{src['source_type']} (score: {src['score']:.3f})")

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

# Check for pending suggestion
pending = st.session_state.pop("pending_question", None)
user_input = st.chat_input("Ask about your pipeline...")

question = pending or user_input

if question:
    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = chat_query(question)
                answer = result.get("answer", "No response received.")
                sources = result.get("sources", [])
            except Exception as e:
                answer = (
                    f"Failed to get a response. Ensure Ollama is running and models are pulled.\n\n"
                    f"Error: {str(e)}"
                )
                sources = []

        st.markdown(answer)
        if sources:
            with st.expander("Sources"):
                for src in sources:
                    st.caption(f"{src['source_type']} (score: {src['score']:.3f})")

    # Save assistant message
    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })

# ---------------------------------------------------------------------------
# Clear chat button
# ---------------------------------------------------------------------------

if st.session_state.chat_messages:
    st.markdown("---")
    if st.button("Clear chat history"):
        st.session_state.chat_messages = []
        st.rerun()
