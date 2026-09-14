import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.core.logging import get_logger
from src.tools.base import BaseTool, ToolResult

logger = get_logger(__name__)


class PolicyVerificationTool(BaseTool):
    """Evaluates corporate governance, procurement, and expenditure compliance."""

    def __init__(self, policies_dir: Optional[Path] = None):
        if policies_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            self._dir = project_root / "data" / "policies"
        else:
            self._dir = policies_dir
        self.policies: Dict[str, Dict[str, Any]] = {}
        self._load_policies()

    def _load_policies(self):
        if self._dir.exists():
            for p_file in self._dir.glob("*.json"):
                try:
                    with open(p_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        p_id = data.get("policy_id", p_file.stem)
                        self.policies[p_id] = data
                except Exception as e:
                    logger.error("Failed to load policy file %s: %s", p_file.name, e)

    @property
    def name(self) -> str:
        return "verify_policy_compliance"

    @property
    def description(self) -> str:
        return (
            "Checks if an operational action, purchase order, or expense complies with corporate policies "
            "and determines if executive Human-in-the-Loop approval is strictly required."
        )

    def evaluate_procurement(
        self,
        amount: float,
        department_budget_spent: float,
        department_budget_annual: float
    ) -> Dict[str, Any]:
        policy = self.policies.get("POL-PROC-001", {})
        rules = policy.get("rules", [])

        applicable_rule = None
        requires_hitl = False
        approval_level = "UNKNOWN"
        violations = []

        # Check budget overrun
        if department_budget_spent + amount > department_budget_annual:
            violations.append(
                f"Budget overrun: Purchase (${amount:,.2f}) exceeds remaining department budget "
                f"(${department_budget_annual - department_budget_spent:,.2f})."
            )
            requires_hitl = True
            approval_level = "BUDGET_OVERRUN_EXCEPTION"

        # Check procurement threshold rule
        for rule in rules:
            max_amt = rule.get("max_amount", float("inf"))
            if amount <= max_amt:
                applicable_rule = rule
                if rule.get("requires_hitl", False):
                    requires_hitl = True
                if approval_level == "UNKNOWN":
                    approval_level = rule.get("approval_required", "MANAGER")
                break

        if not applicable_rule and rules:
            applicable_rule = rules[-1]
            requires_hitl = True
            approval_level = "EXECUTIVE_BOARD"

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "requires_hitl": requires_hitl,
            "approval_level": approval_level,
            "rule_id": applicable_rule.get("rule_id", "N/A") if applicable_rule else "N/A",
            "rule_description": applicable_rule.get("description", "") if applicable_rule else ""
        }

    def execute(self, action_type: str, payload: Dict[str, Any]) -> ToolResult:
        if action_type == "procurement":
            amount = float(payload.get("amount", 0.0))
            spent = float(payload.get("budget_spent", 0.0))
            annual = float(payload.get("budget_annual", 0.0))
            result = self.evaluate_procurement(amount, spent, annual)
            return ToolResult(success=True, data=result)
        elif action_type == "travel":
            # Travel policy evaluation
            daily_lodging = float(payload.get("daily_lodging", 0.0))
            is_compliant = daily_lodging <= 350.0
            return ToolResult(
                success=True,
                data={
                    "compliant": is_compliant,
                    "requires_hitl": not is_compliant,
                    "approval_level": "TRAVEL_DESK" if is_compliant else "DIRECTOR_EXCEPTION"
                }
            )
        else:
            return ToolResult(
                success=False,
                error=f"Unrecognized policy evaluation action type: '{action_type}'"
            )
