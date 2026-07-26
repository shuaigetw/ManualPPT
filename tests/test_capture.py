"""
Local Browser and Desktop Capture 測試 (4.1 - 4.7)
"""

import pytest
from src.service.capture import (
    DesktopSessionController,
    EvidenceIngestionService,
    MaskingRules,
    RawCaptureEvent,
)


def test_masking_rules():
    assert MaskingRules.mask_text("User Password") == "***MASKED***"
    assert MaskingRules.mask_text("Normal Text") == "Normal Text"

    sanitized = MaskingRules.sanitize_event_payload({"action_type": "INPUT_TEXT", "value": "my_secret_password"})
    assert sanitized["value"] == "***MASKED***"


def test_desktop_session_controller():
    ctrl = DesktopSessionController()
    assert ctrl.is_recording is False

    ctrl.start_recording()
    assert ctrl.is_recording is True

    ctrl.switch_to_manual_takeover()
    assert ctrl.is_manual_takeover is True

    ctrl.buffer_incoming_events([
        RawCaptureEvent(action_type="CLICK", target={"role": "button", "name": "OK"}, timestamp="2026-07-25T12:00:00Z")
    ])

    flushed = ctrl.flush_buffer()
    assert len(flushed) == 1
    assert len(ctrl.buffered_events) == 0


def test_evidence_ingestion_and_deduplication():
    service = EvidenceIngestionService()
    img_data = b"fake_screenshot_png_bytes_123"

    ev1 = service.ingest_event("run_1", "step_1", {"action_type": "CLICK", "value": "secret_token"}, img_data)
    assert ev1 is not None
    assert ev1.is_masked is True
    assert ev1.raw_event_payload["value"] == "***MASKED***"
    assert ev1.screenshot_path is not None

    # 輸入相同圖片數據 -> 合併/捨棄重複截圖
    ev2 = service.ingest_event("run_1", "step_2", {"action_type": "CLICK", "value": "normal"}, img_data)
    assert ev2 is not None
    assert ev2.screenshot_path is None  # 被捨棄
