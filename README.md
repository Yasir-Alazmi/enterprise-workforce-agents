# Enterprise Workforce Multi-Agent Orchestrator

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-E6522C?style=flat-square&logo=prometheus&logoColor=white)](https://prometheus.io/)

An enterprise reference architecture and production platform for autonomous multi-agent business process automation. Built for high-security enterprise operations requiring deterministic state graphs, sandboxed read-only database query tools, Human-in-the-Loop (HITL) authorization gateways, zero-trust RBAC, and SHA-256 tamper-evident cryptographic audit ledgers.

---

## Architecture Blueprint

```
[ Client Request ] ──► [ Sliding Window Rate Limiter (200 req/min) ]
                               │
                               ▼
        [ Zero-Trust Bearer Token & JWT Verification Engine ]
        (Roles: EMPLOYEE < MANAGER < ADMIN | AUDITOR)
                               │
                               ▼
        [ Injection Detector & System Boundary Guardrail ]
                               │
                               ▼
            [ Central Supervisor Agent & DAG Planner ]
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
  [ SQL Data Agent ]    [ Policy Agent ]       [ ERP Agent ]
  (Sandboxed Queries)   (Rules & Compliance)   (Requisition Staging)
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
            🔴 [ Human-in-the-Loop (HITL) Gate ]
            (Amount > $5,000 / Budget Overrun Exception)
                               │
        ┌──────────────────────┴──────────────────────┐
        ▼ (Requires Approval)                         ▼ (Compliant)
   [ Atomic Checkpoint ]                      [ Commit Action ]
   (Pause: WAITING_FOR_APPROVAL)                      │
        │                                             ▼
        ▼                                    [ Executive Summary ]
   [ POST /approve ] ────────────────────────►        │
                                                      ▼
                                       [ Cryptographic Audit Ledger ]
                                       [ Prometheus Stage Telemetry ]
```

---

## Core Engineering Capabilities

### 1. Multi-Agent Orchestration & Deterministic Graph (`src/orchestration/`)
- **Supervisor Agent**: Decomposes high-level business goals into directed acyclic task queues (`TaskItem`).
- **Domain Worker Agents**:
  - `SQLDataAgent`: Sandboxed enterprise database queries with automatic schema introspection.
  - `PolicyComplianceAgent`: Evaluates procurement and expense rules against formal corporate delegations of authority.
  - `ERPActionAgent`: Prepares and stages operational requisitions.
- **Deterministic State Engine**: Strongly-typed `AgentState` transition machine with error recovery and cycle prevention.

### 2. Human-in-the-Loop (HITL) Approval Gateway & Checkpoints (`src/orchestration/checkpoint.py`)
- **Configurable Risk Thresholds**: Automatically pauses execution when financial commitments exceed policy limits (e.g. > $5,000) or violate department budgets.
- **Atomic State Checkpointing**: Serializes running workflow state to atomic JSON/disk storage (`data/checkpoints/`) upon pause.
- **Authorized Decision Gateway**: `POST /api/v1/tasks/{id}/approve` strictly enforces `MANAGER` or `ADMIN` clearance before resuming execution and committing ERP actions.

### 3. Sandboxed Defense-in-Depth Tools (`src/tools/`)
- **`SafeSQLTool`**: Strictly read-only SQLite execution. Rejects forbidden tokens (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, multi-statement `;`, and comments `--`). Enforces row capping and timeouts.
- **`PolicyVerificationTool`**: Evaluates corporate delegation of authority policies (`data/policies/`).
- **`ERPActionTool`**: Staged requisition drafting with dry-run verification.

### 4. Cryptographic Audit Ledger & Security (`src/guardrails/`, `src/core/security.py`)
- **Tamper-Evident SHA-256 Ledger**: Every state transition, thought, and decision is hashed in an append-only chain where each block cryptographically links to `prev_hash`.
- **Adversarial Injection Screening**: Heuristic scanner intercepting system prompt overrides, mode switches, and jailbreaks.
- **Zero-Trust JWT Verification**: HMAC-SHA256 signature verification with role-based permissions (`ROLE_PERMISSIONS`).
- **Restricted CORS Policy**: Configurable allowed origins, explicit HTTP methods, and header filtering.

---

## Empirical Benchmark & Evaluation Results

### Performance Benchmark (`scripts/benchmark_workflow.py`)
Measured across 100 consecutive requests on Windows (AMD64, Python 3.13):

| Workflow Type | p50 Latency (Median) | p95 Latency | Automated Test Suite |
| :--- | :--- | :--- | :--- |
| **Single-Agent Data Query Workflow** | **1.21 ms** | **1.64 ms** | **58 / 58 Passed (100%)** |
| **Full HITL Multi-Agent Requisition Workflow** | **2.85 ms** | **3.42 ms** | 12 Test Suites |

### Automated System Evaluation Report (`scripts/evaluate_agents.py`)
Evaluated across diverse enterprise scenarios:

| Evaluation Metric | Aggregate Score | Target SLA |
| :--- | :--- | :--- |
| **Task Routing Accuracy** | **1.000 (100%)** | > 0.95 |
| **HITL Gating Fidelity** | **1.000 (100%)** | 1.00 (Zero Missed Authorizations) |
| **Safety Violation Prevention Rate** | **1.000 (100%)** | 1.00 (Zero Jailbreak Leaks) |
| **Overall Multi-Agent System Fidelity** | **1.000 (100%)** | > 0.98 |

---

## Directory Structure

```
enterprise-workforce-agents/
├── .github/workflows/ci.yml       # GitHub Actions CI matrix (Python 3.10 & 3.11)
├── configs/config.yaml            # Hyperparameters, security thresholds, and CORS
├── data/
│   ├── enterprise_db.sqlite      # Enterprise SQL database (departments, employees, POs)
│   └── policies/                 # Corporate delegation of authority & travel policies
├── docs/
│   ├── architecture.md           # Detailed multi-agent graph architecture and trade-offs
│   └── runbook.md                # Day-2 operations, HITL approval procedures, and runbooks
├── results/
│   ├── benchmark_report.json     # Empirical latency percentiles (p50/p95/p99)
│   └── evaluation_report.json    # Routing accuracy, HITL fidelity, and safety metrics
├── scripts/
│   ├── benchmark_workflow.py     # Performance benchmark harness
│   ├── evaluate_agents.py        # Multi-agent system evaluation harness
│   └── seed_enterprise_db.py     # Deterministic enterprise database seed script
├── src/
│   ├── api/                      # FastAPI routes, schemas, and rate-limiting middleware
│   ├── core/                     # JWT security, zero-trust RBAC, Prometheus metrics
│   ├── orchestration/            # State machine graph, checkpointing, and supervisor
│   ├── agents/                   # Specialized domain agents (SQL, Policy, ERP)
│   ├── tools/                    # Sandboxed read-only SQL, policy evaluator, and ERP tool
│   ├── llm/                      # Pluggable LLM interface (Deterministic + Live adapters)
│   └── guardrails/               # Adversarial injection detector and SHA-256 audit ledger
├── tests/                        # 58 automated tests across 12 test suites (100% passing)
├── pyproject.toml                # Build system & pytest configuration
└── requirements.txt              # Pinned dependencies
```

---

## Quickstart Guide

### 1. Installation
```bash
git clone https://github.com/Yasir-Alazmi/enterprise-workforce-agents.git
cd enterprise-workforce-agents
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Test Suite (58 Tests)
```bash
python -m pytest tests/ -v
```

### 3. Run Evaluation Harness
```bash
python scripts/evaluate_agents.py
```

### 4. Run Performance Benchmark
```bash
python scripts/benchmark_workflow.py
```

### 5. Start Production API Server
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- Prometheus Operational Metrics: `http://localhost:8000/api/v1/metrics`
- Health Probe: `http://localhost:8000/api/v1/health`

### 6. Workflow cURL Examples

```bash
# 1. Submit Multi-Agent Requisition Workflow (Employee Bearer Token)
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer token-employee-dev" \
  -d '{"user_goal": "Purchase $18,000 GPU compute cluster for Engineering from ServerMax"}'

# 2. Authorize High-Value Requisition via Human-in-the-Loop Gateway (Manager/Admin Bearer Token)
curl -X POST http://localhost:8000/api/v1/tasks/<workflow_id>/approve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer token-manager-ops" \
  -d '{"decision": "APPROVE", "reason": "Approved for Q1 engineering compute expansion."}'

# 3. Verify Cryptographic SHA-256 Audit Trail (Auditor/Admin Bearer Token)
curl -X GET http://localhost:8000/api/v1/tasks/<workflow_id>/audit-trail \
  -H "Authorization: Bearer token-auditor-sec"
```

---

## Author & Contact

**Yasir Alazmi**  
Artificial Intelligence Engineer  
- Email: [yasir.alazmi@outlook.sa](mailto:yasir.alazmi@outlook.sa)  
- LinkedIn: [yasir-alazmi-471832436](https://www.linkedin.com/in/yasir-alazmi-471832436)  
- GitHub: [Yasir-Alazmi](https://github.com/Yasir-Alazmi)
