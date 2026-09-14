import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskItem(BaseModel):
    step_id: str
    agent: str
    action: str
    description: str
    status: str = "PENDING"
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HITLApprovalRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: f"HITL-{uuid.uuid4().hex[:8].upper()}")
    task_id: str
    action_type: str
    amount: float = 0.0
    department_id: str = ""
    reason: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    decision: Optional[str] = None
    decision_by: Optional[str] = None
    decision_reason: Optional[str] = None
    decision_at: Optional[float] = None


class AgentState(BaseModel):
    workflow_id: str = Field(default_factory=lambda: f"wf-{uuid.uuid4().hex[:12]}")
    user_goal: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    tasks: List[TaskItem] = Field(default_factory=list)
    current_step_index: int = 0
    accumulated_data: Dict[str, Any] = Field(default_factory=dict)
    pending_hitl: Optional[HITLApprovalRequest] = None
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    final_resolution: Optional[str] = None
    total_tokens_used: int = 0
    estimated_cost_usd: float = 0.0
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def advance_step(self) -> Optional[TaskItem]:
        if self.current_step_index < len(self.tasks):
            task = self.tasks[self.current_step_index]
            self.current_step_index += 1
            self.updated_at = time.time()
            return task
        return None

    def get_current_task(self) -> Optional[TaskItem]:
        if self.current_step_index < len(self.tasks):
            return self.tasks[self.current_step_index]
        return None
