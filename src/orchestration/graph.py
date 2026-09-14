import time
from typing import Dict, Optional

from src.agents.base import BaseAgent
from src.core.config import settings
from src.core.logging import get_logger
from src.core.metrics import metrics_collector
from src.guardrails.audit_ledger import audit_ledger
from src.guardrails.injection_detector import InjectionDetector
from src.llm.base import BaseAgentLLM
from src.orchestration.checkpoint import checkpoint_manager
from src.orchestration.state import AgentState, HITLApprovalRequest, WorkflowStatus
from src.orchestration.supervisor import SupervisorAgent

logger = get_logger(__name__)


class WorkforceGraphEngine:
    """Deterministic multi-agent execution engine with pause/resume Human-in-the-Loop checkpoints."""

    def __init__(
        self,
        supervisor: SupervisorAgent,
        agents: Dict[str, BaseAgent],
        llm: BaseAgentLLM
    ):
        self.supervisor = supervisor
        self.agents = agents
        self.llm = llm
        self.detector = InjectionDetector()

    def create_workflow(self, user_goal: str) -> AgentState:
        # Screen for adversarial injection
        is_inj, findings = self.detector.scan(user_goal)
        if is_inj:
            state = AgentState(user_goal=user_goal, status=WorkflowStatus.FAILED)
            state.final_resolution = f"Security Violation: Adversarial prompt injection detected: {findings}"
            audit_ledger.record_event(
                task_id=state.workflow_id,
                event_type="SECURITY_BLOCK",
                agent_name="InjectionDetector",
                payload={"findings": findings, "goal": user_goal}
            )
            checkpoint_manager.save_checkpoint(state)
            return state

        tasks = self.supervisor.plan_workflow(user_goal)
        state = AgentState(
            user_goal=user_goal,
            status=WorkflowStatus.RUNNING,
            tasks=tasks
        )
        audit_ledger.record_event(
            task_id=state.workflow_id,
            event_type="WORKFLOW_CREATED",
            agent_name="Supervisor",
            payload={"task_count": len(tasks), "goal": user_goal}
        )
        checkpoint_manager.save_checkpoint(state)
        return state

    def step(self, state: AgentState) -> AgentState:
        if state.status not in [WorkflowStatus.RUNNING, WorkflowStatus.APPROVED]:
            return state

        # Check if completed all tasks
        if state.current_step_index >= len(state.tasks):
            state.status = WorkflowStatus.COMPLETED
            state.final_resolution = self.llm.synthesize_resolution(state.user_goal, state.execution_trace)
            checkpoint_manager.save_checkpoint(state)
            audit_ledger.record_event(
                task_id=state.workflow_id,
                event_type="WORKFLOW_COMPLETED",
                agent_name="GraphEngine",
                payload={"resolution": state.final_resolution}
            )
            return state

        task = state.tasks[state.current_step_index]
        agent_name = task.agent
        agent = self.agents.get(agent_name)

        if not agent:
            task.status = "FAILED"
            task.error = f"Agent '{agent_name}' not registered."
            state.status = WorkflowStatus.FAILED
            checkpoint_manager.save_checkpoint(state)
            return state

        t0 = time.perf_counter()
        step_result = agent.execute_task(task.metadata, state.accumulated_data)
        dur = time.perf_counter() - t0

        metrics_collector.record_agent_invocation(agent_name, dur)
        state.total_tokens_used += step_result.get("tokens_used", 0)
        # Standard token pricing estimate ($0.0001 per 1k tokens)
        state.estimated_cost_usd = round(state.total_tokens_used * 0.0000005, 6)

        # Record audit log
        audit_ledger.record_event(
            task_id=state.workflow_id,
            event_type="AGENT_STEP",
            agent_name=agent_name,
            payload={
                "step_id": task.step_id,
                "action": step_result.get("action"),
                "thought": step_result.get("thought"),
                "success": step_result.get("success"),
                "duration_sec": round(dur, 4)
            }
        )

        task.result = step_result.get("data")
        task.status = "COMPLETED" if step_result.get("success") else "FAILED"

        # Update accumulated state
        if agent_name == "sql_agent":
            state.accumulated_data["sql_results"] = step_result.get("data", [])
        elif agent_name == "policy_agent":
            state.accumulated_data["policy_result"] = step_result.get("data", {})
        elif agent_name == "erp_agent":
            state.accumulated_data["erp_result"] = step_result.get("data", {})

        state.execution_trace.append(step_result)

        # Check for Human-in-the-Loop trigger
        policy_res = state.accumulated_data.get("policy_result", {})
        erp_res = state.accumulated_data.get("erp_result", {})

        # If policy strictly requires HITL, or ERP staged an order requiring approval
        if (policy_res.get("requires_hitl") or erp_res.get("requires_hitl")) and not state.accumulated_data.get("hitl_approved"):
            state.status = WorkflowStatus.WAITING_FOR_APPROVAL
            amount = task.metadata.get("target_amount", 0.0)
            state.pending_hitl = HITLApprovalRequest(
                task_id=state.workflow_id,
                action_type=task.action,
                amount=amount,
                department_id=task.metadata.get("target_department", ""),
                reason=policy_res.get("rule_description") or f"Purchase amount (${amount:,.2f}) exceeds autonomous delegation threshold.",
                payload=step_result.get("data") or {}
            )
            audit_ledger.record_event(
                task_id=state.workflow_id,
                event_type="HITL_PAUSE",
                agent_name="GraphEngine",
                payload={"request_id": state.pending_hitl.request_id, "amount": amount}
            )
            checkpoint_manager.save_checkpoint(state)
            logger.info("Workflow %s paused at step %d for Human-in-the-Loop approval.", state.workflow_id, state.current_step_index)
            return state

        state.current_step_index += 1
        checkpoint_manager.save_checkpoint(state)
        return state

    def run_until_complete_or_pause(self, state: AgentState) -> AgentState:
        step_count = 0
        max_steps = settings.max_graph_steps

        while state.status in [WorkflowStatus.RUNNING, WorkflowStatus.APPROVED] and step_count < max_steps:
            state = self.step(state)
            step_count += 1
            if state.status == WorkflowStatus.WAITING_FOR_APPROVAL:
                break
            if state.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                break

        checkpoint_manager.save_checkpoint(state)
        return state

    def process_hitl_decision(
        self,
        workflow_id: str,
        decision: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> AgentState:
        state = checkpoint_manager.load_checkpoint(workflow_id)
        if not state:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        if state.status != WorkflowStatus.WAITING_FOR_APPROVAL:
            raise ValueError(f"Workflow '{workflow_id}' is not currently waiting for approval (Status: {state.status.value}).")

        is_approved = decision.upper() == "APPROVE"
        metrics_collector.record_hitl_decision(decision.upper())

        if state.pending_hitl:
            state.pending_hitl.decision = decision.upper()
            state.pending_hitl.decision_by = user_id
            state.pending_hitl.decision_reason = reason or ("Approved by administrator" if is_approved else "Rejected")
            state.pending_hitl.decision_at = time.time()

        audit_ledger.record_event(
            task_id=state.workflow_id,
            event_type="HITL_DECISION",
            agent_name="HumanSupervisor",
            payload={"decision": decision.upper(), "by": user_id, "reason": reason}
        )

        if is_approved:
            state.status = WorkflowStatus.APPROVED
            state.accumulated_data["hitl_approved"] = True
            # Re-execute ERP action to commit now that it has been approved
            state = self.step(state)
            return self.run_until_complete_or_pause(state)
        else:
            state.status = WorkflowStatus.REJECTED
            state.final_resolution = f"Workflow rejected by human supervisor {user_id}: {reason or 'No reason provided'}"
            checkpoint_manager.save_checkpoint(state)
            return state
