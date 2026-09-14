import tempfile
from pathlib import Path

from src.orchestration.checkpoint import CheckpointManager
from src.orchestration.state import AgentState, WorkflowStatus


def test_checkpoint_save_and_load():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cm = CheckpointManager(storage_dir=Path(tmp_dir))
        state = AgentState(
            user_goal="Test checkpointing",
            status=WorkflowStatus.WAITING_FOR_APPROVAL,
            accumulated_data={"test_key": "test_val"}
        )

        saved_path = cm.save_checkpoint(state)
        assert Path(saved_path).exists()

        # Clear memory cache to test disk loading
        cm._memory_cache.clear()
        loaded = cm.load_checkpoint(state.workflow_id)
        assert loaded is not None
        assert loaded.workflow_id == state.workflow_id
        assert loaded.status == WorkflowStatus.WAITING_FOR_APPROVAL
        assert loaded.accumulated_data["test_key"] == "test_val"


def test_checkpoint_nonexistent_returns_none():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cm = CheckpointManager(storage_dir=Path(tmp_dir))
        assert cm.load_checkpoint("wf-nonexistent-12345") is None


def test_checkpoint_corrupt_file_returns_none():
    with tempfile.TemporaryDirectory() as tmp_dir:
        cm = CheckpointManager(storage_dir=Path(tmp_dir))
        corrupt_file = Path(tmp_dir) / "wf-corrupted.json"
        corrupt_file.write_text("{invalid json syntax...", encoding="utf-8")
        assert cm.load_checkpoint("wf-corrupted") is None
