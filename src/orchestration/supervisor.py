from typing import List

from src.core.logging import get_logger
from src.llm.base import BaseAgentLLM
from src.orchestration.state import TaskItem

logger = get_logger(__name__)


class SupervisorAgent:
    """Central planner that decomposes user goals into structured, ordered domain tasks."""

    def __init__(self, llm: BaseAgentLLM):
        self.llm = llm

    def plan_workflow(self, user_goal: str) -> List[TaskItem]:
        logger.info("[Supervisor] Decomposing enterprise goal into execution graph: '%s'", user_goal)
        raw_tasks = self.llm.plan_workflow(user_goal=user_goal)

        task_items: List[TaskItem] = []
        for raw in raw_tasks:
            task_items.append(TaskItem(
                step_id=raw.get("step_id", f"step_{len(task_items)+1}"),
                agent=raw.get("agent", "sql_agent"),
                action=raw.get("action", "query"),
                description=raw.get("description", ""),
                metadata=raw
            ))

        logger.info("[Supervisor] Generated %d executable tasks in DAG.", len(task_items))
        return task_items
