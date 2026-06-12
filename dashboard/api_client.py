"""Shared HTTP client for the Streamlit dashboard to call the FastAPI backend."""

import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "changeme-generate-a-strong-key")

HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def _handle_response(response: httpx.Response) -> dict | list:
    """Raise user-friendly errors for non-2xx responses."""
    if response.status_code == 401:
        st.error("API authentication failed. Check your API_KEY.")
        return {}
    if response.status_code == 404:
        return {}
    response.raise_for_status()
    if response.status_code == 204:
        return {}
    return response.json()


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------

def list_companies() -> list[dict]:
    r = httpx.get(f"{API_BASE_URL}/api/companies/", headers=HEADERS, timeout=10)
    return _handle_response(r) or []


def get_company(company_id: str) -> dict:
    r = httpx.get(f"{API_BASE_URL}/api/companies/{company_id}", headers=HEADERS, timeout=10)
    return _handle_response(r) or {}


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------

def list_contacts(company_id: str | None = None) -> list[dict]:
    params = {}
    if company_id:
        params["company_id"] = company_id
    r = httpx.get(f"{API_BASE_URL}/api/contacts/", headers=HEADERS, params=params, timeout=10)
    return _handle_response(r) or []


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

def list_leads(status: str | None = None) -> list[dict]:
    params = {}
    if status:
        params["status"] = status
    r = httpx.get(f"{API_BASE_URL}/api/leads/", headers=HEADERS, params=params, timeout=10)
    return _handle_response(r) or []


def get_lead(lead_id: str) -> dict:
    r = httpx.get(f"{API_BASE_URL}/api/leads/{lead_id}", headers=HEADERS, timeout=10)
    return _handle_response(r) or {}


def create_lead(data: dict) -> dict:
    r = httpx.post(f"{API_BASE_URL}/api/leads/", headers=HEADERS, json=data, timeout=10)
    return _handle_response(r) or {}


def update_lead(lead_id: str, data: dict) -> dict:
    r = httpx.patch(f"{API_BASE_URL}/api/leads/{lead_id}", headers=HEADERS, json=data, timeout=10)
    return _handle_response(r) or {}


# ---------------------------------------------------------------------------
# Interactions
# ---------------------------------------------------------------------------

def list_interactions(lead_id: str | None = None, type_filter: str | None = None) -> list[dict]:
    params = {}
    if lead_id:
        params["lead_id"] = lead_id
    if type_filter:
        params["type"] = type_filter
    r = httpx.get(
        f"{API_BASE_URL}/api/interactions/", headers=HEADERS, params=params, timeout=10
    )
    return _handle_response(r) or []


def create_interaction(data: dict) -> dict:
    r = httpx.post(f"{API_BASE_URL}/api/interactions/", headers=HEADERS, json=data, timeout=10)
    return _handle_response(r) or {}


# ---------------------------------------------------------------------------
# Deals
# ---------------------------------------------------------------------------

def list_deals() -> list[dict]:
    r = httpx.get(f"{API_BASE_URL}/api/deals/", headers=HEADERS, timeout=10)
    return _handle_response(r) or []


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

def list_tags() -> list[dict]:
    r = httpx.get(f"{API_BASE_URL}/api/tags/", headers=HEADERS, timeout=10)
    return _handle_response(r) or []


def create_tag(data: dict) -> dict:
    r = httpx.post(f"{API_BASE_URL}/api/tags/", headers=HEADERS, json=data, timeout=10)
    return _handle_response(r) or {}


def delete_tag(tag_id: str) -> dict:
    r = httpx.delete(f"{API_BASE_URL}/api/tags/{tag_id}", headers=HEADERS, timeout=10)
    return _handle_response(r)


# ---------------------------------------------------------------------------
# Chat (RAG)
# ---------------------------------------------------------------------------

def chat_query(question: str, top_k: int = 10) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/api/chat/",
        headers=HEADERS,
        json={"question": question, "top_k": top_k},
        timeout=120,
    )
    return _handle_response(r) or {"answer": "No response", "sources": []}


# ---------------------------------------------------------------------------
# Integrations
# ---------------------------------------------------------------------------

def gmail_status() -> dict:
    r = httpx.get(f"{API_BASE_URL}/api/integrations/gmail/status", headers=HEADERS, timeout=10)
    return _handle_response(r) or {}


def gmail_authorize_url() -> str:
    r = httpx.get(f"{API_BASE_URL}/api/integrations/gmail/authorize", headers=HEADERS, timeout=10)
    data = _handle_response(r) or {}
    return data.get("auth_url", "")


def sync_gmail() -> dict:
    r = httpx.post(f"{API_BASE_URL}/api/integrations/gmail/sync", headers=HEADERS, timeout=60)
    return _handle_response(r) or {}


def import_linkedin_connections(csv_bytes: bytes, filename: str) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/api/integrations/linkedin/import/connections",
        headers=HEADERS,
        files={"file": (filename, csv_bytes, "text/csv")},
        timeout=60,
    )
    return _handle_response(r) or {}


def import_linkedin_messages(csv_bytes: bytes, filename: str) -> dict:
    r = httpx.post(
        f"{API_BASE_URL}/api/integrations/linkedin/import/messages",
        headers=HEADERS,
        files={"file": (filename, csv_bytes, "text/csv")},
        timeout=60,
    )
    return _handle_response(r) or {}
