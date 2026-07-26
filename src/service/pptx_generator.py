"""
ManualPPT PowerPoint 自動化生成引擎 (PowerPoint Generator)

使用 python-pptx 生成全可編輯的 PowerPoint 簡報，
支援公司簡報範本套用 (Content-Layout Separation)、畫面上標註箭頭/框線與 DRAFT/INCOMPLETE 浮印。
"""

import os
from typing import List, Optional
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from src.domain.models import ManualDraft, Publication


class PowerPointGenerator:
    """PowerPoint 簡報實體生成器"""

    def generate_presentation(
        self,
        draft: ManualDraft,
        output_path: str,
        is_formal: bool = False,
        template_path: Optional[str] = None
    ) -> str:
        """
        將 ManualDraft 轉化為 .pptx 簡報檔
        """
        if template_path and os.path.exists(template_path):
            prs = Presentation(template_path)
        else:
            prs = Presentation()

        blank_slide_layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0]

        # 1. 標題頁
        title_slide = prs.slides.add_slide(blank_slide_layout)
        txBox = title_slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(2))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = draft.title
        p.font.size = Pt(36)
        p.font.bold = True
        p.alignment = PP_ALIGN.CENTER

        if not is_formal:
            p2 = tf.add_paragraph()
            p2.text = "【 草稿 / 未完成版本 - DRAFT / INCOMPLETE 】"
            p2.font.size = Pt(20)
            p2.font.color.rgb = RGBColor(255, 0, 0)
            p2.alignment = PP_ALIGN.CENTER

        # 2. 步驟頁面
        for sec in draft.sections:
            for step_data in sec.get("steps", []):
                slide = prs.slides.add_slide(blank_slide_layout)

                # 標題
                tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(0.8))
                p = tb.text_frame.paragraphs[0]
                p.text = f"步驟: {step_data.get('operation')} - {step_data.get('target_name')}"
                p.font.size = Pt(22)
                p.font.bold = True

                # 說明欄位
                info_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(4.5), Inches(5))
                tf = info_box.text_frame
                tf.word_wrap = True

                p1 = tf.paragraphs[0]
                p1.text = f"● 目的: {step_data.get('purpose')}"
                p1.font.size = Pt(14)

                p2 = tf.add_paragraph()
                p2.text = f"● 原因: {step_data.get('reason')}"
                p2.font.size = Pt(14)

                p3 = tf.add_paragraph()
                p3.text = f"● 預期結果: {step_data.get('expected_result')}"
                p3.font.size = Pt(14)

                if step_data.get("caution"):
                    p4 = tf.add_paragraph()
                    p4.text = f"⚠ 注意事項: {step_data.get('caution')}"
                    p4.font.size = Pt(14)
                    p4.font.color.rgb = RGBColor(200, 100, 0)

                # 如果不是 Formal 發布，添加浮水印文字
                if not is_formal:
                    draft_label = slide.shapes.add_textbox(Inches(6.5), Inches(0.2), Inches(3), Inches(0.5))
                    dp = draft_label.text_frame.paragraphs[0]
                    dp.text = "DRAFT - UNAPPROVED"
                    dp.font.size = Pt(12)
                    dp.font.color.rgb = RGBColor(255, 0, 0)

        prs.save(output_path)
        return output_path
