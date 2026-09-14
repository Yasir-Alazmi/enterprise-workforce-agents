import pytest

from src.agents.erp_agent import ERPActionAgent
from src.agents.policy_agent import PolicyComplianceAgent
from src.agents.sql_agent import SQLDataAgent
from src.llm.deterministic import DeterministicAgentLLM
from src.orchestration.graph import WorkforceGraphEngine
from src.orchestration.state import WorkflowStatus
from src.orchestration.supervisor import SupervisorAgent
from src.tools.erp_tool import ERPActionTool
from src.tools.policy_tool import PolicyVerificationTool
from src.tools.sql_tool import SafeSQLTool


def _build_test_engine():
    llm = DeterministicAgentLLM()
    return WorkforceGraphEngine(
        supervisor=SupervisorAgent(llm),
        agents={
            "sql_agent": SQLDataAgent(llm, SafeSQLTool()),
            "policy_agent": PolicyComplianceAgent(llm, PolicyVerificationTool()),
            "erp_agent": ERPActionAgent(llm, ERPActionTool()),
        },
        llm=llm
    )


def test_hitl_pauses_for_high_value_procurement():
    engine = _build_test_engine()
    state = engine.create_workflow("Purchase $25,000 AI servers for Engineering from ServerMax")
    paused_state = engine.run_until_complete_or_pause(state)

    assert paused_state.status == WorkflowStatus.WAITING_FOR_APPROVAL
    assert paused_state.pending_hitl is not None
    assert paused_state.pending_hitl.amount == 25000.0
    assert "HITL-" in paused_state.pending_hitl.request_id


def test_hitl_approval_decision_resumes_and_completes():
    engine = _build_test_engine()
    state = engine.create_workflow("Purchase $18,000 networking switches for Engineering from CiscoNet")
    paused_state = engine.run_until_complete_or_pause(state)

    assert paused_state.status == WorkflowStatus.WAITING_FOR_APPROVAL

    # Decision: APPROVE
    resumed = engine.process_hitl_decision(
        workflow_id=paused_state.workflow_id,
        decision="APPROVE",
        user_id="cfo_user",
        reason="Approved for Q1 data center expansion."
    )
    assert resumed.status == WorkflowStatus.COMPLETED
    assert resumed.pending_hitl.decision == "APPROVE"
    assert resumed.pending_hitl.decision_by == "cfo_user"
    assert resumed.accumulated_data.get("hitl_approved") is True


def test_hitl_rejection_decision_terminates():
    engine = _build_test_engine()
    state = engine.create_workflow("Purchase $45,000 unbudgeted monitors for Marketing from TechDisplay")
    paused_state = engine.run_until_complete_or_pause(state)

    # Decision: REJECT
    rejected = engine.process_hitl_decision(
        workflow_id=paused_state.workflow_id,
        decision="REJECT",
        user_id="finance_director",
        reason="Exceeds allowable quarterly discretionary budget."
    )
    assert rejected.status == WorkflowStatus.REJECTED
    assert "rejected by human supervisor" in rejected.final_resolution.lower()


def test_hitl_decision_on_non_waiting_workflow_raises_error():
    engine = _build_test_engine()
    state = engine.create_workflow("Query Engineering data")
    completed = engine.run_until_complete_or_pause(state)
    assert completed.status == WorkflowStatus.COMPLETED

    with pytest.raises(ValueError, match="not currently waiting for approval"):
        engine.process_hitl_decision(completed.workflow_id, "APPROVE", "admin")


def test_hitl_decision_on_nonexistent_workflow_raises_error():
    engine = _build_test_engine()
    with pytest.raises(ValueError, match="not found"):
        engine.process_hitl_decision("wf-fake-id-9999", "APPROVE", "admin")
