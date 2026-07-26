"""
Discovery and Source Ingestion 測試 (3.1 - 3.5)
"""

import pytest
from src.domain.models import ApplicationScope
from src.repository.adapters import CheckpointRepositoryAdapter
from src.repository.db import DatabaseManager
from src.service.discovery import (
    DiscoveryAnswers,
    DiscoveryService,
    FeatureInventory,
    FeatureInventoryItem,
)
from src.service.ingestion import DocumentIngestionService
from src.service.orchestrator import AgentOrchestrator, AgentPhase, OrchestratorState


def test_discovery_completeness_and_workflow_tree():
    service = DiscoveryService()
    incomplete_answers = DiscoveryAnswers(app_purpose="Test System")
    is_complete, missing = service.evaluate_discovery_completeness(incomplete_answers)
    assert is_complete is False
    assert "target_users (目標使用者)" in missing

    inventory = FeatureInventory(
        project_id="prj_1",
        items=[
            FeatureInventoryItem(module="auth", feature_name="Login", role_required="User", exposed_actions=["LoginBtn"])
        ]
    )
    scope = ApplicationScope(
        project_id="prj_1",
        target_origin="http://localhost:3000",
        approved_modules=["auth"],
        approved_roles=["User"],
        is_approved=True
    )
    wf_tree = service.build_reachable_workflow_tree(inventory, scope)
    assert len(wf_tree.states) == 2  # Root/Login + auth - Login


def test_document_ingestion_and_conflict():
    ingest = DocumentIngestionService()
    ingest.ingest_text_document("SOP Manual", "1.0", "2026-01-01", "PDF", "Click button A to submit")
    ingest.ingest_text_document("SOP Manual", "2.0", "2026-06-01", "PDF", "Click button B to submit")

    conflicts = ingest.detect_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0].feature_or_step == "SOP Manual"


def test_agent_orchestrator():
    db_mgr = DatabaseManager("sqlite:///:memory:")
    session = next(db_mgr.get_session())
    chk_repo = CheckpointRepositoryAdapter(session)

    orchestrator = AgentOrchestrator(chk_repo)
    state = OrchestratorState(run_id="run_test_1")

    assert state.current_phase == AgentPhase.DISCOVERY
    updated = orchestrator.advance_phase(state, AgentPhase.PLANNING, "step_1", "trc_100", {"plan": "ready"})

    assert updated.current_phase == AgentPhase.PLANNING
    chk = chk_repo.get_latest_checkpoint("run_test_1")
    assert chk is not None
    assert chk.state_snapshot["current_phase"] == AgentPhase.PLANNING
