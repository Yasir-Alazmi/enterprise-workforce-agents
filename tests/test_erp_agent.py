from src.tools.erp_tool import ERPActionTool


def test_erp_staging_requiring_hitl():
    tool = ERPActionTool()
    res = tool.execute(
        action="create_po",
        department_id="DEP-ENG",
        vendor_name="CloudHost Inc",
        amount=15000.0,
        description="GPU instances",
        requires_hitl=True,
        approved=False
    )
    assert res.success is True
    assert res.data["status"] == "STAGED_PENDING_APPROVAL"
    assert res.data["requires_hitl"] is True
    assert "PO-REQ-" in res.data["order_id"]


def test_erp_committing_after_hitl_approval():
    tool = ERPActionTool()
    res = tool.execute(
        action="create_po",
        department_id="DEP-ENG",
        vendor_name="CloudHost Inc",
        amount=15000.0,
        description="GPU instances",
        requires_hitl=True,
        approved=True
    )
    assert res.success is True
    assert res.data["status"] == "COMMITTED"
    assert res.data["requires_hitl"] is False
