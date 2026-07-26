"""
Project Foundations 測試 (1.1 - 1.4)
"""

import pytest
from src.config import settings
from src.core.tracing import generate_trace_id, generate_idempotency_key, EventSequenceTracker
from src.core.audit import AuditEvent, AuditEventType, AuditLogStore


def test_config_and_allowlist():
    assert settings.feature_flags.readonly_discovery is True
    assert settings.origin_allowlist.is_origin_allowed("http://localhost:3000") is True
    assert settings.origin_allowlist.is_origin_allowed("https://app.staging.internal") is True
    assert settings.origin_allowlist.is_origin_allowed("https://production.bank.com") is False


def test_tracing_and_idempotency():
    trace_id = generate_trace_id()
    assert trace_id.startswith("trc_")
    
    idk = generate_idempotency_key("click_button", "button_submit")
    assert idk.startswith("idk_click_button_")

    tracker = EventSequenceTracker()
    seq1 = tracker.next_sequence()
    assert seq1 == 1
    assert tracker.validate_next(2) is True
    assert tracker.validate_next(3) is False


def test_append_only_audit_log():
    store = AuditLogStore()
    trace_id = generate_trace_id()
    event = AuditEvent(
        trace_id=trace_id,
        event_type=AuditEventType.SCOPE_APPROVED,
        actor_id="user_admin",
        details={"scope": "all_reachable"}
    )
    store.append(event)
    assert store.count() == 1
    retrieved = store.list_events(trace_id=trace_id)
    assert len(retrieved) == 1
    assert retrieved[0].event_type == AuditEventType.SCOPE_APPROVED
