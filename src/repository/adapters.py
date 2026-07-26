"""
ManualPPT 儲存庫適配器 (Repository Adapters & Durable Agent Checkpoint Storage)
"""

import json
from typing import List, Optional
from sqlalchemy.orm import Session
from src.domain.models import Checkpoint, WorkflowVersion
from src.repository.db import CheckpointORM, WorkflowVersionORM


class WorkflowRepositoryAdapter:
    """流程版本持久化適配器"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, workflow: WorkflowVersion) -> WorkflowVersion:
        data_json = workflow.model_dump_json()
        orm_obj = WorkflowVersionORM(
            version_id=workflow.version_id,
            project_id=workflow.project_id,
            version_number=workflow.version_number,
            parent_version_id=workflow.parent_version_id,
            is_committed=workflow.is_committed,
            serialized_json=data_json
        )
        self.session.merge(orm_obj)
        self.session.commit()
        return workflow

    def get_by_id(self, version_id: str) -> Optional[WorkflowVersion]:
        orm_obj = self.session.query(WorkflowVersionORM).filter_by(version_id=version_id).first()
        if not orm_obj:
            return None
        return WorkflowVersion.model_validate_json(orm_obj.serialized_json)


class CheckpointRepositoryAdapter:
    """Durable Agent Checkpoint 持久化適配器"""

    def __init__(self, session: Session):
        self.session = session

    def save_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        """保存可恢復的 Agent 檢查點"""
        orm_obj = CheckpointORM(
            checkpoint_id=checkpoint.checkpoint_id,
            run_id=checkpoint.run_id,
            step_id=checkpoint.step_id,
            trace_id=checkpoint.trace_id,
            state_snapshot_json=json.dumps(checkpoint.state_snapshot),
            evidence_ids_json=json.dumps(checkpoint.evidence_ids),
            created_at=checkpoint.created_at
        )
        self.session.merge(orm_obj)
        self.session.commit()
        return checkpoint

    def get_latest_checkpoint(self, run_id: str) -> Optional[Checkpoint]:
        """取得指定 ExecutionRun 最新的檢查點"""
        orm_obj = (
            self.session.query(CheckpointORM)
            .filter_by(run_id=run_id)
            .order_by(CheckpointORM.created_at.desc())
            .first()
        )
        if not orm_obj:
            return None

        return Checkpoint(
            checkpoint_id=orm_obj.checkpoint_id,
            run_id=orm_obj.run_id,
            step_id=orm_obj.step_id,
            trace_id=orm_obj.trace_id,
            state_snapshot=json.loads(orm_obj.state_snapshot_json),
            evidence_ids=json.loads(orm_obj.evidence_ids_json),
            created_at=orm_obj.created_at
        )
