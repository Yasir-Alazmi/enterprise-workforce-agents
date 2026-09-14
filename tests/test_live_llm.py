from src.llm.deterministic import DeterministicAgentLLM
from src.llm.live_llm import LiveAgentLLM, get_agent_llm


def test_get_agent_llm_factory():
    det = get_agent_llm("deterministic")
    assert isinstance(det, DeterministicAgentLLM)

    live = get_agent_llm("openai")
    assert isinstance(live, LiveAgentLLM)


def test_live_agent_llm_fallback_behavior():
    live_adapter = LiveAgentLLM()
    plan = live_adapter.plan_workflow("Purchase $5,000 laptops for Marketing")
    assert len(plan) >= 2

    response = live_adapter.reason_step(
        agent_name="sql_agent",
        current_task={"action": "query", "target_department": "DEP-MKT"},
        accumulated_state={},
        tools_available=["safe_sql_query"]
    )
    assert response.action == "safe_sql_query"
    assert "query" in response.action_input
    assert response.usage["total_tokens"] > 0
