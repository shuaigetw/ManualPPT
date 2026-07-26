"""
ManualPPT 受治理控制服務 (Governance Enforcement Service)

為所有 Workflow 與 Execution 寫入路徑提供原使用者權限、核准 Scope、
Origin 白名單與高風險動作二次確認授權檢查。
"""

from typing import Dict, Optional, Tuple
from src.config import settings
from src.core.audit import AuditEvent, AuditEventType, AuditLogStore
from src.domain.models import ActionType, ApplicationScope, Approval, RiskLevel
from src.core.tracing import generate_trace_id


class GovernanceDeniedException(Exception):
    """治理權限攔截例外"""
    def __init__(self, message: str, trace_id: str, code: str):
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id
        self.code = code


class GovernanceService:
    """治理授權檢查服務器"""

    def __init__(self, audit_store: AuditLogStore):
        self.audit_store = audit_store
        self._one_time_grants: Dict[str, bool] = {}

    def check_origin_allowlist(self, target_origin: str, trace_id: str):
        """檢查目標 Origin 是否在 localhost/staging 白名單之內"""
        if not settings.origin_allowlist.is_origin_allowed(target_origin):
            # 寫入 UNAPPROVED_UPLOAD_BLOCKED 或 ACTION_DENIED 稽核
            self.audit_store.append(
                AuditEvent(
                    trace_id=trace_id,
                    event_type=AuditEventType.UNAPPROVED_UPLOAD_BLOCKED,
                    actor_id="system_governance",
                    details={"rejected_origin": target_origin, "reason": "Origin 不在授權白名單內"}
                )
            )
            raise GovernanceDeniedException(
                message=f"拒絕存取非白名單 Origin: {target_origin}",
                trace_id=trace_id,
                code="UNSAFE_ORIGIN"
            )

    def check_scope_approval(self, scope: ApplicationScope, trace_id: str):
        """檢查 Scope 是否已經獲得核准"""
        if not scope.is_approved:
            self.audit_store.append(
                AuditEvent(
                    trace_id=trace_id,
                    event_type=AuditEventType.ACTION_DENIED,
                    actor_id="system_governance",
                    details={"scope_id": scope.scope_id, "reason": "Scope 尚未經使用者核准"}
                )
            )
            raise GovernanceDeniedException(
                message=f"Scope [{scope.scope_id}] 尚未核准，無法進行寫入操作",
                trace_id=trace_id,
                code="SCOPE_UNAPPROVED"
            )

    def evaluate_action_risk(self, action_type: ActionType) -> Tuple[RiskLevel, bool]:
        """評估動作風險等級與是否需二次確認"""
        if action_type in (ActionType.DELETE, ActionType.PAYMENT, ActionType.SUBMIT):
            return RiskLevel.DANGEROUS, True
        elif action_type in (ActionType.FILE_UPLOAD, ActionType.INPUT_TEXT):
            return RiskLevel.MEDIUM, False
        return RiskLevel.LOW, False

    def authorize_action(
        self,
        actor_id: str,
        scope: ApplicationScope,
        action_type: ActionType,
        target_origin: str,
        trace_id: str,
        grant_id: Optional[str] = None
    ) -> bool:
        """
        對每一個 side-effecting 寫入動作執行綜合授權驗證
        """
        # 1. 檢查 Origin 白名單
        self.check_origin_allowlist(target_origin, trace_id)

        # 2. 檢查 Scope 是否已核准
        self.check_scope_approval(scope, trace_id)

        # 3. 評估風險等級
        risk_level, requires_second_conf = self.evaluate_action_risk(action_type)

        if requires_second_conf:
            if not grant_id or not self._one_time_grants.get(grant_id):
                self.audit_store.append(
                    AuditEvent(
                        trace_id=trace_id,
                        event_type=AuditEventType.DANGEROUS_ACTION_REQUESTED,
                        actor_id=actor_id,
                        details={"action_type": action_type, "risk_level": risk_level}
                    )
                )
                raise GovernanceDeniedException(
                    message=f"高風險動作 [{action_type}] 需要一次性二次確認 grant",
                    trace_id=trace_id,
                    code="SECOND_CONFIRMATION_REQUIRED"
                )
            # 一次性使用，用完即失效
            self._one_time_grants[grant_id] = False
            self.audit_store.append(
                AuditEvent(
                    trace_id=trace_id,
                    event_type=AuditEventType.DANGEROUS_ACTION_CONFIRMED,
                    actor_id=actor_id,
                    details={"action_type": action_type, "grant_id": grant_id}
                )
            )

        # 寫入授權成功稽核
        self.audit_store.append(
            AuditEvent(
                trace_id=trace_id,
                event_type=AuditEventType.ACTION_AUTHORIZED,
                actor_id=actor_id,
                details={"action_type": action_type, "target_origin": target_origin}
            )
        )
        return True

    def issue_one_time_grant(self, actor_id: str, action_name: str, trace_id: str) -> str:
        """發行一次性二次確認 Grant"""
        grant_id = generate_trace_id("grt")
        self._one_time_grants[grant_id] = True
        return grant_id
