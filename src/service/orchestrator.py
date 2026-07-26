"""
ManualPPT Agent Orchestrator (Orchestration Engine)

協調 Discovery, Planning, Evidence Analysis 與 Drafting 等長任務階段，
並使用 CheckpointRepositoryAdapter 於每個關鍵節點保存 durable checkpoint。
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from src.core.tracing import generate_trace_id
from src.domain.models import Checkpoint, ExecutionRun, ExecutionStatus
from src.repository.adapters import CheckpointRepositoryAdapter


class AgentPhase(str, Enum):
    """Agent 協調階段"""
    DISCOVERY = "DISCOVERY"
    PLANNING = "PLANNING"
    EVIDENCE_ANALYSIS = "EVIDENCE_ANALYSIS"
    DRAFTING = "DRAFTING"
    COMPLETED = "COMPLETED"


class OrchestratorState(BaseModel):
    """Agent 協調狀態"""
    session_id: str = Field(default_factory=lambda: generate_trace_id("orc"))
    run_id: str
    current_phase: AgentPhase = AgentPhase.DISCOVERY
    phase_data: Dict[str, Any] = Field(default_factory=dict)


class AgentOrchestrator:
    """Agent 任務協調器"""

    def __init__(self, checkpoint_repo: CheckpointRepositoryAdapter):
        self.checkpoint_repo = checkpoint_repo

    def advance_phase(
        self,
        orch_state: OrchestratorState,
        next_phase: AgentPhase,
        step_id: str,
        trace_id: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> OrchestratorState:
        """推進至下一階段並記錄可恢復持久化檢查點"""
        orch_state.current_phase = next_phase
        if additional_data:
            orch_state.phase_data.update(additional_data)

        # 儲存 Checkpoint
        chk = Checkpoint(
            run_id=orch_state.run_id,
            step_id=step_id,
            trace_id=trace_id,
            state_snapshot={
                "session_id": orch_state.session_id,
                "current_phase": orch_state.current_phase,
                "phase_data": orch_state.phase_data
            }
        )
        self.checkpoint_repo.save_checkpoint(chk)
        return orch_state
