from abc import ABC, abstractmethod
from typing import Any, Dict

from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: str = ""
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """Abstract base interface for all workforce agent tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        pass
