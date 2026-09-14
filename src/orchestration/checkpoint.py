import json
from pathlib import Path
from typing import Dict, Optional

from src.core.config import settings
from src.core.logging import get_logger
from src.orchestration.state import AgentState

logger = get_logger(__name__)


class CheckpointManager:
    """Atomic state persistence enabling Human-in-the-Loop pause/resume and replay."""

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            self.storage_dir = project_root / settings.checkpoint_dir
        else:
            self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, AgentState] = {}

    def save_checkpoint(self, state: AgentState) -> str:
        state_dict = state.model_dump()
        file_path = self.storage_dir / f"{state.workflow_id}.json"
        temp_file = self.storage_dir / f"{state.workflow_id}.json.tmp"

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2)

        temp_file.replace(file_path)
        self._memory_cache[state.workflow_id] = state
        logger.info("Saved atomic checkpoint for workflow: %s (%s)", state.workflow_id, state.status.value)
        return str(file_path)

    def load_checkpoint(self, workflow_id: str) -> Optional[AgentState]:
        if workflow_id in self._memory_cache:
            return self._memory_cache[workflow_id]

        file_path = self.storage_dir / f"{workflow_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            state = AgentState(**data)
            self._memory_cache[workflow_id] = state
            return state
        except Exception as e:
            logger.error("Failed to load checkpoint for workflow %s: %s", workflow_id, e)
            return None


checkpoint_manager = CheckpointManager()
