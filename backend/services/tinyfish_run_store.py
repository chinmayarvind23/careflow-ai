from typing import Dict, Optional
from threading import Lock

from models.tinyfish_state import TinyFishEligibilityState


class TinyFishRunStore:
    def __init__(self) -> None:
        self._runs: Dict[str, TinyFishEligibilityState] = {}
        self._lock = Lock()

    def create_run(self, state: TinyFishEligibilityState) -> None:
        with self._lock:
            self._runs[state.tinyfish_run_id] = state

    def get_run(self, tinyfish_run_id: str) -> Optional[TinyFishEligibilityState]:
        with self._lock:
            return self._runs.get(tinyfish_run_id)

    def update_run(self, state: TinyFishEligibilityState) -> None:
        with self._lock:
            self._runs[state.tinyfish_run_id] = state


tinyfish_run_store = TinyFishRunStore()