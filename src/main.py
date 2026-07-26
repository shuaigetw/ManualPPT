"""
ManualPPT FastAPI Sidecar 服務進入點 (Main Entrypoint)

串接本機 Extension 擷取事件、檔案匯入、受治理執行、手冊生成與 PowerPoint 發布 API。
"""

import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.config import settings
from src.core.audit import AuditLogStore, AuditEvent, AuditEventType
from src.core.tracing import generate_trace_id
from src.domain.models import ApplicationScope, WorkflowVersion, ManualDraft
from src.repository.db import DatabaseManager
from src.repository.adapters import WorkflowRepositoryAdapter, CheckpointRepositoryAdapter
from src.service.capture import DesktopSessionController, EvidenceIngestionService, RawCaptureEvent
from src.service.discovery import DiscoveryService, DiscoveryAnswers, FeatureInventory
from src.service.ingestion import DocumentIngestionService
from src.service.drafting import EvidenceBoundDraftEngine, PublicationGate
from src.service.pptx_generator import PowerPointGenerator
from src.service.governance import GovernanceService

app = FastAPI(
    title="ManualPPT Sidecar Service",
    description="FastAPI Sidecar for Tauri Desktop & Chrome Extension Capture",
    version=settings.version
)

# 允許 Tauri (localhost) 與 Extension 跨網域存取
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_manager = DatabaseManager()
audit_store = AuditLogStore()
gov_service = GovernanceService(audit_store)
capture_controller = DesktopSessionController()
evidence_service = EvidenceIngestionService()
ingest_service = DocumentIngestionService()


class IngestDocRequest(BaseModel):
    title: str
    version: str
    effective_date: str
    doc_type: str
    content_text: str


class EventsListRequest(BaseModel):
    events: List[RawCaptureEvent]


class PublishRequest(BaseModel):
    draft_id: str
    signed_off_by: Optional[str] = None
    is_formal: bool = False
    output_filename: str = "output_manual.pptx"


@app.get("/api/health")
def health_check():
    """健康檢查"""
    return {"status": "OK", "version": settings.version}


@app.post("/api/ingest")
def ingest_document(req: IngestDocRequest):
    """匯入 SOP 規格文件"""
    src = ingest_service.ingest_text_document(
        title=req.title,
        version=req.version,
        effective_date=req.effective_date,
        doc_type=req.doc_type,
        content_text=req.content_text
    )
    return {"status": "SUCCESS", "source_id": src.source_id}


@app.post("/api/capture/events")
def receive_captured_events(req: EventsListRequest):
    """接收來自 Chrome Extension 傳回的瀏覽器操作事件"""
    capture_controller.buffer_incoming_events(req.events)
    return {"status": "BUFFERED", "count": len(req.events)}


@app.post("/api/publish")
def generate_pptx_manual(req: PublishRequest, db: Session = Depends(db_manager.get_session)):
    """審核並產出作業手冊 PowerPoint 簡報"""
    # 建立 Dummy Draft
    wf = WorkflowVersion(project_id="prj_default")
    draft = EvidenceBoundDraftEngine().generate_draft(wf, [], ingest_service.sources, "trc_pub")
    
    gate = PublicationGate()
    can_publish, reasons = gate.evaluate_publication(
        draft=draft,
        unresolved_conflicts_count=len(ingest_service.detect_conflicts()),
        signed_off_by=req.signed_off_by
    )

    if req.is_formal and not can_publish:
        raise HTTPException(status_code=400, detail={"message": "未通過發布審核閘門", "reasons": reasons})

    output_path = os.path.abspath(req.output_filename)
    PowerPointGenerator().generate_presentation(draft, output_path, is_formal=req.is_formal)

    return {
        "status": "SUCCESS",
        "pptx_path": output_path,
        "is_formal": req.is_formal,
        "publication_gate_passed": can_publish,
        "reasons": reasons
    }
