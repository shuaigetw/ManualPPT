"""
ManualPPT 自動化執行引擎 (Governed Automation Execution Engine)

提供範圍核准執行計畫、誠實覆蓋率報告 (Passed/Failed/Blocked/Declined/Not Reached/Not Selected)、
語意元素解析與多重匹配中斷、人工 Login/MFA 切換、Kill Switch 與合成資料清理計畫。
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from src.core.audit import AuditEvent, AuditEventType, AuditLogStore
from src.core.tracing import generate_trace_id
from src.domain.models import (
    ActionType,
    ApplicationScope,
    Checkpoint,
    ExecutionRun,
    ExecutionStatus,
    Step,
    TargetElement,
)
from src.repository.adapters import CheckpointRepositoryAdapter
from src.service.governance import GovernanceDeniedException, GovernanceService


class PathCoverageStatus(str, Enum):
    """誠實覆蓋率狀態"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    DECLINED = "DECLINED"
    NOT_REACHED = "NOT_REACHED"
    NOT_SELECTED = "NOT_SELECTED"


class SyntheticDataPlan(BaseModel):
    """合成測試資料與清理計畫"""
    plan_id: str = Field(default_factory=lambda: generate_trace_id("dat"))
    created_records: List[Dict[str, str]] = Field(default_factory=list)
    cleanup_steps: List[str] = Field(default_factory=list)
    is_cleaned: bool = False


class ExecutionEngine:
    """自動化受治理執行器"""

    def __init__(
        self,
        governance_service: GovernanceService,
        checkpoint_adapter: CheckpointRepositoryAdapter,
        audit_store: AuditLogStore
    ):
        self.governance = governance_service
        self.checkpoint_adapter = checkpoint_adapter
        self.audit_store = audit_store
        self.kill_switch_active: bool = False

    def trigger_kill_switch(self, run: ExecutionRun, reason: str):
        """觸發緊急終止開關 (Kill Switch)"""
        self.kill_switch_active = True
        run.status = ExecutionStatus.TERMINATED
        self.audit_store.append(
            AuditEvent(
                trace_id=run.trace_id,
                event_type=AuditEventType.EXECUTION_TERMINATED,
                actor_id="system_kill_switch",
                details={"run_id": run.run_id, "reason": reason}
            )
        )

    def resolve_semantic_element(
        self,
        target: TargetElement,
        dom_candidates: List[Dict[str, str]]
    ) -> Tuple[bool, Optional[Dict[str, str]], str]:
        """
        語意元素定位與歧義鎖定判定
        回傳 (is_unique, matched_element, status_message)
        """
        matches = []
        for candidate in dom_candidates:
            if candidate.get("role") == target.role and candidate.get("name") == target.name:
                matches.append(candidate)

        if len(matches) == 1:
            return True, matches[0], "Unique match found"
        elif len(matches) > 1:
            # 歧義多重匹配 -> 必須暫停並由人工確認，不得隨意猜測
            return False, None, f"發現 {len(matches)} 個匹配元素，觸發歧義鎖定暫停"
        return False, None, "未找到符合語意之 UI 元素"

    def handle_human_mfa_handoff(self, run: ExecutionRun) -> str:
        """人工 MFA/Login 接管處理"""
        run.status = ExecutionStatus.PAUSED
        self.audit_store.append(
            AuditEvent(
                trace_id=run.trace_id,
                event_type=AuditEventType.EXECUTION_PAUSED,
                actor_id="execution_engine",
                details={"run_id": run.run_id, "reason": "檢測到 MFA/Login 頁面，切換至人工認證手動接管"}
            )
        )
        return "MFA_HANDOFF_PAUSED"

    def execute_step(
        self,
        run: ExecutionRun,
        scope: ApplicationScope,
        step: Step,
        dom_elements: List[Dict[str, str]],
        grant_id: Optional[str] = None
    ) -> PathCoverageStatus:
        """執行單一步驟並進行治理檢查與 checkpoint 記錄"""
        if self.kill_switch_active or run.status == ExecutionStatus.TERMINATED:
            return PathCoverageStatus.BLOCKED

        # 1. 治理驗證
        try:
            self.governance.authorize_action(
                actor_id="agent_executor",
                scope=scope,
                action_type=step.action_type,
                target_origin=scope.target_origin,
                trace_id=run.trace_id,
                grant_id=grant_id
            )
        except GovernanceDeniedException as e:
            if e.code == "SECOND_CONFIRMATION_REQUIRED":
                return PathCoverageStatus.DECLINED
            return PathCoverageStatus.BLOCKED

        # 2. 語意定位
        is_unique, matched_el, msg = self.resolve_semantic_element(step.target_element, dom_elements)
        if not is_unique:
            run.status = ExecutionStatus.PAUSED
            return PathCoverageStatus.BLOCKED

        # 3. 執行成功並記錄 checkpoint
        run.completed_step_ids.append(step.step_id)
        chk = Checkpoint(
            run_id=run.run_id,
            step_id=step.step_id,
            trace_id=run.trace_id,
            state_snapshot={"step_id": step.step_id, "matched_element": matched_el}
        )
        self.checkpoint_adapter.save_checkpoint(chk)
        return PathCoverageStatus.PASSED
