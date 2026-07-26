"""
Governed Automation Execution 測試 (5.1 - 5.7)
"""

import pytest
from src.core.audit import AuditLogStore
from src.domain.models import (
    ActionType,
    ApplicationScope,
    ExecutionRun,
    ExecutionStatus,
    Step,
    TargetElement,
)
from src.repository.adapters import CheckpointRepositoryAdapter
from src.repository.db import DatabaseManager
from src.service.execution import ExecutionEngine, PathCoverageStatus
from src.service.governance import GovernanceService


def test_execution_engine_flow():
    db_mgr = DatabaseManager("sqlite:///:memory:")
    session = next(db_mgr.get_session())
    chk_repo = CheckpointRepositoryAdapter(session)
    audit_store = AuditLogStore()
    gov = GovernanceService(audit_store)

    engine = ExecutionEngine(gov, chk_repo, audit_store)
    scope = ApplicationScope(project_id="p1", target_origin="http://localhost:8000", is_approved=True)
    run = ExecutionRun(workflow_version_id="v1", scope_id=scope.scope_id, trace_id="trc_exec")

    step = Step(
        state_id="st1",
        action_type=ActionType.CLICK,
        target_element=TargetElement(role="button", name="Submit")
    )
    dom_elements = [{"role": "button", "name": "Submit"}]

    status = engine.execute_step(run, scope, step, dom_elements)
    assert status == PathCoverageStatus.PASSED
    assert step.step_id in run.completed_step_ids


def test_ambiguous_element_suspension():
    db_mgr = DatabaseManager("sqlite:///:memory:")
    session = next(db_mgr.get_session())
    chk_repo = CheckpointRepositoryAdapter(session)
    audit_store = AuditLogStore()
    gov = GovernanceService(audit_store)

    engine = ExecutionEngine(gov, chk_repo, audit_store)
    scope = ApplicationScope(project_id="p1", target_origin="http://localhost:8000", is_approved=True)
    run = ExecutionRun(workflow_version_id="v1", scope_id=scope.scope_id, trace_id="trc_exec")

    step = Step(
        state_id="st1",
        action_type=ActionType.CLICK,
        target_element=TargetElement(role="button", name="Submit")
    )
    # 畫面上出現 2 個同名同角色的 Submit 按鈕 -> 歧義掛起
    dom_elements = [{"role": "button", "name": "Submit"}, {"role": "button", "name": "Submit"}]

    status = engine.execute_step(run, scope, step, dom_elements)
    assert status == PathCoverageStatus.BLOCKED
    assert run.status == ExecutionStatus.PAUSED


def test_mfa_handoff_and_kill_switch():
    db_mgr = DatabaseManager("sqlite:///:memory:")
    session = next(db_mgr.get_session())
    chk_repo = CheckpointRepositoryAdapter(session)
    audit_store = AuditLogStore()
    gov = GovernanceService(audit_store)

    engine = ExecutionEngine(gov, chk_repo, audit_store)
    run = ExecutionRun(workflow_version_id="v1", scope_id="s1", trace_id="trc_mfa")

    msg = engine.handle_human_mfa_handoff(run)
    assert msg == "MFA_HANDOFF_PAUSED"
    assert run.status == ExecutionStatus.PAUSED

    engine.trigger_kill_switch(run, "使用者按下緊急終止按鈕")
    assert run.status == ExecutionStatus.TERMINATED
    assert engine.kill_switch_active is True
