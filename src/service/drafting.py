"""
ManualPPT 手冊腳本與發布閘門服務 (Manual Drafting & Formal Publication Gate Service)

提供證據綁定的步驟說明生成 (Purpose, Environment, Process, Reason, Outcome, Caution)、
未支援聲明標註、步階層級全追溯性 (Traceability) 與 Formal Publication Gate 審核。
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from src.domain.models import (
    Evidence,
    ManualDraft,
    Publication,
    SourceReference,
    Step,
    WorkflowVersion,
)


class StepTraceability(BaseModel):
    """步階全追溯性標籤"""
    step_id: str
    workflow_version_id: str
    trace_id: str
    evidence_id: Optional[str] = None
    screenshot_path: Optional[str] = None
    source_reference_ids: List[str] = Field(default_factory=list)
    execution_result: str = Field(default="PASSED")


class DraftStepContent(BaseModel):
    """手冊草稿步驟內容 (含來源綁定說明)"""
    step_id: str
    operation: str
    target_name: str
    purpose: str
    reason: str
    expected_result: str
    caution: Optional[str] = None
    is_pending_confirmation: bool = False
    traceability: StepTraceability


class EvidenceBoundDraftEngine:
    """證據導向手冊草稿生成引擎"""

    def generate_draft(
        self,
        workflow: WorkflowVersion,
        evidences: List[Evidence],
        sources: List[SourceReference],
        trace_id: str
    ) -> ManualDraft:
        sections: List[Dict[str, Any]] = [
            {"title": "1. 主流程說明", "steps": []},
            {"title": "2. 分支與例外流程", "steps": []},
            {"title": "3. 測試與覆蓋附錄", "steps": []}
        ]

        evidence_map = {e.step_id: e for e in evidences}

        for step in workflow.steps:
            ev = evidence_map.get(step.step_id)
            
            # 檢查是否有合法的 Source Reference 支撐說明
            has_source = len(sources) > 0
            is_pending = not has_source

            trace_info = StepTraceability(
                step_id=step.step_id,
                workflow_version_id=workflow.version_id,
                trace_id=trace_id,
                evidence_id=ev.evidence_id if ev else None,
                screenshot_path=ev.screenshot_path if ev else None,
                source_reference_ids=[s.source_id for s in sources]
            )

            content = DraftStepContent(
                step_id=step.step_id,
                operation=step.action_type,
                target_name=step.target_element.name or "目標元件",
                purpose=step.purpose or ("依據規格說明" if has_source else "待確認用途"),
                reason=step.reason or "完成業務流程步驟",
                expected_result=step.expected_result or "畫面正確切換並回應成功訊息",
                caution=step.caution,
                is_pending_confirmation=is_pending,
                traceability=trace_info
            )

            sections[0]["steps"].append(content.model_dump())

        return ManualDraft(
            workflow_version_id=workflow.version_id,
            title="標準作業手冊草稿",
            sections=sections,
            is_approved=False
        )


class PublicationGate:
    """正式發布審核閘門 (Formal Publication Gate)"""

    def evaluate_publication(
        self,
        draft: ManualDraft,
        unresolved_conflicts_count: int,
        signed_off_by: Optional[str]
    ) -> Tuple[bool, List[str]]:
        """
        評估是否具備 Formal Publication 資格
        回傳 (can_publish_formal, unfulfilled_criteria)
        """
        unfulfilled: List[str] = []

        if unresolved_conflicts_count > 0:
            unfulfilled.append(f"存在 {unresolved_conflicts_count} 個未解決的規格衝突")

        if not signed_off_by:
            unfulfilled.append("尚未取得負責人正式簽核 (signed_off_by)")

        # 檢查草稿步驟中是否有待確認項目
        pending_count = 0
        for sec in draft.sections:
            for stp in sec.get("steps", []):
                if stp.get("is_pending_confirmation"):
                    pending_count += 1

        if pending_count > 0:
            unfulfilled.append(f"手冊內包含 {pending_count} 項待確認欄位")

        return len(unfulfilled) == 0, unfulfilled
