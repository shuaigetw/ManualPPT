"""
ManualPPT 不可變流程版本差異與合併引擎 (Immutable Workflow Version Diff & Merge Engine)

計算 add, replace, skip, branch 等人工修正/人工接管與舊版 Workflow 的差異，
並產生需使用者確認的 Diff 候選與不可變新版本。
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from src.core.tracing import generate_trace_id
from src.domain.models import Branch, Step, WorkflowVersion


class DiffType(str, Enum):
    """差異變更類型"""
    ADD_STEP = "ADD_STEP"
    REPLACE_STEP = "REPLACE_STEP"
    SKIP_STEP = "SKIP_STEP"
    BRANCH_CORRECTION = "BRANCH_CORRECTION"


class ChangeCandidate(BaseModel):
    """變更候選項目"""
    candidate_id: str = Field(default_factory=lambda: generate_trace_id("cnd"))
    diff_type: DiffType
    target_step_id: Optional[str] = None
    original_step: Optional[Step] = None
    proposed_step: Optional[Step] = None
    proposed_branch: Optional[Branch] = None
    reason: str = Field(description="變更原因 (如人工示範差異)")
    is_confirmed: bool = False


class WorkflowVersionDiff(BaseModel):
    """流程版本差異紀錄"""
    diff_id: str = Field(default_factory=lambda: generate_trace_id("dif"))
    base_version_id: str
    candidates: List[ChangeCandidate] = Field(default_factory=list)

    def is_all_resolved(self) -> bool:
        """確認是否所有候選變更都有明確核准結果"""
        return len(self.candidates) > 0 and all(c.is_confirmed for c in self.candidates)


class WorkflowDiffEngine:
    """版本差異比對與安全合併引擎"""

    @staticmethod
    def compare_steps(
        base_version: WorkflowVersion,
        recorded_steps: List[Step]
    ) -> WorkflowVersionDiff:
        """比對基底 Workflow 與錄製/修正的 Step 序列"""
        diff = WorkflowVersionDiff(base_version_id=base_version.version_id)

        base_step_map = {s.step_id: s for s in base_version.steps}
        rec_step_map = {s.step_id: s for s in recorded_steps}

        # 檢查新增與取代
        for r_step in recorded_steps:
            if r_step.step_id not in base_step_map:
                # 新增步驟
                diff.candidates.append(
                    ChangeCandidate(
                        diff_type=DiffType.ADD_STEP,
                        proposed_step=r_step,
                        reason="人工錄製新增步驟"
                    )
                )
            else:
                b_step = base_step_map[r_step.step_id]
                # 檢查動作或目標元素是否有改變
                if (b_step.action_type != r_step.action_type or
                    b_step.target_element != r_step.target_element or
                    b_step.input_data != r_step.input_data):
                    diff.candidates.append(
                        ChangeCandidate(
                            diff_type=DiffType.REPLACE_STEP,
                            target_step_id=b_step.step_id,
                            original_step=b_step,
                            proposed_step=r_step,
                            reason="人工示範與腳本步驟不符，提出取代"
                        )
                    )

        # 檢查略過 (SKIP)
        for b_step in base_version.steps:
            if b_step.step_id not in rec_step_map:
                diff.candidates.append(
                    ChangeCandidate(
                        diff_type=DiffType.SKIP_STEP,
                        target_step_id=b_step.step_id,
                        original_step=b_step,
                        reason="人工示範跳過此步驟"
                    )
                )

        return diff

    @staticmethod
    def merge_confirmed_diff(
        base_version: WorkflowVersion,
        diff: WorkflowVersionDiff,
        confirmed_by: str
    ) -> WorkflowVersion:
        """
        將已確認的 Diff 合併至新版本，舊版本保持不可變
        """
        new_version_number = base_version.version_number + 1
        new_steps: List[Step] = list(base_version.steps)

        for candidate in diff.candidates:
            if not candidate.is_confirmed:
                continue

            if candidate.diff_type == DiffType.ADD_STEP and candidate.proposed_step:
                new_steps.append(candidate.proposed_step)
            elif candidate.diff_type == DiffType.REPLACE_STEP and candidate.proposed_step:
                idx = next((i for i, s in enumerate(new_steps) if s.step_id == candidate.target_step_id), -1)
                if idx >= 0:
                    new_steps[idx] = candidate.proposed_step
            elif candidate.diff_type == DiffType.SKIP_STEP:
                new_steps = [s for s in new_steps if s.step_id != candidate.target_step_id]

        new_version = WorkflowVersion(
            project_id=base_version.project_id,
            version_number=new_version_number,
            parent_version_id=base_version.version_id,
            is_committed=True,
            states=list(base_version.states),
            steps=new_steps,
            transitions=list(base_version.transitions),
            branches=list(base_version.branches)
        )
        return new_version
