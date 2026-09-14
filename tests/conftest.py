import pytest
from starlette.testclient import TestClient

from src.api.main import app

ADMIN_HEADERS = {"Authorization": "Bearer token-admin-root"}
MANAGER_HEADERS = {"Authorization": "Bearer token-manager-ops"}
EMPLOYEE_HEADERS = {"Authorization": "Bearer token-employee-dev"}
AUDITOR_HEADERS = {"Authorization": "Bearer token-auditor-sec"}


@pytest.fixture
def test_client():
    with TestClient(app) as client:
        yield client
