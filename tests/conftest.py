from pathlib import Path

import pytest
from starlette.testclient import TestClient

from scripts.seed_enterprise_db import seed_db, seed_policies
from src.api.main import app

# Ensure enterprise test database is seeded before running tests
db_file = Path(__file__).resolve().parent.parent / "data" / "enterprise_db.sqlite"
if not db_file.exists():
    seed_db()
    seed_policies()

ADMIN_HEADERS = {"Authorization": "Bearer token-admin-root"}
MANAGER_HEADERS = {"Authorization": "Bearer token-manager-ops"}
EMPLOYEE_HEADERS = {"Authorization": "Bearer token-employee-dev"}
AUDITOR_HEADERS = {"Authorization": "Bearer token-auditor-sec"}


@pytest.fixture
def test_client():
    with TestClient(app) as client:
        yield client
