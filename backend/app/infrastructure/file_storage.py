"""本地文件存储。"""

import json
import shutil
import uuid
from pathlib import Path

from app.config import get_settings
from app.domain.models import Chapter, ParsedNovel


class FileStorage:
    """项目文件读写。"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.root = self.settings.data_dir / "projects"
        self.root.mkdir(parents=True, exist_ok=True)

    def project_dir(self, project_id: str) -> Path:
        path = self.root / project_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def source_dir(self, project_id: str) -> Path:
        path = self.project_dir(project_id) / "source"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def output_dir(self, project_id: str) -> Path:
        path = self.project_dir(project_id) / "output"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_upload(self, project_id: str, filename: str, content: bytes) -> Path:
        """保存上传的原始文件。"""
        dest = self.source_dir(project_id) / filename
        dest.write_bytes(content)
        return dest

    def save_novel(self, project_id: str, novel: ParsedNovel) -> None:
        """保存解析后的小说 JSON。"""
        data = novel.model_dump()
        path = self.project_dir(project_id) / "novel.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_novel(self, project_id: str) -> ParsedNovel | None:
        """加载解析后的小说。"""
        path = self.project_dir(project_id) / "novel.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return ParsedNovel.model_validate(data)

    def save_chapters_override(self, project_id: str, chapters: list[Chapter]) -> None:
        """保存用户手动调整后的章节。"""
        novel = self.load_novel(project_id)
        if novel is None:
            raise FileNotFoundError("未找到小说数据")
        novel.chapters = chapters
        self.save_novel(project_id, novel)

    def save_script_yaml(self, project_id: str, yaml_content: str) -> Path:
        """保存剧本 YAML。"""
        path = self.output_dir(project_id) / "script.yaml"
        path.write_text(yaml_content, encoding="utf-8")
        return path

    def load_script_yaml(self, project_id: str) -> str | None:
        """加载剧本 YAML。"""
        path = self.output_dir(project_id) / "script.yaml"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def script_exists(self, project_id: str) -> bool:
        return (self.output_dir(project_id) / "script.yaml").exists()

    def delete_project_files(self, project_id: str) -> None:
        """删除项目所有文件。"""
        path = self.root / project_id
        if path.exists():
            shutil.rmtree(path)


def new_project_id() -> str:
    return str(uuid.uuid4())
