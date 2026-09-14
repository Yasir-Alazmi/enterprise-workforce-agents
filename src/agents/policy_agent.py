from typing import Any, Dict

from src.agents.base import BaseAgent
from src.core.logging import get_logger
from src.llm.base import BaseAgentLLM
from src.tools.policy_tool import PolicyVerificationTool

logger = get_logger(__name__)


class PolicyComplianceAgent(BaseAgent):
    """Specialist agent for evaluating corporate governance, procurement authority, and policies."""

    def __init__(self, llm: BaseAgentLLM, policy_tool: PolicyVerificationTool):
        super().__init__(name="policy_agent", role="Corporate Governance & Policy Specialist", llm=llm)
        self.register_tool(policy_tool)
        self.policy_tool = policy_tool

    def execute_task(self, task: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        tools_available = list(self.tools.keys())
        reasoning = self.llm.reason_step(self.name, task, state, tools_available)

        action_type = reasoning.action_input.get("action_type", "procurement")
        payload = reasoning.action_input.get("payload", {})

        logger.info("[PolicyAgent] Evaluating policy compliance for %s: %s", action_type, payload)
        tool_res = self.policy_tool.execute(action_type=action_type, payload=payload)

        return {
            "agent": self.name,
            "action": reasoning.action or "verify_policy_compliance",
            "thought": reasoning.thought,
            "success": tool_res.success,
            "data": tool_res.data,
            "error": tool_res.error,
            "tokens_used": reasoning.usage.get("total_tokens", 0)
        }
