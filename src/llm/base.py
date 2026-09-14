from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AgentLLMResponse(BaseModel):
    thought: str
    action: Optional[str] = None
    action_input: Dict[str, Any] = {}
    final_response: Optional[str] = None
    usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


class BaseAgentLLM(ABC):
    """Abstract base interface for agent reasoning engines."""

    @abstractmethod
    def plan_workflow(self, user_goal: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def reason_step(
        self,
        agent_name: str,
        current_task: Dict[str, Any],
        accumulated_state: Dict[str, Any],
        tools_available: List[str]
    ) -> AgentLLMResponse:
        pass

    @abstractmethod
    def synthesize_resolution(self, user_goal: str, execution_trace: List[Dict[str, Any]]) -> str:
        pass
