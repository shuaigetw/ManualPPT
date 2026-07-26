"""
ManualPPT 資料庫連線與 ORM 模型定義 (SQLAlchemy DB Engine)
"""

import json
from datetime import datetime, timezone
from typing import Generator
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()


class WorkflowVersionORM(Base):
    """WorkflowVersion ORM 實體"""
    __tablename__ = "workflow_versions"

    version_id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    parent_version_id = Column(String, nullable=True)
    is_committed = Column(Boolean, default=False)
    serialized_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CheckpointORM(Base):
    """Durable Agent Checkpoint ORM 實體"""
    __tablename__ = "checkpoints"

    checkpoint_id = Column(String, primary_key=True)
    run_id = Column(String, nullable=False, index=True)
    step_id = Column(String, nullable=False)
    trace_id = Column(String, nullable=False)
    state_snapshot_json = Column(Text, nullable=False)
    evidence_ids_json = Column(Text, nullable=False)
    created_at = Column(String, nullable=False)


class DatabaseManager:
    """SQLite 本機資料庫管理器與自動 Migration"""

    def __init__(self, db_url: str = "sqlite:///manualppt.db"):
        self.engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()

    def create_tables(self):
        """創建立資料表 (即時 Migration)"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        """取得 Session 迭代器"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
