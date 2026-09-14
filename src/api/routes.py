from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Response, status

from src.agents.erp_agent import ERPActionAgent
from src.agents.policy_agent import PolicyComplianceAgent
from src.agents.sql_agent import SQLDataAgent
from src.api.schemas import (
    AuditTrailResponse,
    CreateWorkflowRequest,
    HealthResponse,
    HITLDecisionRequest,
    WorkflowResponse,
)
from src.core.config import settings
from src.core.logging import get_logger
from src.core.metrics import metrics_collector
from src.core.security import AccessControlManager
from src.guardrails.audit_ledger import audit_ledger
from src.llm.live_llm import get_agent_llm
from src.orchestration.checkpoint import checkpoint_manager
from src.orchestration.graph import WorkforceGraphEngine
from src.orchestration.supervisor import SupervisorAgent
from src.tools.erp_tool import ERPActionTool
from src.tools.policy_tool import PolicyVerificationTool
from src.tools.sql_tool import SafeSQLTool

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1")

# Initialize global engine singletons
llm = get_agent_llm(settings.llm_provider)
sql_tool = SafeSQLTool()
policy_tool = PolicyVerificationTool()
erp_tool = ERPActionTool()

sql_agent = SQLDataAgent(llm=llm, sql_tool=sql_tool)
policy_agent = PolicyComplianceAgent(llm=llm, policy_tool=policy_tool)
erp_agent = ERPActionAgent(llm=llm, erp_tool=erp_tool)
supervisor = SupervisorAgent(llm=llm)

engine = WorkforceGraphEngine(
    supervisor=supervisor,
    agents={
        "sql_agent": sql_agent,
        "policy_agent": policy_agent,
        "erp_agent": erp_agent
    },
    llm=llm
)


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    db_schema = sql_tool.get_schema()
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        environment=settings.app_env,
        db_connected=len(db_schema) > 0,
        registered_agents=list(engine.agents.keys())
    )


@router.get("/metrics")
def metrics() -> Response:
    return Response(content=metrics_collector.export_text(), media_type="text/plain; version=0.0.4; charset=utf-8")


@router.post("/tasks", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def submit_workflow_task(
    payload: CreateWorkflowRequest,
    authorization: Optional[str] = Header(default=None)
) -> WorkflowResponse:
    sub, role = AccessControlManager.resolve_bearer_identity(authorization, require_auth=True)
    AccessControlManager.enforce_permission(role, "read:data", "workflow submission")

    state = engine.create_workflow(payload.user_goal)
    if state.status.value != "FAILED":
        state = engine.run_until_complete_or_pause(state)

    return WorkflowResponse(**state.model_dump())


@router.get("/tasks/{workflow_id}", response_model=WorkflowResponse)
def get_workflow_status(
    workflow_id: str,
    authorization: Optional[str] = Header(default=None)
) -> WorkflowResponse:
    AccessControlManager.resolve_bearer_identity(authorization, require_auth=True)

    state = checkpoint_manager.load_checkpoint(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' was not found in checkpoint storage."
        )

    return WorkflowResponse(**state.model_dump())


@router.post("/tasks/{workflow_id}/approve", response_model=WorkflowResponse)
def decide_hitl_approval(
    workflow_id: str,
    payload: HITLDecisionRequest,
    authorization: Optional[str] = Header(default=None)
) -> WorkflowResponse:
    sub, role = AccessControlManager.resolve_bearer_identity(authorization, require_auth=True)
    # Strictly require MANAGER or ADMIN for Human-in-the-Loop approval
    AccessControlManager.enforce_permission(role, "approve:hitl", "human-in-the-loop authorization")

    try:
        updated_state = engine.process_hitl_decision(
            workflow_id=workflow_id,
            decision=payload.decision,
            user_id=sub,
            reason=payload.reason
        )
        return WorkflowResponse(**updated_state.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/tasks/{workflow_id}/audit-trail", response_model=AuditTrailResponse)
def get_workflow_audit_trail(
    workflow_id: str,
    authorization: Optional[str] = Header(default=None)
) -> AuditTrailResponse:
    AccessControlManager.resolve_bearer_identity(authorization, require_auth=True)

    trail = audit_ledger.get_task_trail(workflow_id)
    is_valid, err = audit_ledger.verify_integrity()

    return AuditTrailResponse(
        workflow_id=workflow_id,
        entry_count=len(trail),
        chain_verified=is_valid,
        integrity_error=err,
        entries=trail
    )
