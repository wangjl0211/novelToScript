"""用户设置 API。"""

import json
from pathlib import Path

from fastapi import APIRouter

from app.config import get_settings, reload_settings
from app.domain.models import SettingsResponse, SettingsUpdate
from app.infrastructure.llm_client import LLMClient

router = APIRouter(prefix="/api/settings", tags=["settings"])

SETTINGS_FILE = get_settings().data_dir / "user_settings.json"
llm_client = LLMClient()


def _load_user_settings() -> dict:
    if SETTINGS_FILE.exists():
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    return {}


def _save_user_settings(data: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("", response_model=SettingsResponse)
def get_settings_api():
    """获取当前设置（不含 API Key 明文）。"""
    settings = get_settings()
    user = _load_user_settings()
    return SettingsResponse(
        llm_provider=user.get("llm_provider", settings.llm_provider),
        llm_base_url=user.get("llm_base_url", settings.llm_base_url),
        llm_model=user.get("llm_model", settings.llm_model),
        llm_temperature=user.get("llm_temperature", settings.llm_temperature),
        llm_max_tokens=user.get("llm_max_tokens", settings.llm_max_tokens),
        has_api_key=llm_client.has_api_key(),
        max_concurrent_requests=user.get(
            "max_concurrent_requests", settings.max_concurrent_requests
        ),
        chapter_retry_count=user.get("chapter_retry_count", settings.chapter_retry_count),
        quality_mode=user.get("quality_mode", settings.quality_mode),
        mock_llm=user.get("mock_llm", settings.mock_llm),
    )


@router.put("", response_model=SettingsResponse)
def update_settings(body: SettingsUpdate):
    """更新用户设置。"""
    settings = get_settings()
    user = _load_user_settings()

    for field in [
        "llm_provider",
        "llm_base_url",
        "llm_model",
        "llm_temperature",
        "llm_max_tokens",
        "max_concurrent_requests",
        "chapter_retry_count",
        "quality_mode",
        "mock_llm",
    ]:
        val = getattr(body, field, None)
        if val is not None:
            user[field] = val
            setattr(settings, field, val)

    if body.api_key:
        llm_client.set_api_key(body.api_key)

    _save_user_settings(user)
    reload_settings()
    return get_settings_api()
