"""
ManualPPT 雙向同步指令編輯器 (Synchronized Workflow Domain Commands)

提供對 Flowchart (State/Transition) 與 Step Table (Step/Branch) 的同步編輯命令，
確保兩視圖修改時維持一致性。
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel
from src.domain.models import Branch, State, Step, Transition, WorkflowVersion


class WorkflowCommand(BaseModel):
    """領域指令抽象基類"""
    pass


class AddStateCommand(WorkflowCommand):
    state: State


class AddStepCommand(WorkflowCommand):
    step: Step
    auto_create_transition_to_state: Optional[str] = None


class UpdateStepCommand(WorkflowCommand):
    step_id: str
    updated_fields: Dict[str, Any]


class AddTransitionCommand(WorkflowCommand):
    transition: Transition


class SynchronizedWorkflowEditor:
    """
    流程圖與步驟表同步編輯器
    """

    def __init__(self, workflow: WorkflowVersion):
        self.workflow = workflow

    def apply_command(self, command: WorkflowCommand) -> WorkflowVersion:
        """根據指令更新 workflow，並保證雙向同步"""
        if isinstance(command, AddStateCommand):
            self._add_state(command.state)
        elif isinstance(command, AddStepCommand):
            self._add_step(command.step, command.auto_create_transition_to_state)
        elif isinstance(command, UpdateStepCommand):
            self._update_step(command.step_id, command.updated_fields)
        elif isinstance(command, AddTransitionCommand):
            self._add_transition(command.transition)
        else:
            raise ValueError(f"未知的 Command 類型: {type(command)}")

        return self.workflow

    def _add_state(self, state: State):
        # 若已有同名或同 id 的 state，更新之；否則追加
        existing = next((s for s in self.workflow.states if s.state_id == state.state_id), None)
        if existing:
            idx = self.workflow.states.index(existing)
            self.workflow.states[idx] = state
        else:
            self.workflow.states.append(state)

    def _add_step(self, step: Step, next_state_id: Optional[str] = None):
        self.workflow.steps.append(step)
        if next_state_id:
            # 同步更新 Transition
            trans = Transition(
                from_state_id=step.state_id,
                to_state_id=next_state_id,
                condition=f"After step {step.step_id}"
            )
            self._add_transition(trans)

    def _update_step(self, step_id: str, updated_fields: Dict[str, Any]):
        step = next((s for s in self.workflow.steps if s.step_id == step_id), None)
        if not step:
            raise KeyError(f"找不到 Step ID: {step_id}")

        step_dict = step.model_dump()
        step_dict.update(updated_fields)
        new_step = Step(**step_dict)

        idx = self.workflow.steps.index(step)
        self.workflow.steps[idx] = new_step

    def _add_transition(self, transition: Transition):
        existing = next(
            (t for t in self.workflow.transitions
             if t.from_state_id == transition.from_state_id and t.to_state_id == transition.to_state_id),
            None
        )
        if not existing:
            self.workflow.transitions.append(transition)
