"""应用配置模块。"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（backend 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "script.schema.json"


class Settings(BaseSettings):
    """全局配置，支持 .env 与环境变量。"""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="gpt-4o", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4096, alias="LLM_MAX_TOKENS")

    # 转换
    max_concurrent_requests: int = Field(default=3, alias="MAX_CONCURRENT_REQUESTS")
    chapter_retry_count: int = Field(default=2, alias="CHAPTER_RETRY_COUNT")
    quality_mode: str = Field(default="standard", alias="QUALITY_MODE")

    # 性能
    chapter_timeout_seconds: int = Field(default=120, alias="CHAPTER_TIMEOUT_SECONDS")
    total_timeout_seconds: int = Field(default=600, alias="TOTAL_TIMEOUT_SECONDS")

    # 开发
    mock_llm: bool = Field(default=False, alias="MOCK_LLM")
    data_dir: Path = Field(default=PROJECT_ROOT / "data", alias="DATA_DIR")

    # keyring 服务名
    keyring_service: str = "novelToScript"
    keyring_username: str = "llm_api_key"

    @property
    def quality_model_map(self) -> dict[str, str]:
        """质量模式对应的默认模型。"""
        return {
            "fast": "gpt-4o-mini",
            "standard": self.llm_model,
            "high": self.llm_model,
        }


def _merge_user_settings(settings: Settings) -> Settings:
    """合并用户自定义设置文件。"""
    user_file = settings.data_dir / "user_settings.json"
    if not user_file.exists():
        return settings
    import json

    user = json.loads(user_file.read_text(encoding="utf-8"))
    for key, val in user.items():
        if hasattr(settings, key):
            setattr(settings, key, val)
    return settings


@lru_cache
def get_settings() -> Settings:
    return _merge_user_settings(Settings())


def reload_settings() -> Settings:
    """清除缓存并重新加载设置。"""
    get_settings.cache_clear()
    return get_settings()
