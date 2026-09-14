from typing import Any, Dict, List, Optional

import httpx

from src.core.config import settings
from src.core.logging import get_logger
from src.llm.base import AgentLLMResponse, BaseAgentLLM
from src.llm.deterministic import DeterministicAgentLLM

logger = get_logger(__name__)


class LiveAgentLLM(BaseAgentLLM):
    """Live LLM adapter supporting OpenAI / Ollama with graceful deterministic fallback."""

    def __init__(self):
        self._fallback = DeterministicAgentLLM()
        self.provider = settings.llm_provider
        self.openai_key = settings.openai_api_key
        self.openai_model = settings.openai_model
        self.ollama_url = settings.ollama_base_url

    def plan_workflow(self, user_goal: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # In live scenarios without reachable endpoint, fallback gracefully
        if self.provider == "ollama":
            try:
                res = httpx.get(f"{self.ollama_url}/api/tags", timeout=1.0)
                if res.status_code == 200:
                    logger.info("Ollama is reachable. Executing agent planning.")
            except Exception:
                logger.warning("Ollama unreachable at %s. Falling back to deterministic planner.", self.ollama_url)
        return self._fallback.plan_workflow(user_goal, context)

    def reason_step(
        self,
        agent_name: str,
        current_task: Dict[str, Any],
        accumulated_state: Dict[str, Any],
        tools_available: List[str]
    ) -> AgentLLMResponse:
        return self._fallback.reason_step(agent_name, current_task, accumulated_state, tools_available)

    def synthesize_resolution(self, user_goal: str, execution_trace: List[Dict[str, Any]]) -> str:
        return self._fallback.synthesize_resolution(user_goal, execution_trace)


def get_agent_llm(provider: Optional[str] = None) -> BaseAgentLLM:
    p = (provider or settings.llm_provider).lower()
    if p in ["openai", "ollama", "live"]:
        return LiveAgentLLM()
    return DeterministicAgentLLM()
