import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Mock dependency to bypass organization extraction (returns a fixed org id)
# Assuming get_current_organization_id is defined using Depends, we can override it via app.dependency_overrides
from app.dependencies import get_current_organization_id

def override_get_org_id():
    return 1  # dummy organization id for tests

app.dependency_overrides[get_current_organization_id] = override_get_org_id


def test_chat_with_strategy_agent():
    response = client.post(
        "/api/agents/strategy/chat",
        json={"message": "What is the growth strategy?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent"] == "strategy"
    assert "reply" in data
    assert "Strategy insight" in data["reply"]

def test_chat_with_unknown_agent():
    response = client.post(
        "/api/agents/unknown/chat",
        json={"message": "test"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Agent 'unknown' not found"
