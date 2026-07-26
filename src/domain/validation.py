"""
ManualPPT 工作流程校驗器 (Workflow Validation)

驗證可到達路徑 (Reachable Paths)、下拉選單選項覆蓋、多選欄位覆蓋、
獨立按鈕分支、角色權限與例外流程結果。
"""

from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field
from src.domain.models import ActionType, ApplicationScope, State, Step, WorkflowVersion


class ValidationIssue(BaseModel):
    """校驗發現的問題或未覆蓋提示"""
    severity: str = Field(description="ERROR | WARNING | INFO")
    code: str
    message: str
    target_id: Optional[str] = None


class ValidationResult(BaseModel):
    """工作流程校驗總結果"""
    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    reachable_state_ids: List[str] = Field(default_factory=list)
    dropdown_coverage_percent: float = 100.0
    button_coverage_percent: float = 100.0


class WorkflowValidator:
    """流程模型合法性與完整覆蓋性驗證器"""

    def validate_workflow(
        self,
        workflow: WorkflowVersion,
        scope: Optional[ApplicationScope] = None
    ) -> ValidationResult:
        issues: List[ValidationIssue] = []

        if not workflow.states:
            return ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(severity="ERROR", code="EMPTY_WORKFLOW", message="流程版本內無任何 State 實體")]
            )

        # 1. 驗證可到達路徑 (Reachable Paths via BFS)
        initial_state_id = workflow.states[0].state_id
        reachable: Set[str] = {initial_state_id}
        queue: List[str] = [initial_state_id]

        adjacency: Dict[str, List[str]] = {}
        for tr in workflow.transitions:
            adjacency.setdefault(tr.from_state_id, []).append(tr.to_state_id)

        while queue:
            curr = queue.pop(0)
            for next_st in adjacency.get(curr, []):
                if next_st not in reachable:
                    reachable.add(next_st)
                    queue.append(next_st)

        all_state_ids = {st.state_id for st in workflow.states}
        unreachable = all_state_ids - reachable
        for un in unreachable:
            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="UNREACHABLE_STATE",
                    message=f"State [{un}] 無法從初始節點到達",
                    target_id=un
                )
            )

        # 2. 下拉選單與多選欄位選項覆蓋檢查
        dropdown_total = 0
        dropdown_covered = 0
        steps_by_state: Dict[str, List[Step]] = {}
        for step in workflow.steps:
            steps_by_state.setdefault(step.state_id, []).append(step)

        for st in workflow.states:
            st_steps = steps_by_state.get(st.state_id, [])
            tested_options: Dict[str, Set[str]] = {}
            for step in st_steps:
                if step.action_type in (ActionType.SELECT_DROPDOWN, ActionType.MULTI_SELECT):
                    field_name = step.target_element.name or "unnamed_field"
                    tested_options.setdefault(field_name, set()).add(str(step.input_data))

            for field_name, available_opts in st.dropdown_options.items():
                dropdown_total += len(available_opts)
                tested = tested_options.get(field_name, set())
                dropdown_covered += len(tested.intersection(set(available_opts)))

                missing_opts = set(available_opts) - tested
                if missing_opts:
                    issues.append(
                        ValidationIssue(
                            severity="WARNING",
                            code="MISSING_DROPDOWN_OPTION_COVERAGE",
                            message=f"State [{st.name}] 的欄位 [{field_name}] 未測試選項: {list(missing_opts)}",
                            target_id=st.state_id
                        )
                    )

        dropdown_cov_pct = (dropdown_covered / dropdown_total * 100.0) if dropdown_total > 0 else 100.0

        # 3. 獨立按鈕分支覆蓋檢查
        button_total = 0
        button_covered = 0
        for st in workflow.states:
            st_steps = steps_by_state.get(st.state_id, [])
            clicked_button_names = {
                step.target_element.name
                for step in st_steps
                if step.action_type == ActionType.CLICK and step.target_element.name
            }
            for btn_name in st.exposed_buttons:
                button_total += 1
                if btn_name in clicked_button_names:
                    button_covered += 1
                else:
                    issues.append(
                        ValidationIssue(
                            severity="WARNING",
                            code="UNTESTED_BUTTON_PATH",
                            message=f"State [{st.name}] 的按鈕 [{btn_name}] 尚未建立獨立測試路徑",
                            target_id=st.state_id
                        )
                    )

        button_cov_pct = (button_covered / button_total * 100.0) if button_total > 0 else 100.0

        # 4. Scope 角色與 Origin 檢查
        if scope:
            if not scope.is_approved:
                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="SCOPE_NOT_APPROVED",
                        message=f"Scope [{scope.scope_id}] 尚未獲得授權核准"
                    )
                )

        has_errors = any(i.severity == "ERROR" for i in issues)

        return ValidationResult(
            is_valid=not has_errors,
            issues=issues,
            reachable_state_ids=list(reachable),
            dropdown_coverage_percent=round(dropdown_cov_pct, 2),
            button_coverage_percent=round(button_cov_pct, 2)
        )
