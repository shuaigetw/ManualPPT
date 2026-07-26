"""
ManualPPT 領域模型定義 (Domain Models)

包含 Project, ApplicationScope, AudienceProfile, RoleSession, WorkflowVersion,
State, Step, Transition, Branch, RiskClassification, ExecutionRun, Checkpoint,
Evidence, Approval, SourceReference, ManualDraft, Publication 等完整型別實體。
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.core.tracing import generate_trace_id


class RiskLevel(str, Enum):
    """動作風險等級"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    DANGEROUS = "DANGEROUS"


class ExecutionStatus(str, Enum):
    """執行狀態"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    FAILED = "FAILED"


class ActionType(str, Enum):
    """UI 動作類型"""
    CLICK = "CLICK"
    DOUBLE_CLICK = "DOUBLE_CLICK"
    RIGHT_CLICK = "RIGHT_CLICK"
    HOVER = "HOVER"
    INPUT_TEXT = "INPUT_TEXT"
    SELECT_DROPDOWN = "SELECT_DROPDOWN"
    MULTI_SELECT = "MULTI_SELECT"
    SLIDER = "SLIDER"
    DRAG_AND_DROP = "DRAG_AND_DROP"
    SCROLL = "SCROLL"
    EXPAND_COLLAPSE = "EXPAND_COLLAPSE"
    FILE_UPLOAD = "FILE_UPLOAD"
    CANVAS_INTERACT = "CANVAS_INTERACT"
    SUBMIT = "SUBMIT"
    DELETE = "DELETE"
    PAYMENT = "PAYMENT"


class TargetElement(BaseModel):
    """UI 元素語意標籤與定位資訊"""
    role: str = Field(description="Accessibility Role (如 button, input, select)")
    name: Optional[str] = Field(default=None, description="Accessible Name / Label")
    test_id: Optional[str] = Field(default=None, description="data-testid")
    candidate_locators: List[str] = Field(default_factory=list, description="候選定位器 (CSS/XPath)")
    bounding_box: Optional[Dict[str, float]] = Field(default=None, description="畫面上相對座標位置")


class Project(BaseModel):
    """專案實體"""
    project_id: str = Field(default_factory=lambda: generate_trace_id("prj"))
    name: str
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ApplicationScope(BaseModel):
    """核准執行範圍"""
    scope_id: str = Field(default_factory=lambda: generate_trace_id("scp"))
    project_id: str
    target_origin: str
    approved_modules: List[str] = Field(default_factory=list)
    approved_roles: List[str] = Field(default_factory=list)
    is_approved: bool = Field(default=False)
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


class AudienceProfile(BaseModel):
    """受眾設定檔 (熟練度, 組織層級, 用途, 語言, 權限)"""
    profile_id: str = Field(default_factory=lambda: generate_trace_id("aud_prof"))
    proficiency: str = Field(description="novice | experienced")
    org_level: str = Field(description="executive | middle_management | frontline_management | frontline_employee | audit")
    purpose: str = Field(description="training | compliance | standard_operation | overview")
    language: str = Field(default="zh-TW")
    role_permissions: List[str] = Field(default_factory=list, description="該受眾允許查看的欄位/角色權限")


class RoleSession(BaseModel):
    """角色工作階段"""
    session_id: str = Field(default_factory=lambda: generate_trace_id("ses"))
    role_name: str
    fixture_account: str
    is_authenticated: bool = False


class State(BaseModel):
    """流程圖中的狀態 (頁面/彈窗狀態)"""
    state_id: str = Field(default_factory=lambda: generate_trace_id("st"))
    name: str
    page_url: str
    exposed_buttons: List[str] = Field(default_factory=list)
    dropdown_options: Dict[str, List[str]] = Field(default_factory=dict, description="欄位名稱 -> 可用選項清單")


class Step(BaseModel):
    """單一操作步驟"""
    step_id: str = Field(default_factory=lambda: generate_trace_id("stp"))
    state_id: str
    action_type: ActionType
    target_element: TargetElement
    input_data: Optional[Any] = None
    purpose: Optional[str] = None
    reason: Optional[str] = None
    caution: Optional[str] = None
    expected_result: Optional[str] = None
    is_dangerous: bool = False


class Transition(BaseModel):
    """狀態轉移與條件"""
    transition_id: str = Field(default_factory=lambda: generate_trace_id("trn"))
    from_state_id: str
    to_state_id: str
    condition: Optional[str] = None
    branch_type: str = Field(default="STANDARD", description="STANDARD | EXCEPTION | OPTION_BRANCH")


class Branch(BaseModel):
    """條件分支"""
    branch_id: str = Field(default_factory=lambda: generate_trace_id("brc"))
    parent_step_id: str
    branch_name: str
    condition: str
    steps: List[Step] = Field(default_factory=list)


class RiskClassification(BaseModel):
    """風險分類判定」"""
    action_type: ActionType
    risk_level: RiskLevel
    requires_second_confirmation: bool


class ExecutionRun(BaseModel):
    """執行紀錄實體"""
    run_id: str = Field(default_factory=lambda: generate_trace_id("run"))
    workflow_version_id: str
    scope_id: str
    trace_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    completed_step_ids: List[str] = Field(default_factory=list)
    current_step_id: Optional[str] = None
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None


class Checkpoint(BaseModel):
    """持久化檢查點 (Durable Checkpoint)"""
    checkpoint_id: str = Field(default_factory=lambda: generate_trace_id("chk"))
    run_id: str
    step_id: str
    trace_id: str
    state_snapshot: Dict[str, Any]
    evidence_ids: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Evidence(BaseModel):
    """操作證據與截圖索引"""
    evidence_id: str = Field(default_factory=lambda: generate_trace_id("evd"))
    run_id: str
    step_id: str
    event_timestamp: str
    screenshot_path: Optional[str] = None
    raw_event_payload: Dict[str, Any] = Field(default_factory=dict)
    hash_digest: str
    is_masked: bool = True


class Approval(BaseModel):
    """二次確認與治理核准單」"""
    approval_id: str = Field(default_factory=lambda: generate_trace_id("appr"))
    scope_id: str
    action_name: str
    requested_by: str
    approved_by: Optional[str] = None
    status: str = Field(default="PENDING", description="PENDING | APPROVED | DECLINED")
    one_time_grant: bool = True


class SourceReference(BaseModel):
    """規格或參考文件引用」"""
    source_id: str = Field(default_factory=lambda: generate_trace_id("src"))
    title: str
    version: str
    effective_date: str
    doc_type: str = Field(description="PDF | WORD | PPT | WEB_HELP | STRUCTURED")
    citation_text: str


class ManualDraft(BaseModel):
    """手冊草稿實體」"""
    draft_id: str = Field(default_factory=lambda: generate_trace_id("dft"))
    workflow_version_id: str
    title: str
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    is_approved: bool = False


class Publication(BaseModel):
    """正式/草稿發布成品」"""
    publication_id: str = Field(default_factory=lambda: generate_trace_id("pub"))
    draft_id: str
    variant_key: str
    pptx_path: str
    publication_gate_passed: bool = False
    is_draft: bool = True
    signed_off_by: Optional[str] = None


class WorkflowVersion(BaseModel):
    """正規化流程圖與版本實體」"""
    version_id: str = Field(default_factory=lambda: generate_trace_id("ver"))
    project_id: str
    version_number: int = 1
    parent_version_id: Optional[str] = None
    is_committed: bool = False
    states: List[State] = Field(default_factory=list)
    steps: List[Step] = Field(default_factory=list)
    transitions: List[Transition] = Field(default_factory=list)
    branches: List[Branch] = Field(default_factory=list)
