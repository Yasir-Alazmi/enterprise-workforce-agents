from typing import Any, Dict

from src.agents.base import BaseAgent
from src.core.logging import get_logger
from src.llm.base import BaseAgentLLM
from src.tools.erp_tool import ERPActionTool

logger = get_logger(__name__)


class ERPActionAgent(BaseAgent):
    """Specialist agent for preparing and staging ERP fulfillment actions."""

    def __init__(self, llm: BaseAgentLLM, erp_tool: ERPActionTool):
        super().__init__(name="erp_agent", role="Enterprise Operations & ERP Specialist", llm=llm)
        self.register_tool(erp_tool)
        self.erp_tool = erp_tool

    def execute_task(self, task: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        tools_available = list(self.tools.keys())
        reasoning = self.llm.reason_step(self.name, task, state, tools_available)

        inp = reasoning.action_input
        logger.info("[ERPAgent] Staging action: %s for %s", inp.get("action"), inp.get("vendor_name"))
        tool_res = self.erp_tool.execute(
            action=inp.get("action", "create_po"),
            department_id=inp.get("department_id", "DEP-ENG"),
            vendor_name=inp.get("vendor_name", "Vendor"),
            amount=float(inp.get("amount", 0.0)),
            description=inp.get("description", "Requisition"),
            requires_hitl=inp.get("requires_hitl", False),
            approved=inp.get("approved", False)
        )

        return {
            "agent": self.name,
            "action": reasoning.action or "stage_erp_action",
            "thought": reasoning.thought,
            "success": tool_res.success,
            "data": tool_res.data,
            "error": tool_res.error,
            "tokens_used": reasoning.usage.get("total_tokens", 0)
        }
