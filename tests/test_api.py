from starlette.testclient import TestClient

ADMIN_HEADERS = {"Authorization": "Bearer token-admin-root"}
MANAGER_HEADERS = {"Authorization": "Bearer token-manager-ops"}
EMPLOYEE_HEADERS = {"Authorization": "Bearer token-employee-dev"}
AUDITOR_HEADERS = {"Authorization": "Bearer token-auditor-sec"}


def test_health_endpoint(test_client: TestClient):
    res = test_client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["db_connected"] is True
    assert "sql_agent" in data["registered_agents"]


def test_submit_task_unauthenticated_fails_401(test_client: TestClient):
    res = test_client.post("/api/v1/tasks", json={"user_goal": "Inspect marketing"})
    assert res.status_code == 401


def test_submit_task_query_workflow_success(test_client: TestClient):
    payload = {"user_goal": "Analyze budget status for Engineering department"}
    res = test_client.post("/api/v1/tasks", json=payload, headers=EMPLOYEE_HEADERS)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert len(data["tasks"]) == 1
    assert data["total_tokens_used"] > 0
    assert data["final_resolution"] is not None


def test_submit_task_high_value_procurement_pauses_for_hitl(test_client: TestClient):
    payload = {"user_goal": "Purchase $18,000 GPU cluster from ServerMax for Engineering"}
    res = test_client.post("/api/v1/tasks", json=payload, headers=EMPLOYEE_HEADERS)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "WAITING_FOR_APPROVAL"
    assert data["pending_hitl"] is not None
    assert data["pending_hitl"]["amount"] == 18000.0
    wf_id = data["workflow_id"]

    # 1. Employee attempting approval should be DENIED 403 Forbidden
    emp_appr = test_client.post(
        f"/api/v1/tasks/{wf_id}/approve",
        json={"decision": "APPROVE", "reason": "Self-approval attempt"},
        headers=EMPLOYEE_HEADERS
    )
    assert emp_appr.status_code == 403

    # 2. Manager approval should SUCCEED 200 OK
    mgr_appr = test_client.post(
        f"/api/v1/tasks/{wf_id}/approve",
        json={"decision": "APPROVE", "reason": "Approved for production compute expansion"},
        headers=MANAGER_HEADERS
    )
    assert mgr_appr.status_code == 200
    appr_data = mgr_appr.json()
    assert appr_data["status"] == "COMPLETED"
    assert appr_data["pending_hitl"]["decision"] == "APPROVE"


def test_get_workflow_audit_trail(test_client: TestClient):
    payload = {"user_goal": "Query finance department status"}
    create_res = test_client.post("/api/v1/tasks", json=payload, headers=EMPLOYEE_HEADERS)
    wf_id = create_res.json()["workflow_id"]

    trail_res = test_client.get(f"/api/v1/tasks/{wf_id}/audit-trail", headers=EMPLOYEE_HEADERS)
    assert trail_res.status_code == 200
    trail_data = trail_res.json()
    assert trail_data["workflow_id"] == wf_id
    assert trail_data["chain_verified"] is True
    assert trail_data["entry_count"] >= 2


def test_get_workflow_status_not_found_404(test_client: TestClient):
    res = test_client.get("/api/v1/tasks/wf-nonexistent-9999", headers=EMPLOYEE_HEADERS)
    assert res.status_code == 404
    assert "was not found" in res.json()["detail"]


def test_approve_non_waiting_workflow_returns_400(test_client: TestClient):
    payload = {"user_goal": "Analyze operations"}
    create_res = test_client.post("/api/v1/tasks", json=payload, headers=EMPLOYEE_HEADERS)
    wf_id = create_res.json()["workflow_id"]

    appr_res = test_client.post(
        f"/api/v1/tasks/{wf_id}/approve",
        json={"decision": "APPROVE"},
        headers=MANAGER_HEADERS
    )
    assert appr_res.status_code == 400
    assert "not currently waiting for approval" in appr_res.json()["detail"]


def test_auditor_can_read_audit_trail(test_client: TestClient):
    payload = {"user_goal": "Query marketing budget"}
    create_res = test_client.post("/api/v1/tasks", json=payload, headers=EMPLOYEE_HEADERS)
    wf_id = create_res.json()["workflow_id"]

    trail_res = test_client.get(f"/api/v1/tasks/{wf_id}/audit-trail", headers=AUDITOR_HEADERS)
    assert trail_res.status_code == 200
    assert trail_res.json()["chain_verified"] is True
