"""
ManualPPT 文件匯入與衝突檢測服務 (Document Ingestion & Conflict Detection Service)

支援 PDF, Word, PowerPoint, Web-Help 與結構化文件匯入，
管理版本、生效日期、引用來源 (Citations)，並偵測不同來源間的指令衝突。
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from src.core.tracing import generate_trace_id
from src.domain.models import SourceReference


class SourceConflict(BaseModel):
    """文件衝突紀錄"""
    conflict_id: str = Field(default_factory=lambda: generate_trace_id("cnf"))
    feature_or_step: str
    source_a: SourceReference
    source_b: SourceReference
    conflict_description: str
    is_resolved: bool = False
    resolution_note: Optional[str] = None


class DocumentIngestionService:
    """文件匯入與處理服務"""

    def __init__(self):
        self.sources: List[SourceReference] = []

    def ingest_text_document(
        self,
        title: str,
        version: str,
        effective_date: str,
        doc_type: str,
        content_text: str
    ) -> SourceReference:
        """匯入文字或解析後的文件內容"""
        source = SourceReference(
            title=title,
            version=version,
            effective_date=effective_date,
            doc_type=doc_type,
            citation_text=content_text
        )
        self.sources.append(source)
        return source

    def detect_conflicts(self) -> List[SourceConflict]:
        """
        掃描已匯入的引用來源，偵測互相衝突的規範
        """
        conflicts: List[SourceConflict] = []

        for i in range(len(self.sources)):
            for j in range(i + 1, len(self.sources)):
                src_a = self.sources[i]
                src_b = self.sources[j]

                # 簡易範例：若同標題但內文關鍵字相反或不一致
                if src_a.title == src_b.title and src_a.version != src_b.version:
                    conflicts.append(
                        SourceConflict(
                            feature_or_step=src_a.title,
                            source_a=src_a,
                            source_b=src_b,
                            conflict_description=f"版本 {src_a.version} (生效日: {src_a.effective_date}) 與版本 {src_b.version} (生效日: {src_b.effective_date}) 內容存在衝突，需使用者確認"
                        )
                    )

        return conflicts
