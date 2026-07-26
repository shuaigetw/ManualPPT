"""
Audience Variants and Lifecycle 測試 (7.1 - 7.7)
"""

import pytest
from src.config import RetentionDefaults
from src.domain.models import ActionType, AudienceProfile, State, Step, TargetElement, WorkflowVersion
from src.service.audience import AudienceRenderer
from src.service.drafting import EvidenceBoundDraftEngine
from src.service.retention import RetentionService


def test_audience_rendering_and_preview():
    st = State(name="Step 1", page_url="http://localhost")
    step = Step(
        state_id=st.state_id,
        action_type=ActionType.CLICK,
        target_element=TargetElement(role="button", name="Submit Secret Field"),
        purpose="提交敏感資料"
    )
    wf = WorkflowVersion(project_id="p1", states=[st], steps=[step])

    draft_engine = EvidenceBoundDraftEngine()
    draft = draft_engine.generate_draft(wf, [], [], "trc_aud")

    renderer = AudienceRenderer()

    # Executive Profile
    exec_prof = AudienceProfile(proficiency="experienced", org_level="executive", purpose="overview", language="zh-TW")
    exec_rendered = renderer.render_for_audience(draft, exec_prof)

    assert "executive" in exec_rendered.sections[0]["title"]
    assert "[高階摘要]" in exec_rendered.sections[0]["steps"][0]["purpose"]

    # Preview
    preview = renderer.preview_variant_generation([exec_prof], base_step_count=1)
    assert preview.total_variants_count == 1
    assert preview.estimated_slides_per_variant == 2


def test_retention_service():
    retention_defaults = RetentionDefaults()
    service = RetentionService(retention_defaults)

    report = service.execute_cleanup()
    assert report.deleted_raw_videos_count == 0
    assert report.deleted_audits_count == 0
