from src.llm.deterministic import DeterministicAgentLLM
from src.orchestration.supervisor import SupervisorAgent


def test_supervisor_decomposes_procurement_goal():
    llm = DeterministicAgentLLM()
    supervisor = SupervisorAgent(llm)
    tasks = supervisor.plan_workflow("Purchase $15,000 server equipment for Engineering from HardwareDirect")

    assert len(tasks) == 3
    assert tasks[0].agent == "sql_agent"
    assert tasks[1].agent == "policy_agent"
    assert tasks[2].agent == "erp_agent"
    assert tasks[0].metadata["target_department"] == "DEP-ENG"
    assert tasks[1].metadata["target_amount"] == 15000.0


def test_supervisor_inspect_data_goal():
    llm = DeterministicAgentLLM()
    supervisor = SupervisorAgent(llm)
    tasks = supervisor.plan_workflow("Analyze marketing department budget and expenditures")

    assert len(tasks) == 1
    assert tasks[0].agent == "sql_agent"
    assert tasks[0].metadata["target_department"] == "DEP-MKT"


def test_supervisor_unmatched_goal_fallback():
    llm = DeterministicAgentLLM()
    supervisor = SupervisorAgent(llm)
    tasks = supervisor.plan_workflow("Generic inquiry about general corporate data")
    assert len(tasks) >= 1
    assert tasks[0].agent == "sql_agent"


def test_supervisor_hr_department_goal():
    llm = DeterministicAgentLLM()
    supervisor = SupervisorAgent(llm)
    tasks = supervisor.plan_workflow("Inspect Human Resources employee payroll status")
    assert len(tasks) == 1
    assert tasks[0].metadata["target_department"] == "DEP-HR"


def test_supervisor_operations_goal():
    llm = DeterministicAgentLLM()
    supervisor = SupervisorAgent(llm)
    tasks = supervisor.plan_workflow("Order $3,500 replacement cooling fans for Operations from FanCo")
    assert len(tasks) == 3
    assert tasks[0].metadata["target_department"] == "DEP-OPS"
    assert tasks[1].metadata["target_amount"] == 3500.0
