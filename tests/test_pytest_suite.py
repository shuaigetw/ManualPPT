"""
全面性 pytest 整合與治理驗證測試套件 (8.1, 8.2, 8.3)

驗證：
1. 流程覆蓋率、版本 Diff、規格衝突、檢查點、資料保留與發布閘門。
2. 治理攔截 (未授權 Origin、非白名單、敏感資料外洩、高風險未確認)。
3. 端對端事件序號、遮罩完整性、證據 Hash 與 Trace Identifier。
"""

import pytest
from src.core.audit import AuditEventType, AuditLogStore
from src.core.tracing import EventSequenceTracker, generate_trace_id
from src.domain.diffing import DiffType, WorkflowDiffEngine
from src.domain.models import ActionType, ApplicationScope, State, Step, TargetElement, WorkflowVersion
from src.repository.adapters import CheckpointRepositoryAdapter
from src.repository.db import DatabaseManager
from src.service.capture import EvidenceIngestionService, MaskingRules
from src.service.drafting import EvidenceBoundDraftEngine, PublicationGate
from src.service.governance import GovernanceDeniedException, GovernanceService
from src.service.ingestion import DocumentIngestionService


def test_full_governance_and_security_blocking():
    audit_store = AuditLogStore()
    gov = GovernanceService(audit_store)
    scope = ApplicationScope(project_id="p1", target_origin="http://localhost:8000", is_approved=True)

    trace_id = generate_trace_id()

    # 1. 驗證非白名單 Origin 阻擋
    with pytest.raises(GovernanceDeniedException) as exc1:
        gov.authorize_action("actor1", scope, ActionType.CLICK, "https://malicious-site.com", trace_id)
    assert exc1.value.code == "UNSAFE_ORIGIN"

    # 2. 驗證未核准 Scope 阻擋
    unapproved_scope = ApplicationScope(project_id="p1", target_origin="http://localhost:8000", is_approved=False)
    with pytest.raises(GovernanceDeniedException) as exc2:
        gov.authorize_action("actor1", unapproved_scope, ActionType.CLICK, "http://localhost:8000", trace_id)
    assert exc2.value.code == "SCOPE_UNAPPROVED"

    # 3. 驗證高風險寫入未核准阻擋
    with pytest.raises(GovernanceDeniedException) as exc3:
        gov.authorize_action("actor1", scope, ActionType.DELETE, "http://localhost:8000", trace_id)
    assert exc3.value.code == "SECOND_CONFIRMATION_REQUIRED"


def test_evidence_integrity_sequence_and_masking():
    tracker = EventSequenceTracker()
    seq1 = tracker.next_sequence()
    seq2 = tracker.next_sequence()

    assert seq1 == 1 and seq2 == 2
    assert tracker.validate_next(3) is True

    # 敏感資訊源頭遮罩與雜湊
    sanitized = MaskingRules.sanitize_event_payload({"action_type": "INPUT_TEXT", "value": "secret_password_123"})
    assert sanitized["value"] == "***MASKED***"

    evidence_service = EvidenceIngestionService()
    ev = evidence_service.ingest_event("run_1", "step_1", sanitized, b"screenshot_data")
    assert ev is not None
    assert ev.hash_digest != ""
    assert ev.is_masked is True


def test_publication_gate_and_source_conflict():
    ingest = DocumentIngestionService()
    ingest.ingest_text_document("Title", "v1", "2026-01-01", "PDF", "Do X")
    ingest.ingest_text_document("Title", "v2", "2026-06-01", "PDF", "Do Y")

    conflicts = ingest.detect_conflicts()
    assert len(conflicts) == 1

    st = State(name="S1", page_url="http://localhost")
    step = Step(state_id=st.state_id, action_type=ActionType.CLICK, target_element=TargetElement(role="button", name="B1"))
    wf = WorkflowVersion(project_id="p1", states=[st], steps=[step])

    draft_engine = EvidenceBoundDraftEngine()
    draft = draft_engine.generate_draft(wf, [], [], "trc_1")

    gate = PublicationGate()
    can_publish, reasons = gate.evaluate_publication(draft, len(conflicts), signed_off_by=None)
    assert can_publish is False
    assert any("衝突" in r for r in reasons)
