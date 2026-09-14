import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple


class AuditLedgerEntry:
    """Single tamper-evident entry in the cryptographic audit ledger."""

    def __init__(
        self,
        entry_id: int,
        task_id: str,
        event_type: str,
        agent_name: str,
        payload: Dict[str, Any],
        prev_hash: str,
        timestamp: Optional[float] = None
    ):
        self.entry_id = entry_id
        self.task_id = task_id
        self.event_type = event_type
        self.agent_name = agent_name
        self.payload = payload
        self.prev_hash = prev_hash
        self.timestamp = timestamp or time.time()
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        serialized = json.dumps({
            "entry_id": self.entry_id,
            "task_id": self.task_id,
            "event_type": self.event_type,
            "agent_name": self.agent_name,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp
        }, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "task_id": self.task_id,
            "event_type": self.event_type,
            "agent_name": self.agent_name,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
            "timestamp": self.timestamp
        }


class CryptographicAuditLedger:
    """Append-only, SHA-256 linked cryptographic audit ledger."""

    def __init__(self):
        self.entries: List[AuditLedgerEntry] = []
        self._genesis_hash = "0" * 64

    def record_event(
        self,
        task_id: str,
        event_type: str,
        agent_name: str,
        payload: Dict[str, Any]
    ) -> AuditLedgerEntry:
        prev_hash = self.entries[-1].hash if self.entries else self._genesis_hash
        entry_id = len(self.entries) + 1
        entry = AuditLedgerEntry(
            entry_id=entry_id,
            task_id=task_id,
            event_type=event_type,
            agent_name=agent_name,
            payload=payload,
            prev_hash=prev_hash
        )
        self.entries.append(entry)
        return entry

    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        prev_hash = self._genesis_hash
        for i, entry in enumerate(self.entries):
            if entry.prev_hash != prev_hash:
                return False, f"Broken chain at entry {entry.entry_id}: prev_hash mismatch"
            recalculated = entry._compute_hash()
            if recalculated != entry.hash:
                return False, f"Tampered entry {entry.entry_id}: hash mismatch"
            prev_hash = entry.hash
        return True, None

    def get_task_trail(self, task_id: str) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.entries if e.task_id == task_id]


audit_ledger = CryptographicAuditLedger()
