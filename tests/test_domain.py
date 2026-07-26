"""
Canonical Workflow Domain 測試 (2.1 - 2.6)
"""

import pytest
from src.core.audit import AuditLogStore
from src.domain.commands import AddStateCommand, AddStepCommand, SynchronizedWorkflowEditor
from src.domain.diffing import DiffType, WorkflowDiffEngine
from src.domain.models import (
    ActionType,
    ApplicationScope,
    Checkpoint,
    Project,
    State,
    Step,
    TargetElement,
    WorkflowVersion,
)
from src.domain.validation import WorkflowValidator
from src.repository.adapters import CheckpointRepositoryAdapter, WorkflowRepositoryAdapter
from src.repository.db import DatabaseManager
from src.service.governance import GovernanceDeniedException, GovernanceService


def test_domain_entities_and_validation():
    prj = Project(name="Demo App Manual")
    scope = ApplicationScope(
        project_id=prj.project_id,
        target_origin="http://localhost:8000",
        approved_modules=["auth", "billing"],
        is_approved=True
    )
    st1 = State(name="Login State", page_url="http://localhost:8000/login", exposed_buttons=["Submit"])
    st2 = State(name="Dashboard State", page_url="http://localhost:8000/dashboard")

    step1 = Step(
        state_id=st1.state_id,
        action_type=ActionType.CLICK,
        target_element=TargetElement(role="button", name="Submit")
    )

    wf = WorkflowVersion(
        project_id=prj.project_id,
        states=[st1, st2],
        steps=[step1]
    )

    validator = WorkflowValidator()
    result = validator.validate_workflow(wf, scope)
    assert result.button_coverage_percent == 100.0


def test_synchronized_commands():
    wf = WorkflowVersion(project_id="prj_1", states=[], steps=[])
    editor = SynchronizedWorkflowEditor(wf)

    st = State(name="Home", page_url="http://localhost/home")
    editor.apply_command(AddStateCommand(state=st))
    assert len(wf.states) == 1

    step = Step(
        state_id=st.state_id,
        action_type=ActionType.CLICK,
        target_element=TargetElement(role="button", name="Start")
    )
    editor.apply_command(AddStepCommand(step=step))
    assert len(wf.steps) == 1


def test_diff_and_immutable_merge():
    st = State(name="Form", page_url="http://localhost/form")
    s1 = Step(state_id=st.state_id, action_type=ActionType.INPUT_TEXT, target_element=TargetElement(role="textbox", name="Username"))
    v1 = WorkflowVersion(project_id="prj_1", version_number=1, states=[st], steps=[s1])

    # 模擬人工錄製新增一個按鈕點擊步驟
    s2 = Step(state_id=st.state_id, action_type=ActionType.CLICK, target_element=TargetElement(role="button", name="Next"))
    diff = WorkflowDiffEngine.compare_steps(v1, [s1, s2])

    assert len(diff.candidates) == 1
    assert diff.candidates[0].diff_type == DiffType.ADD_STEP

    # 模擬使用者確認該變更
    diff.candidates[0].is_confirmed = True
    v2 = WorkflowDiffEngine.merge_confirmed_diff(v1, diff, confirmed_by="user_admin")

    assert v2.version_number == 2
    assert len(v2.steps) == 2
    assert v1.version_number == 1
    assert len(v1.steps) == 1  # 驗證 v1 不可變


def test_governance_service():
    audit_store = AuditLogStore()
    gov = GovernanceService(audit_store)
    scope = ApplicationScope(project_id="p1", target_origin="http://localhost:8000", is_approved=True)

    # 普通 CLICK 動作應該成功
    assert gov.authorize_action("user1", scope, ActionType.CLICK, "http://localhost:8000", "trc_1") is True

    # 存取非白名單 Origin 應該引發例外
    with pytest.raises(GovernanceDeniedException) as exc_info:
        gov.authorize_action("user1", scope, ActionType.CLICK, "https://production.bank.com", "trc_2")
    assert exc_info.value.code == "UNSAFE_ORIGIN"

    # 高風險 DELETE 動作缺乏二次確認應該引發例外
    with pytest.raises(GovernanceDeniedException) as exc_info:
        gov.authorize_action("user1", scope, ActionType.DELETE, "http://localhost:8000", "trc_3")
    assert exc_info.value.code == "SECOND_CONFIRMATION_REQUIRED"

    # 取得 Grant 後再執行高風險動作
    grant_id = gov.issue_one_time_grant("user1", "DELETE_ACCOUNT", "trc_4")
    assert gov.authorize_action("user1", scope, ActionType.DELETE, "http://localhost:8000", "trc_4", grant_id=grant_id) is True


def test_durable_checkpoint_repository():
    db_mgr = DatabaseManager("sqlite:///:memory:")
    session = next(db_mgr.get_session())

    wf_adapter = WorkflowRepositoryAdapter(session)
    chk_adapter = CheckpointRepositoryAdapter(session)

    wf = WorkflowVersion(project_id="prj_1", states=[], steps=[])
    wf_adapter.save(wf)

    fetched_wf = wf_adapter.get_by_id(wf.version_id)
    assert fetched_wf is not None
    assert fetched_wf.project_id == "prj_1"

    chk = Checkpoint(
        run_id="run_100",
        step_id="stp_1",
        trace_id="trc_999",
        state_snapshot={"current_url": "http://localhost/page1"},
        evidence_ids=["evd_1", "evd_2"]
    )
    chk_adapter.save_checkpoint(chk)

    latest_chk = chk_adapter.get_latest_checkpoint("run_100")
    assert latest_chk is not None
    assert latest_chk.step_id == "stp_1"
    assert "evd_1" in latest_chk.evidence_ids
