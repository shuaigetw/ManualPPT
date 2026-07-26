"""
Manual Drafting and PowerPoint 測試 (6.1 - 6.7)
"""

import os
import pytest
from src.domain.models import ActionType, State, Step, TargetElement, WorkflowVersion
from src.service.drafting import EvidenceBoundDraftEngine, PublicationGate
from src.service.pptx_generator import PowerPointGenerator


def test_draft_engine_and_publication_gate():
    st = State(name="Step 1", page_url="http://localhost")
    step = Step(
        state_id=st.state_id,
        action_type=ActionType.CLICK,
        target_element=TargetElement(role="button", name="Submit"),
        purpose="提交表單"
    )
    wf = WorkflowVersion(project_id="p1", states=[st], steps=[step])

    engine = EvidenceBoundDraftEngine()
    draft = engine.generate_draft(wf, [], [], "trc_draft_test")

    assert draft.title == "標準作業手冊草稿"
    assert len(draft.sections[0]["steps"]) == 1

    gate = PublicationGate()
    # 尚無簽核且包含未確認欄位 -> 無法正式發布
    can_pub, reasons = gate.evaluate_publication(draft, unresolved_conflicts_count=0, signed_off_by=None)
    assert can_pub is False
    assert "尚未取得負責人正式簽核 (signed_off_by)" in reasons

    # 補足簽核且移除未確認欄位 -> 可以正式發布
    draft.sections[0]["steps"][0]["is_pending_confirmation"] = False
    can_pub_2, reasons_2 = gate.evaluate_publication(draft, unresolved_conflicts_count=0, signed_off_by="Manager_Alice")
    assert can_pub_2 is True


def test_pptx_generator(tmp_path):
    st = State(name="Step 1", page_url="http://localhost")
    step = Step(
        state_id=st.state_id,
        action_type=ActionType.CLICK,
        target_element=TargetElement(role="button", name="Submit"),
        purpose="提交表單"
    )
    wf = WorkflowVersion(project_id="p1", states=[st], steps=[step])

    engine = EvidenceBoundDraftEngine()
    draft = engine.generate_draft(wf, [], [], "trc_draft_test")

    generator = PowerPointGenerator()
    out_file = str(tmp_path / "test_manual.pptx")
    result_path = generator.generate_presentation(draft, out_file, is_formal=False)

    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 0
