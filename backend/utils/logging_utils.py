import time
from typing import Optional

from models.workflow_state import DocumentWorkflowState, WorkflowLog


def add_log(state: DocumentWorkflowState, message: str) -> None:
    state.logs.append(WorkflowLog(timestamp=time.time(), message=message))


def update_agent(
    state: DocumentWorkflowState,
    agent_id: str,
    *,
    status: Optional[str] = None,
    current_task: Optional[str] = None,
    observation: Optional[str] = None,
    action: Optional[str] = None,
    append_update: Optional[str] = None,
) -> None:
    for agent in state.agents:
        if agent.id == agent_id:
            if status is not None:
                agent.status = status  # type: ignore
            if current_task is not None:
                agent.current_task = current_task
            if observation is not None:
                agent.observation = observation
            if action is not None:
                agent.action = action
            if append_update is not None:
                agent.updates.append(append_update)
            return