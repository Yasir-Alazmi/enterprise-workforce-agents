import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
POLICIES_DIR = DATA_DIR / "policies"
POLICIES_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "enterprise_db.sqlite"


def seed_db():
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE departments (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        manager_id TEXT NOT NULL,
        budget_annual REAL NOT NULL,
        budget_spent REAL NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE employees (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department_id TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT NOT NULL,
        salary REAL NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE procurement_orders (
        id TEXT PRIMARY KEY,
        department_id TEXT NOT NULL,
        vendor_name TEXT NOT NULL,
        item_description TEXT NOT NULL,
        amount REAL NOT NULL,
        status TEXT NOT NULL,
        approved_by TEXT,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        action_type TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        details TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)

    departments = [
        ("DEP-ENG", "Engineering", "EMP-001", 1200000.0, 850000.0),
        ("DEP-MKT", "Marketing", "EMP-002", 600000.0, 420000.0),
        ("DEP-FIN", "Finance", "EMP-003", 400000.0, 210000.0),
        ("DEP-HR", "Human Resources", "EMP-004", 300000.0, 190000.0),
        ("DEP-OPS", "Operations", "EMP-005", 900000.0, 680000.0),
    ]
    cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?, ?)", departments)

    employees = [
        ("EMP-001", "Faisal Al-Otaibi", "DEP-ENG", "VP Engineering", "faisal@enterprise.com", 145000.0, "ACTIVE"),
        ("EMP-002", "Reem Al-Qahtani", "DEP-MKT", "Marketing Director", "reem@enterprise.com", 115000.0, "ACTIVE"),
        ("EMP-003", "Omar Al-Harbi", "DEP-FIN", "Chief Financial Officer", "omar@enterprise.com", 160000.0, "ACTIVE"),
        ("EMP-004", "Noura Al-Dosari", "DEP-HR", "HR Director", "noura@enterprise.com", 110000.0, "ACTIVE"),
        ("EMP-005", "Khalid Al-Ghamdi", "DEP-OPS", "Head of Operations", "khalid@enterprise.com", 125000.0, "ACTIVE"),
        ("EMP-006", "Sara Al-Shehri", "DEP-ENG", "Senior AI Engineer", "sara@enterprise.com", 95000.0, "ACTIVE"),
        ("EMP-007", "Tariq Al-Mutairi", "DEP-ENG", "DevOps Specialist", "tariq@enterprise.com", 85000.0, "ACTIVE"),
        ("EMP-008", "Mona Al-Zahrani", "DEP-FIN", "Financial Analyst", "mona@enterprise.com", 70000.0, "ACTIVE"),
    ]
    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)", employees)

    procurements = [
        ("PO-2026-001", "DEP-ENG", "CloudCompute Inc", "GPU Compute Cluster Lease (H100 8x)", 24000.0, "APPROVED", "EMP-003", "2026-01-15 10:00:00"),
        ("PO-2026-002", "DEP-ENG", "VectorDB Corp", "Managed Dedicated Vector Search Instance", 4800.0, "COMPLETED", "EMP-001", "2026-02-10 14:30:00"),
        ("PO-2026-003", "DEP-MKT", "AdMedia Agency", "Q1 Omnichannel Campaign Launch", 18500.0, "APPROVED", "EMP-003", "2026-02-28 09:15:00"),
        ("PO-2026-004", "DEP-OPS", "DataCenter Hub", "Server Rack Power Redundancy Upgrade", 12000.0, "COMPLETED", "EMP-005", "2026-03-05 11:20:00"),
    ]
    cursor.executemany("INSERT INTO procurement_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)", procurements)

    conn.commit()
    conn.close()
    print(f"Database seeded successfully at: {DB_PATH}")


def seed_policies():
    procurement_policy = {
        "policy_id": "POL-PROC-001",
        "title": "Corporate Procurement and Financial Delegation of Authority",
        "version": "2.4",
        "effective_date": "2026-01-01",
        "rules": [
            {
                "rule_id": "RULE-001",
                "condition": "amount <= 1000",
                "max_amount": 1000.0,
                "approval_required": "EMPLOYEE_EXPENSE",
                "description": "Standard operational expenses under $1,000 can be expensed directly."
            },
            {
                "rule_id": "RULE-002",
                "condition": "1000 < amount <= 5000",
                "max_amount": 5000.0,
                "approval_required": "DEPARTMENT_MANAGER",
                "description": "Purchases between $1,000 and $5,000 require Department Manager sign-off."
            },
            {
                "rule_id": "RULE-003",
                "condition": "amount > 5000",
                "max_amount": 50000.0,
                "approval_required": "CFO_EXECUTIVE_APPROVAL",
                "requires_hitl": True,
                "description": "Any purchase order exceeding $5,000 strictly requires Executive CFO approval via Human-in-the-Loop gateway."
            },
            {
                "rule_id": "RULE-004",
                "condition": "budget_spent + amount > budget_annual",
                "approval_required": "BUDGET_OVERRUN_EXCEPTION",
                "requires_hitl": True,
                "description": "Any purchase exceeding annual allocated department budget is blocked unless exception granted."
            }
        ]
    }
    (POLICIES_DIR / "procurement_policy.json").write_text(json.dumps(procurement_policy, indent=2), encoding="utf-8")

    travel_policy = {
        "policy_id": "POL-TRV-002",
        "title": "Corporate Travel & Expense Reimbursement Policy",
        "version": "1.8",
        "effective_date": "2026-01-01",
        "rules": [
            {
                "rule_id": "TRV-001",
                "max_daily_lodging": 350.0,
                "max_daily_meals": 120.0,
                "flight_class": "ECONOMY",
                "requires_preapproval": True,
                "description": "International travel requires minimum 14 days advance departmental approval."
            }
        ]
    }
    (POLICIES_DIR / "travel_policy.json").write_text(json.dumps(travel_policy, indent=2), encoding="utf-8")

    print(f"Policies seeded successfully in: {POLICIES_DIR}")


if __name__ == "__main__":
    seed_db()
    seed_policies()
