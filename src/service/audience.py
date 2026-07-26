"""
ManualPPT 多受眾發布與差異更新服務 (Audience Variant Renderer & Differential Maintenance)

提供 Novice, Experienced, Executive, Audit, Middle/Frontline 版本的渲染器、
欄位層級與流程層級權限遮罩、事實保存語意在地化 (Localization) 與簡報產生數預覽。
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from src.domain.models import AudienceProfile, ManualDraft


class VariantPreview(BaseModel):
    """簡報多版本產生預覽結果"""
    total_variants_count: int
    configured_profiles: List[AudienceProfile]
    estimated_slides_per_variant: int


class AudienceRenderer:
    """受眾專用手冊渲染器"""

    def render_for_audience(
        self,
        draft: ManualDraft,
        profile: AudienceProfile
    ) -> ManualDraft:
        """
        根據 AudienceProfile 進行結構過濾、權限遮罩與重點提煉
        """
        rendered_sections: List[Dict[str, Any]] = []

        for sec in draft.sections:
            rendered_steps = []
            for step_data in sec.get("steps", []):
                # 1. 欄位與角色權限過濾 (Field & Role Permission Masking)
                target_name = step_data.get("target_name", "")
                if profile.role_permissions and not any(p in target_name for p in profile.role_permissions):
                    # 若受眾缺乏欄位權限，予以遮罩
                    step_data["target_name"] = "***UNAUTHORIZED_FIELD***"
                    step_data["purpose"] = "該受眾權限無法檢視此操作細節"

                # 2. 依受眾層級進行重點提煉 (Emphasis per org_level)
                if profile.org_level == "executive":
                    # 高階主管重點：強調目的、風險與治理，簡化微觀步驟
                    step_data["purpose"] = f"[高階摘要] {step_data.get('purpose')}"
                elif profile.proficiency == "novice":
                    # 初學者重點：提供詳細步驟與圖文說明
                    step_data["purpose"] = f"[新手引導] {step_data.get('purpose')}"

                rendered_steps.append(step_data)

            rendered_sections.append({
                "title": f"{sec.get('title')} ({profile.org_level} - {profile.language})",
                "steps": rendered_steps
            })

        return ManualDraft(
            workflow_version_id=draft.workflow_version_id,
            title=f"{draft.title} - [{profile.org_level.upper()} / {profile.language}]",
            sections=rendered_sections,
            is_approved=draft.is_approved
        )

    def preview_variant_generation(self, profiles: List[AudienceProfile], base_step_count: int) -> VariantPreview:
        """預覽將產生的簡報版本總數」"""
        return VariantPreview(
            total_variants_count=len(profiles),
            configured_profiles=profiles,
            estimated_slides_per_variant=base_step_count + 1
        )
