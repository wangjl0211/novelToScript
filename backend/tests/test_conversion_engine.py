"""转换引擎 Mock 测试。"""

import pytest

from app.infrastructure.file_storage import FileStorage
from app.services.conversion_engine import ConversionEngine
from app.services.import_parser import parse_novel_file

SAMPLE = """第一章 开端

李明走进房间。小红向他招手。

第二章 转折

两人在咖啡馆交谈，气氛微妙。

第三章 结局

李明做出了决定，故事落下帷幕。
"""


@pytest.fixture
def project_with_novel(tmp_path, monkeypatch):
    """创建带小说数据的临时项目。"""
    from app.config import reload_settings

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MOCK_LLM", "true")
    reload_settings()

    storage = FileStorage()
    project_id = "test-project-001"
    novel = parse_novel_file("sample.txt", SAMPLE.encode("utf-8"))
    storage.save_novel(project_id, novel)
    return project_id, storage


@pytest.mark.asyncio
async def test_convert_project_mock(project_with_novel):
    project_id, _ = project_with_novel
    engine = ConversionEngine()
    result = await engine.convert_project(project_id)

    assert result.success
    assert result.script_yaml
    assert "script:" in result.script_yaml
