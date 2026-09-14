from starlette.testclient import TestClient


def test_prometheus_metrics_endpoint(test_client: TestClient):
    test_client.get("/api/v1/health")
    res = test_client.get("/api/v1/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers["content-type"]
    assert "workforce_http_requests_total" in res.text
    assert "workforce_workflow_executions_total" in res.text


def test_cors_middleware_allowed_origin(test_client: TestClient):
    res = test_client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert res.headers.get("access-control-allow-credentials") == "true"


def test_cors_middleware_disallowed_origin(test_client: TestClient):
    res = test_client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://malicious-external-site.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert res.headers.get("access-control-allow-origin") != "http://malicious-external-site.com"
