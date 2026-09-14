import re
from typing import Any, Dict, List, Optional

from src.llm.base import AgentLLMResponse, BaseAgentLLM


class DeterministicAgentLLM(BaseAgentLLM):
    """Offline, zero-cost, high-speed deterministic agent reasoning engine for tests and CI."""

    def plan_workflow(self, user_goal: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        goal_lower = user_goal.lower()
        tasks: List[Dict[str, Any]] = []

        # Heuristic intent parser
        dept_match = re.search(r"\b(engineering|marketing|finance|human resources|operations|dep-\w+)\b", goal_lower)
        dept_id = "DEP-ENG"
        if dept_match:
            dept_name = dept_match.group(1).upper()
            mapping = {
                "ENGINEERING": "DEP-ENG", "MARKETING": "DEP-MKT", "FINANCE": "DEP-FIN",
                "HUMAN RESOURCES": "DEP-HR", "OPERATIONS": "DEP-OPS"
            }
            dept_id = mapping.get(dept_name, dept_name)

        amount_match = re.search(r"\$?\b(\d[\d,]*(\.\d+)?)\b", goal_lower)
        amount = 0.0
        if amount_match:
            try:
                amount = float(amount_match.group(1).replace(",", ""))
            except ValueError:
                amount = 15000.0

        vendor_match = re.search(r"from\s+([A-Za-z0-9\s]+?)(?:\s+for|\s+at|\s+costing|\$|$)", user_goal, re.IGNORECASE)
        vendor = vendor_match.group(1).strip() if vendor_match else "Premier Tech Supplies"

        # 1. If asking for data/budget/employees/procurement
        if any(w in goal_lower for w in ["budget", "spend", "cost", "salary", "employee", "purchase", "order", "analyze"]):
            tasks.append({
                "step_id": "step_1_query_data",
                "agent": "sql_agent",
                "action": "safe_sql_query",
                "description": f"Query department and financial data for {dept_id}",
                "target_department": dept_id
            })

        # 2. If involving a purchase, procurement, or policy check
        if any(w in goal_lower for w in ["purchase", "procure", "order", "buy", "acquire", "requisition", "policy"]):
            tasks.append({
                "step_id": "step_2_verify_policy",
                "agent": "policy_agent",
                "action": "verify_policy_compliance",
                "description": f"Verify procurement policy compliance for ${amount:,.2f} order",
                "target_amount": amount,
                "target_department": dept_id
            })
            tasks.append({
                "step_id": "step_3_stage_erp_action",
                "agent": "erp_agent",
                "action": "stage_erp_action",
                "description": f"Stage purchase order with {vendor} for ${amount:,.2f}",
                "target_amount": amount,
                "target_department": dept_id,
                "vendor_name": vendor
            })

        # Fallback if no specific pattern matched
        if not tasks:
            tasks.append({
                "step_id": "step_1_inspect",
                "agent": "sql_agent",
                "action": "safe_sql_query",
                "description": f"Inspect enterprise database for {user_goal[:40]}",
                "target_department": dept_id
            })

        return tasks

    def reason_step(
        self,
        agent_name: str,
        current_task: Dict[str, Any],
        accumulated_state: Dict[str, Any],
        tools_available: List[str]
    ) -> AgentLLMResponse:
        dept = current_task.get("target_department", "DEP-ENG")
        amount = current_task.get("target_amount", 12000.0)
        vendor = current_task.get("vendor_name", "Enterprise Cloud Services")

        if agent_name == "sql_agent":
            query = f"SELECT * FROM departments WHERE id = '{dept}'"
            return AgentLLMResponse(
                thought=f"I need to inspect the current budget and expenditure status for department {dept}.",
                action="safe_sql_query",
                action_input={"query": query},
                usage={"prompt_tokens": 120, "completion_tokens": 40, "total_tokens": 160}
            )

        elif agent_name == "policy_agent":
            dept_data = accumulated_state.get("sql_results", [{}])[0]
            annual = dept_data.get("budget_annual", 1000000.0)
            spent = dept_data.get("budget_spent", 500000.0)
            return AgentLLMResponse(
                thought=f"Evaluating procurement compliance for purchase of ${amount:,.2f} against department {dept} budget.",
                action="verify_policy_compliance",
                action_input={
                    "action_type": "procurement",
                    "payload": {
                        "amount": amount,
                        "budget_annual": annual,
                        "budget_spent": spent
                    }
                },
                usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200}
            )

        elif agent_name == "erp_agent":
            policy_res = accumulated_state.get("policy_result", {})
            requires_hitl = policy_res.get("requires_hitl", amount > 5000.0)
            return AgentLLMResponse(
                thought=f"Staging ERP requisition order for {vendor} (${amount:,.2f}). HITL required: {requires_hitl}.",
                action="stage_erp_action",
                action_input={
                    "action": "create_po",
                    "department_id": dept,
                    "vendor_name": vendor,
                    "amount": amount,
                    "description": f"Enterprise procurement requisition for {vendor}",
                    "requires_hitl": requires_hitl,
                    "approved": accumulated_state.get("hitl_approved", False)
                },
                usage={"prompt_tokens": 140, "completion_tokens": 45, "total_tokens": 185}
            )

        return AgentLLMResponse(
            thought=f"Default agent response for {agent_name}",
            final_response="Completed standard processing.",
            usage={"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70}
        )

    def synthesize_resolution(self, user_goal: str, execution_trace: List[Dict[str, Any]]) -> str:
        summary_lines = [f"Successfully orchestrated enterprise workflow for: '{user_goal}'."]
        for item in execution_trace:
            agent = item.get("agent", "Agent")
            action = item.get("action", "Action")
            status = item.get("status", "SUCCESS")
            summary_lines.append(f"- [{agent}] {action}: {status}")
        return "\n".join(summary_lines)
