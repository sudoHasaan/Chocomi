import os
import json
import pytest
from pathlib import Path
from crm_store import get_user_info, store_user_info, update_user_info, add_interaction, CRM_FILE_PATH

# Use a temporary CRM file for testing to avoid corrupting production data
TEST_CRM_FILE = Path(__file__).parent / "test_crm_data.json"

@pytest.fixture(autouse=True)
def setup_test_crm(monkeypatch):
    """Set the CRM file path to a test file for the duration of the test."""
    monkeypatch.setattr("crm_store.CRM_FILE_PATH", TEST_CRM_FILE)
    if TEST_CRM_FILE.exists():
        TEST_CRM_FILE.unlink()
    yield
    if TEST_CRM_FILE.exists():
        TEST_CRM_FILE.unlink()

def test_store_and_get_user():
    user_id = "test_user_123"
    store_user_info(user_id, name="Test User", email="test@example.com")
    
    info = get_user_info(user_id)
    assert info["profile"]["name"] == "Test User"
    assert info["profile"]["email"] == "test@example.com"
    assert info["user_id"] == user_id

def test_update_user_field():
    user_id = "test_user_456"
    store_user_info(user_id, name="Original Name")
    
    update_user_info(user_id, "name", "Updated Name")
    info = get_user_info(user_id)
    assert info["profile"]["name"] == "Updated Name"

def test_add_interaction_history():
    user_id = "test_user_789"
    add_interaction(user_id, "User asked about GPUs")
    add_interaction(user_id, "Assistant replied with RTX 4070")
    
    info = get_user_info(user_id)
    assert len(info["history"]) == 2
    assert "User asked about GPUs" in info["history"][0]["details"]

def test_persistence():
    user_id = "persist_user"
    store_user_info(user_id, preferences="Loves RGB")
    
    # Simulate a reload by reading from the file manually
    raw = TEST_CRM_FILE.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert user_id in data["users"]
    assert data["users"][user_id]["profile"]["preferences"] == "Loves RGB"
