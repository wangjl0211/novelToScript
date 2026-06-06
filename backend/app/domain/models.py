"""领域模型定义。"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ConversionStatus(str, Enum):
    """转换任务状态。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ChapterStatus(str, Enum):
    """单章转换状态。"""

    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Chapter(BaseModel):
    """小说章节。"""

    index: int
    title: str
    content: str
    word_count: int


class ParsedNovel(BaseModel):
    """解析后的小说结构。"""

    title: str
    author: str | None = None
    chapters: list[Chapter]


class StoryContext(BaseModel):
    """转换上下文：人物表与前章摘要。"""

    title: str
    global_summary: str = ""
    characters: list[dict[str, Any]] = Field(default_factory=list)
    previous_summaries: list[str] = Field(default_factory=list)


class ChapterScript(BaseModel):
    """单章剧本片段。"""

    chapter_index: int
    summary: str = ""
    characters: list[dict[str, Any]] = Field(default_factory=list)
    locations: list[dict[str, Any]] = Field(default_factory=list)
    scenes: list[dict[str, Any]] = Field(default_factory=list)


class ConversionProgress(BaseModel):
    """转换进度事件。"""

    project_id: str
    status: ConversionStatus
    total_chapters: int
    completed_chapters: int
    current_chapter: int | None = None
    message: str = ""
    chapter_statuses: dict[int, ChapterStatus] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)


class ConversionResult(BaseModel):
    """转换结果。"""

    success: bool
    script_yaml: str | None = None
    errors: list[str] = Field(default_factory=list)


class ProjectCreate(BaseModel):
    """创建项目请求。"""

    name: str
    description: str | None = None


class ProjectResponse(BaseModel):
    """项目响应。"""

    id: str
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    chapter_count: int = 0
    conversion_status: ConversionStatus = ConversionStatus.PENDING
    has_script: bool = False


class SettingsUpdate(BaseModel):
    """用户设置更新。"""

    llm_provider: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_temperature: float | None = None
    llm_max_tokens: int | None = None
    api_key: str | None = None
    max_concurrent_requests: int | None = None
    chapter_retry_count: int | None = None
    quality_mode: str | None = None
    mock_llm: bool | None = None


class SettingsResponse(BaseModel):
    """用户设置响应（不含完整 API Key）。"""

    llm_provider: str
    llm_base_url: str
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int
    has_api_key: bool
    max_concurrent_requests: int
    chapter_retry_count: int
    quality_mode: str
    mock_llm: bool
