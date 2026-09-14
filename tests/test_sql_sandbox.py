from src.tools.sql_tool import SafeSQLTool


def test_sql_sandbox_select_query():
    tool = SafeSQLTool()
    res = tool.execute("SELECT id, name, budget_annual FROM departments WHERE id = 'DEP-ENG'")
    assert res.success is True
    assert len(res.data) == 1
    assert res.data[0]["name"] == "Engineering"
    assert res.metadata["row_count"] == 1
    assert res.metadata["execution_ms"] >= 0.0


def test_sql_sandbox_blocks_forbidden_mutations():
    tool = SafeSQLTool()
    forbidden_queries = [
        "DELETE FROM employees WHERE id = 'EMP-001'",
        "DROP TABLE departments",
        "UPDATE departments SET budget_annual = 9999999",
        "INSERT INTO departments VALUES ('DEP-HACK', 'Hack', 'EMP-01', 100, 100)",
        "TRUNCATE TABLE procurement_orders",
        "ALTER TABLE employees ADD COLUMN ssn TEXT",
        "SELECT * FROM departments; DROP TABLE employees;",
        "SELECT * FROM departments -- SQL comment injection",
    ]
    for q in forbidden_queries:
        res = tool.execute(q)
        assert res.success is False
        assert "Security Violation" in res.error


def test_sql_sandbox_blocks_non_select():
    tool = SafeSQLTool()
    res = tool.execute("SHOW TABLES")
    assert res.success is False
    assert "Only SELECT queries are permitted" in res.error


def test_sql_sandbox_schema_introspection():
    tool = SafeSQLTool()
    schema = tool.get_schema()
    assert "departments" in schema
    assert "employees" in schema
    assert "procurement_orders" in schema
    assert "audit_logs" in schema
    assert any("budget_annual" in col for col in schema["departments"])


def test_sql_sandbox_nonexistent_table():
    tool = SafeSQLTool()
    res = tool.execute("SELECT * FROM imaginary_enterprise_table")
    assert res.success is False
    assert "no such table" in res.error.lower()


def test_sql_sandbox_empty_result():
    tool = SafeSQLTool()
    res = tool.execute("SELECT * FROM employees WHERE id = 'EMP-NONEXISTENT'")
    assert res.success is True
    assert len(res.data) == 0
    assert res.metadata["row_count"] == 0


def test_sql_sandbox_custom_max_rows():
    tool = SafeSQLTool()
    res = tool.execute("SELECT * FROM employees", max_rows=2)
    assert res.success is True
    assert len(res.data) == 2
