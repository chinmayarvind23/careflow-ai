from typing import Dict, Optional
from threading import Lock

from models.workflow_state import DocumentWorkflowState


class RunStore:
    def __init__(self) -> None:
        self._runs: Dict[str, DocumentWorkflowState] = {}
        self._lock = Lock()

    def create_run(self, state: DocumentWorkflowState) -> None:
        with self._lock:
            self._runs[state.run_id] = state

    def get_run(self, run_id: str) -> Optional[DocumentWorkflowState]:
        with self._lock:
            return self._runs.get(run_id)

    def update_run(self, state: DocumentWorkflowState) -> None:
        with self._lock:
            self._runs[state.run_id] = state


run_store = RunStore()