"""
ManualPPT 全域組態設定模組 (Configuration Settings)

定義系統功能旗標 (Feature Flags)、本機/Staging 白名單、測試帳號政策與資料保留預設值。
"""

from typing import List, Set
from pydantic import BaseModel, Field


class FeatureFlags(BaseModel):
    """系統功能旗標設定"""
    readonly_discovery: bool = Field(default=True, description="唯讀探索模式")
    hybrid_capture: bool = Field(default=True, description="混合式錄製模式")
    governed_execution: bool = Field(default=True, description="受治理自動化執行")
    evidence_generation: bool = Field(default=True, description="證據鏈導向手冊生成")
    audience_publishing: bool = Field(default=True, description="多受眾簡報發布")


class OriginAllowlistConfig(BaseModel):
    """執行環境白名單設定 (僅允許 localhost 及 Staging 網域)"""
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost",
            "http://127.0.0.1",
            "https://localhost",
            "https://127.0.0.1",
        ],
        description="允許執行的 Origin 清單"
    )
    allowed_origin_patterns: List[str] = Field(
        default=[
            r"^http://localhost(:\d+)?$",
            r"^http://127\.0\.0\.1(:\d+)?$",
            r"^https://.*\.staging\.internal(:\d+)?$",
        ],
        description="允許執行的 Regex 正則表達式清單"
    )

    def is_origin_allowed(self, origin: str) -> bool:
        """
        驗證 Target Origin 是否符合白名單規定
        """
        import re
        normalized = origin.strip().rstrip("/")
        if normalized in self.allowed_origins:
            return True
        for pattern in self.allowed_origin_patterns:
            if re.match(pattern, normalized):
                return True
        return False


class FixtureAccountPolicy(BaseModel):
    """測試帳號與合成資料政策"""
    require_fixture_account: bool = Field(default=True, description="強制要求使用測試帳號")
    allow_production_credentials: bool = Field(default=False, description="嚴禁使用正式環境憑證")
    allowed_account_prefixes: List[str] = Field(
        default=["test_", "fixture_", "demo_", "mock_"],
        description="允許使用的測試帳號前綴"
    )


class RetentionDefaults(BaseModel):
    """資料保留政策預設天數 (Retention Policies)"""
    raw_video_days: int = Field(default=7, description="原始錄影天數")
    screenshot_days: int = Field(default=30, description="截圖保留天數")
    evidence_days: int = Field(default=90, description="工作流程證據天數")
    audit_log_days: int = Field(default=365, description="稽核日誌保留天數")
    publication_days: int = Field(default=365, description="發布手冊保留天數")


class AppConfig(BaseModel):
    """ManualPPT 系統總設定"""
    version: str = Field(default="1.0.0", description="系統版本號")
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)
    origin_allowlist: OriginAllowlistConfig = Field(default_factory=OriginAllowlistConfig)
    fixture_policy: FixtureAccountPolicy = Field(default_factory=FixtureAccountPolicy)
    retention: RetentionDefaults = Field(default_factory=RetentionDefaults)


# 全域單例設定實例
settings = AppConfig()
