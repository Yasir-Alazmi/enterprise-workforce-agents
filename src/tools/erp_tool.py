import uuid

from src.core.logging import get_logger
from src.tools.base import BaseTool, ToolResult

logger = get_logger(__name__)


class ERPActionTool(BaseTool):
    """Stages and executes enterprise ERP operations (Procurement Orders, Ticket Updates)."""

    @property
    def name(self) -> str:
        return "stage_erp_action"

    @property
    def description(self) -> str:
        return (
            "Stages an ERP action (e.g. create purchase order, submit requisition). "
            "If the action requires Human-in-the-Loop approval, it stages a pending draft."
        )

    def execute(
        self,
        action: str,
        department_id: str,
        vendor_name: str,
        amount: float,
        description: str,
        requires_hitl: bool = False,
        approved: bool = False
    ) -> ToolResult:
        order_id = f"PO-REQ-{uuid.uuid4().hex[:8].upper()}"

        if requires_hitl and not approved:
            logger.info("Staged ERP action %s requiring HITL approval: $%s for %s", order_id, amount, vendor_name)
            return ToolResult(
                success=True,
                data={
                    "status": "STAGED_PENDING_APPROVAL",
                    "order_id": order_id,
                    "department_id": department_id,
                    "vendor_name": vendor_name,
                    "amount": amount,
                    "description": description,
                    "requires_hitl": True
                },
                metadata={"message": "Action staged. Requires authorized human approval to commit to ERP."}
            )

        # Committed action
        logger.info("Committed ERP action %s: $%s for %s", order_id, amount, vendor_name)
        return ToolResult(
            success=True,
            data={
                "status": "COMMITTED",
                "order_id": order_id,
                "department_id": department_id,
                "vendor_name": vendor_name,
                "amount": amount,
                "description": description,
                "requires_hitl": False
            },
            metadata={"message": "Action successfully executed and committed to enterprise records."}
        )
