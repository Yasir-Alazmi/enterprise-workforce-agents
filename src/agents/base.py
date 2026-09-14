from abc import ABC, abstractmethod
from typing import Any, Dict

from src.llm.base import BaseAgentLLM
from src.tools.base import BaseTool


class BaseAgent(ABC):
    """Abstract base class for specialized domain agents."""

    def __init__(self, name: str, role: str, llm: BaseAgentLLM):
        self.name = name
        self.role = role
        self.llm = llm
        self.tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        self.tools[tool.name] = tool

    @abstractmethod
    def execute_task(self, task: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        pass
