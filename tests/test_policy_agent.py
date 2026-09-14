from src.tools.policy_tool import PolicyVerificationTool


def test_policy_procurement_under_threshold():
    tool = PolicyVerificationTool()
    res = tool.execute("procurement", {
        "amount": 800.0,
        "budget_spent": 10000.0,
        "budget_annual": 100000.0
    })
    assert res.success is True
    assert res.data["compliant"] is True
    assert res.data["requires_hitl"] is False
    assert res.data["approval_level"] == "EMPLOYEE_EXPENSE"


def test_policy_procurement_mid_tier_manager():
    tool = PolicyVerificationTool()
    res = tool.execute("procurement", {
        "amount": 3500.0,
        "budget_spent": 20000.0,
        "budget_annual": 100000.0
    })
    assert res.success is True
    assert res.data["compliant"] is True
    assert res.data["requires_hitl"] is False
    assert res.data["approval_level"] == "DEPARTMENT_MANAGER"


def test_policy_procurement_high_tier_hitl_required():
    tool = PolicyVerificationTool()
    res = tool.execute("procurement", {
        "amount": 18000.0,
        "budget_spent": 50000.0,
        "budget_annual": 200000.0
    })
    assert res.success is True
    assert res.data["requires_hitl"] is True
    assert res.data["approval_level"] == "CFO_EXECUTIVE_APPROVAL"


def test_policy_budget_overrun_detection():
    tool = PolicyVerificationTool()
    res = tool.execute("procurement", {
        "amount": 60000.0,
        "budget_spent": 95000.0,
        "budget_annual": 100000.0
    })
    assert res.success is True
    assert res.data["compliant"] is False
    assert res.data["requires_hitl"] is True
    assert "Budget overrun" in res.data["violations"][0]


def test_policy_travel_evaluation():
    tool = PolicyVerificationTool()
    res_compliant = tool.execute("travel", {"daily_lodging": 280.0})
    assert res_compliant.success is True
    assert res_compliant.data["compliant"] is True
    assert res_compliant.data["requires_hitl"] is False

    res_excess = tool.execute("travel", {"daily_lodging": 450.0})
    assert res_excess.success is True
    assert res_excess.data["compliant"] is False
    assert res_excess.data["requires_hitl"] is True


def test_policy_unrecognized_action_fails():
    tool = PolicyVerificationTool()
    res = tool.execute("unrecognized_corporate_action", {})
    assert res.success is False
    assert "Unrecognized policy evaluation action type" in res.error


def test_policy_extreme_budget_overrun():
    tool = PolicyVerificationTool()
    res = tool.execute("procurement", {
        "amount": 500000.0,
        "budget_spent": 1100000.0,
        "budget_annual": 1200000.0
    })
    assert res.success is True
    assert res.data["compliant"] is False
    assert res.data["requires_hitl"] is True
    assert res.data["approval_level"] == "BUDGET_OVERRUN_EXCEPTION"
