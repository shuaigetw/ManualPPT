"""
ManualPPT 唯增稽核日誌 (Append-Only Audit Log Engine)

定義所有核心事件類型與不可變 (Immutable) 稽核事件結構。
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from src.core.tracing import generate_trace_id


class AuditEventType(str, Enum):
    """稽核事件類型"""
    SCOPE_APPROVED = "SCOPE_APPROVED"
    ACTION_AUTHORIZED = "ACTION_AUTHORIZED"
    ACTION_DENIED = "ACTION_DENIED"
    DANGEROUS_ACTION_REQUESTED = "DANGEROUS_ACTION_REQUESTED"
    DANGEROUS_ACTION_CONFIRMED = "DANGEROUS_ACTION_CONFIRMED"
    DANGEROUS_ACTION_DECLINED = "DANGEROUS_ACTION_DECLINED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_PAUSED = "EXECUTION_PAUSED"
    EXECUTION_RESUMED = "EXECUTION_RESUMED"
    EXECUTION_TERMINATED = "EXECUTION_TERMINATED"
    CHECKPOINT_CREATED = "CHECKPOINT_CREATED"
    EVIDENCE_CAPTURED = "EVIDENCE_CAPTURED"
    EVIDENCE_MASKED = "EVIDENCE_MASKED"
    MANUAL_CORRECTION_PROPOSED = "MANUAL_CORRECTION_PROPOSED"
    WORKFLOW_VERSION_COMMITTED = "WORKFLOW_VERSION_COMMITTED"
    PUBLICATION_SIGNED_OFF = "PUBLICATION_SIGNED_OFF"
    UNAPPROVED_UPLOAD_BLOCKED = "UNAPPROVED_UPLOAD_BLOCKED"


class AuditEvent(BaseModel):
    """
    不可變稽核事件實體
    """
    event_id: str = Field(default_factory=lambda: generate_trace_id("aud"), description="稽核事件 ID")
    trace_id: str = Field(description="關聯 Trace ID")
    event_type: AuditEventType = Field(description="事件類型")
    actor_id: str = Field(description="操作者 ID (使用者或 Agent)")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO UTC 時間戳記"
    )
    details: Dict[str, Any] = Field(default_factory=dict, description="事件詳細資料")
    corrected_event_id: Optional[str] = Field(default=None, description="若此事件為修正前事件，記錄被修正事件之 ID")


class AuditLogStore:
    """
    記憶體與持久化 Append-Only 稽核儲存庫
    嚴禁修改與刪除舊有記錄，僅能追加。
    """

    def __init__(self):
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> AuditEvent:
        """追加新稽核事件"""
        self._events.append(event)
        return event

    def list_events(self, trace_id: Optional[str] = None) -> list[AuditEvent]:
        """查詢稽核紀錄 (唯讀)"""
        if trace_id:
            return [e for e in self._events if e.trace_id == trace_id]
        return list(self._events)

    def count(self) -> int:
        """取得總事件數"""
        return len(self._events)
