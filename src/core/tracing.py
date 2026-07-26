"""
ManualPPT 追蹤識別符與事件序號規則 (Tracing & Idempotency Rules)

提供全域 Trace Identifier 生成、冪等鍵 (Idempotency Key) 計算與事件序號校驗機制。
"""

import hashlib
import time
import uuid
from typing import Optional
from pydantic import BaseModel, Field


def generate_trace_id(prefix: str = "trc") -> str:
    """
    生成唯一 Trace Identifier
    格式: trc_<timestamp_ms>_<hex8>
    """
    ts = int(time.time() * 1000)
    rand_hex = uuid.uuid4().hex[:8]
    return f"{prefix}_{ts}_{rand_hex}"


def generate_idempotency_key(scope: str, action_payload: str) -> str:
    """
    生成冪等鍵 (Idempotency Key)
    格式: idk_<scope>_<sha256_short>
    """
    digest = hashlib.sha256(action_payload.encode("utf-8")).hexdigest()[:16]
    return f"idk_{scope}_{digest}"


class EventSequenceTracker(BaseModel):
    """
    事件序號追蹤器，確保事件連續性與順序不顛倒
    """
    current_sequence: int = Field(default=0, description="目前最後序號")

    def next_sequence(self) -> int:
        """取得下一個號碼"""
        self.current_sequence += 1
        return self.current_sequence

    def validate_next(self, incoming_sequence: int) -> bool:
        """驗證新傳入的序號是否精確為 current_sequence + 1"""
        return incoming_sequence == self.current_sequence + 1
