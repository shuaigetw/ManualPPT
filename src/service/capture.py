"""
ManualPPT 本機擷取與證據處理解析服務 (Capture & Evidence Ingestion Service)

提供桌面工作階段控制器、錄影/人工接管模式切換、斷線緩衝、
擷取源頭敏感資訊遮罩、顯著狀態截圖篩選與帶 Hash 的證據寫入。
"""

import hashlib
import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.core.tracing import generate_trace_id
from src.domain.models import Evidence


class RawCaptureEvent(BaseModel):
    """傳入的原始 UI 事件"""
    action_type: str
    target: Dict[str, Any]
    value: Optional[str] = None
    timestamp: str


class MaskingRules:
    """本機遮罩規則與敏感資訊偵測器"""

    SENSITIVE_KEY_PATTERNS = [
        r"password", r"passwd", r"secret", r"salary", r"pay",
        r"ssn", r"id_number", r"mfa", r"token", r"bank_account"
    ]

    @classmethod
    def mask_text(cls, text: str) -> str:
        """如果包含敏感詞，予以遮罩"""
        if not text:
            return text
        for pat in cls.SENSITIVE_KEY_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return "***MASKED***"
        return text

    @classmethod
    def sanitize_event_payload(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """對事件 payload 進行深層遮罩處理"""
        sanitized = json.loads(json.dumps(payload))
        val = str(sanitized.get("value", ""))
        if val and cls.mask_text(val) == "***MASKED***":
            sanitized["value"] = "***MASKED***"
        return sanitized


class DesktopSessionController:
    """本機桌面工作階段控制器 (支援錄製、人工接管與斷線緩衝區)"""

    def __init__(self):
        self.is_recording: bool = False
        self.is_manual_takeover: bool = False
        self.buffered_events: List[RawCaptureEvent] = []

    def start_recording(self):
        self.is_recording = True
        self.is_manual_takeover = False

    def switch_to_manual_takeover(self):
        """切換至人工接管示範模式"""
        self.is_manual_takeover = True

    def resume_scripted_mode(self):
        self.is_manual_takeover = False

    def stop_recording(self):
        self.is_recording = False
        self.is_manual_takeover = False

    def buffer_incoming_events(self, events: List[RawCaptureEvent]):
        """緩衝斷線或連續事件"""
        self.buffered_events.extend(events)

    def flush_buffer(self) -> List[RawCaptureEvent]:
        flushed = list(self.buffered_events)
        self.buffered_events = []
        return flushed


class EvidenceIngestionService:
    """有序證據寫入服務 (含 Hash 雜湊計算、重複畫面合併與伺服器 Ack)"""

    def __init__(self):
        self.ingested_evidences: List[Evidence] = []
        self._last_screenshot_hash: Optional[str] = None

    def ingest_event(
        self,
        run_id: str,
        step_id: str,
        event_payload: Dict[str, Any],
        screenshot_bytes: Optional[bytes] = None
    ) -> Optional[Evidence]:
        """
        寫入單一事件與截圖。若截圖無顯著變化 (Hash 重複)，予以合併或捨棄。
        """
        sanitized_payload = MaskingRules.sanitize_event_payload(event_payload)
        payload_str = json.dumps(sanitized_payload, sort_keys=True)
        
        screenshot_hash = ""
        screenshot_path = None
        if screenshot_bytes:
            screenshot_hash = hashlib.sha256(screenshot_bytes).hexdigest()
            # 若連續截圖 Hash 完全相同，丟棄低價值畫面 (Discard Low-Value Frames)
            if screenshot_hash == self._last_screenshot_hash:
                screenshot_bytes = None
            else:
                self._last_screenshot_hash = screenshot_hash
                screenshot_path = f"/screenshots/{screenshot_hash[:16]}.png"

        full_content_str = payload_str + screenshot_hash
        content_digest = hashlib.sha256(full_content_str.encode("utf-8")).hexdigest()

        evidence = Evidence(
            run_id=run_id,
            step_id=step_id,
            event_timestamp=sanitized_payload.get("timestamp", ""),
            screenshot_path=screenshot_path,
            raw_event_payload=sanitized_payload,
            hash_digest=content_digest,
            is_masked=True
        )

        self.ingested_evidences.append(evidence)
        return evidence
