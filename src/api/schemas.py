from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.orchestration.state import HITLApprovalRequest, TaskItem, WorkflowStatus


class CreateWorkflowRequest(BaseModel):
    user_goal: str = Field(..., description="High-level business task or operational objective.")
    user_role: Optional[str] = Field(default="employee", description="Contextual role of the submitting user.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context parameters.")


class HITLDecisionRequest(BaseModel):
    decision: str = Field(..., description="Decision: 'APPROVE' or 'REJECT'")
    reason: Optional[str] = Field(default=None, description="Explanation or business justification.")


class WorkflowResponse(BaseModel):
    workflow_id: str
    status: WorkflowStatus
    user_goal: str
    current_step_index: int
    tasks: List[TaskItem]
    pending_hitl: Optional[HITLApprovalRequest] = None
    final_resolution: Optional[str] = None
    total_tokens_used: int
    estimated_cost_usd: float
    created_at: float
    updated_at: float


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    db_connected: bool
    registered_agents: List[str]
    version: str = "0.1.0"


class AuditTrailResponse(BaseModel):
    workflow_id: str
    entry_count: int
    chain_verified: bool
    integrity_error: Optional[str] = None
    entries: List[Dict[str, Any]]
