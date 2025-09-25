import pytest
from starlette.testclient import TestClient

from backend import app


@pytest.fixture
def client():
    """Test client for HTTP request tests."""

    with TestClient(app) as test_client:
        yield test_client


def test_status(client):
    response = client.get("/status")
    assert response.status_code == 204
