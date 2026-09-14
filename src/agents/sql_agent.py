from typing import Any, Dict

from src.agents.base import BaseAgent
from src.core.logging import get_logger
from src.llm.base import BaseAgentLLM
from src.tools.sql_tool import SafeSQLTool

logger = get_logger(__name__)


class SQLDataAgent(BaseAgent):
    """Specialist agent for data analysis, schema inspection, and sandboxed SQL querying."""

    def __init__(self, llm: BaseAgentLLM, sql_tool: SafeSQLTool):
        super().__init__(name="sql_agent", role="Enterprise Data & Analytics Specialist", llm=llm)
        self.register_tool(sql_tool)
        self.sql_tool = sql_tool

    def execute_task(self, task: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        tools_available = list(self.tools.keys())
        reasoning = self.llm.reason_step(self.name, task, state, tools_available)

        query = reasoning.action_input.get("query")
        if not query:
            # Fallback default query for department
            dept = task.get("target_department", "DEP-ENG")
            query = f"SELECT * FROM departments WHERE id = '{dept}'"

        logger.info("[SQLAgent] Executing query: %s", query)
        tool_res = self.sql_tool.execute(query=query)

        return {
            "agent": self.name,
            "action": reasoning.action or "safe_sql_query",
            "thought": reasoning.thought,
            "success": tool_res.success,
            "data": tool_res.data,
            "error": tool_res.error,
            "tokens_used": reasoning.usage.get("total_tokens", 0)
        }
