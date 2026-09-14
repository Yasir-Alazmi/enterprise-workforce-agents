# Architecture & Engineering Design

An enterprise-grade multi-agent autonomous system built for business process automation, policy compliance enforcement, and sandboxed execution.

---

## 1. System Architecture Diagram

```
[ User / External API ] ──► [ Sliding Window Rate Limiter (200 req/min) ]
                                      │
                                      ▼
             [ Zero-Trust HMAC-SHA256 JWT Authentication & RBAC ]
             (Roles: EMPLOYEE < MANAGER < ADMIN | AUDITOR)
                                      │
                                      ▼
                       [ Injection Detector Guardrail ]
                       (Jailbreak, Mode Switch, SQL Tokens)
                                      │
                                      ▼
                        [ Central Supervisor Agent ]
                        (Goal Decomposition into DAG Queue)
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
   [ SQL Data Agent ]         [ Policy Agent ]             [ ERP Action Agent ]
   - SafeSQLTool (Read-Only)  - Delegation of Authority    - Requisition Staging
   - AST & Regex Safety       - Threshold Compliance       - Mock ERP Mutation
         │                            │                            │
         └────────────────────────────┼────────────────────────────┘
                                      │
                                      ▼
                  🔴 [ Human-in-the-Loop (HITL) Gate ]
                  (Threshold: Amount > $5,000 or Budget Overrun)
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼ (Requires Approval)                 ▼ (Compliant / Under Limit)
        [ Save Checkpoint Snapshot ]             [ Execute & Commit Action ]
        (Pause at WAITING_FOR_APPROVAL)                  │
                   │                                     │
                   ▼                                     ▼
        [ Resume on POST /approve ] ──────────► [ Executive Synthesis ]
                                                         │
                                                         ▼
                                          [ SHA-256 Audit Ledger Chain ]
                                          [ Prometheus Telemetry Export ]
```

---

## 2. Core Architectural Invariants

1. **Strict Read-Only SQL Sandboxing**:
   The SQL execution tool rejects any mutating keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, stacked statements `;`, comments `--`). Enforces row limit caps (`LIMIT 100`) and execution timeouts.
2. **Autonomous Boundaries & Human-in-the-Loop (HITL)**:
   High-risk financial actions exceeding configurable thresholds ($5,000 by default) or causing budget overruns cannot be autonomously committed. The engine serializes the complete agent state, halts execution, and requires authenticated human authorization (`approve:hitl` permission).
3. **Cryptographic Auditability**:
   Every state change, agent reasoning thought, tool parameter, and human decision is appended to a cryptographic ledger where each entry contains `SHA256(prev_hash + entry_data)`, guaranteeing tamper-evident audit trails for regulatory compliance.
4. **Offline Reproducibility**:
   Decoupled through `BaseAgentLLM`, enabling 100% test coverage and instant CI passes without network latency or external API token expenditure.
