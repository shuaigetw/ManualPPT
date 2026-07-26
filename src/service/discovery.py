"""
ManualPPT 探索訪談與功能盤點服務 (Discovery & Feature Inventory Service)

提供訪談問卷處理、待確認狀態 (Pending Confirmation)、唯讀功能盤點與可到達流程樹生成。
"""

from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from src.core.tracing import generate_trace_id
from src.domain.models import ApplicationScope, State, Step, WorkflowVersion


class DiscoveryAnswers(BaseModel):
    """訪談問卷答案紀錄"""
    app_purpose: Optional[str] = None
    target_users: Optional[str] = None
    environments: Optional[str] = None
    key_tasks: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    terminology: Dict[str, str] = Field(default_factory=dict)
    known_risks: List[str] = Field(default_factory=list)
    known_exceptions: List[str] = Field(default_factory=list)
    target_audiences: List[str] = Field(default_factory=list)
    output_languages: List[str] = Field(default_factory=lambda: ["zh-TW"])


class FeatureInventoryItem(BaseModel):
    """盤點出的單一功能項目"""
    item_id: str = Field(default_factory=lambda: generate_trace_id("inv"))
    module: str
    feature_name: str
    role_required: str
    is_reachable: bool = True
    exposed_actions: List[str] = Field(default_factory=list)


class FeatureInventory(BaseModel):
    """應用程式功能總盤點"""
    inventory_id: str = Field(default_factory=lambda: generate_trace_id("fiv"))
    project_id: str
    items: List[FeatureInventoryItem] = Field(default_factory=list)


class DiscoveryService:
    """探索服務控制項"""

    def evaluate_discovery_completeness(self, answers: DiscoveryAnswers) -> Tuple[bool, List[str]]:
        """
        評估訪談問卷是否完整
        回傳 (is_complete, missing_fields)
        """
        missing: List[str] = []
        if not answers.app_purpose:
            missing.append("app_purpose (應用程式用途)")
        if not answers.target_users:
            missing.append("target_users (目標使用者)")
        if not answers.key_tasks:
            missing.append("key_tasks (主要任務)")
        if not answers.roles:
            missing.append("roles (角色)")

        return len(missing) == 0, missing

    def build_reachable_workflow_tree(
        self,
        inventory: FeatureInventory,
        scope: ApplicationScope
    ) -> WorkflowVersion:
        """
        依據盤點清單與 Scope，產生可到達的初始 WorkflowVersion 結構 (唯讀探索)
        """
        states: List[State] = []
        # 以 Login 為初始 State
        init_st = State(name="Root/Login", page_url=scope.target_origin)
        states.append(init_st)

        for item in inventory.items:
            if item.module in scope.approved_modules and item.role_required in scope.approved_roles:
                st = State(
                    name=f"{item.module} - {item.feature_name}",
                    page_url=f"{scope.target_origin}/{item.module.lower()}",
                    exposed_buttons=item.exposed_actions
                )
                states.append(st)

        return WorkflowVersion(
            project_id=inventory.project_id,
            version_number=1,
            states=states,
            steps=[]
        )
