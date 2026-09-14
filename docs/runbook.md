# Operations & Day-2 Runbook

## 1. Production Health Probes & Readiness
- **Liveness Probe**: `GET /api/v1/health` (HTTP 200)
- **Prometheus Telemetry**: `GET /api/v1/metrics`

## 2. Human-in-the-Loop Operations
When a workflow enters `WAITING_FOR_APPROVAL`:
1. The supervisor receives the `workflow_id` and `request_id`.
2. Inspect details:
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/tasks/{workflow_id}
   ```
3. Authorize or reject:
   ```bash
   curl -X POST http://localhost:8000/api/v1/tasks/{workflow_id}/approve \
     -H "Authorization: Bearer <manager_token>" \
     -H "Content-Type: application/json" \
     -d '{"decision": "APPROVE", "reason": "Authorized by VP of Engineering"}'
   ```

## 3. Cryptographic Audit Trail Verification
To verify the integrity of an execution trail:
```bash
curl -H "Authorization: Bearer <auditor_token>" http://localhost:8000/api/v1/tasks/{workflow_id}/audit-trail
```
Ensure `chain_verified` is `true`. If `false`, inspect `integrity_error` for tampering.
