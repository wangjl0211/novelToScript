"""YAML 序列化与 Schema 校验。"""

from datetime import datetime, timezone
from typing import Any

import yaml
from ruamel.yaml import YAML

from app.domain.script_schema import validate_script_data


class YAMLHandler:
    """剧本 YAML 读写与校验。"""

    def __init__(self) -> None:
        self.yaml = YAML()
        self.yaml.default_flow_style = False
        self.yaml.allow_unicode = True
        self.yaml.width = 120

    def to_yaml_string(self, data: dict[str, Any]) -> str:
        """将 dict 序列化为 YAML 字符串。"""
        from io import StringIO

        stream = StringIO()
        self.yaml.dump(data, stream)
        return stream.getvalue()

    def parse_yaml(self, content: str) -> dict[str, Any]:
        """解析 YAML 字符串。"""
        return yaml.safe_load(content)

    def validate(self, data: dict[str, Any]) -> list[str]:
        """Schema 校验。"""
        return validate_script_data(data)

    def validate_yaml(self, content: str) -> tuple[dict[str, Any] | None, list[str]]:
        """解析并校验 YAML。"""
        try:
            data = self.parse_yaml(content)
        except yaml.YAMLError as e:
            return None, [f"YAML 解析错误: {e}"]
        if not isinstance(data, dict):
            return None, ["根节点必须是对象"]
        return data, self.validate(data)

    @staticmethod
    def build_script_document(
        title: str,
        author: str | None,
        global_data: dict[str, Any],
        chapter_scripts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """组装完整剧本文档。"""
        now = datetime.now(timezone.utc).isoformat()
        characters = global_data.get("characters", [])
        locations_map: dict[str, dict] = {}
        all_scenes: list[dict[str, Any]] = []
        scene_counter = 1

        for chap in chapter_scripts:
            chap_index = chap.get("chapter_index", 1)
            for scene in chap.get("scenes", []):
                loc_name = scene.get("heading", {}).get("location", "未知地点")
                loc_id = _slugify(loc_name)
                if loc_id not in locations_map:
                    locations_map[loc_id] = {
                        "id": loc_id,
                        "name": loc_name,
                        "description": "",
                        "interior": scene.get("heading", {}).get("int_ext", "INT") == "INT",
                    }

                heading = scene.get("heading", {})
                if "display" not in heading:
                    int_ext = heading.get("int_ext", "INT")
                    loc = heading.get("location", loc_name)
                    tod = heading.get("time_of_day", "日")
                    heading["display"] = f"{'内景' if int_ext == 'INT' else '外景'} {loc} - {tod}"

                all_scenes.append(
                    {
                        "scene_id": f"sc{scene_counter:03d}",
                        "chapter_source": chap_index,
                        "heading": heading,
                        "location_id": loc_id,
                        "time": scene.get("time", heading.get("time_of_day", "")),
                        "weather": scene.get("weather", ""),
                        "cast": scene.get("cast", []),
                        "props": scene.get("props", []),
                        "summary": scene.get("summary", ""),
                        "blocks": scene.get("blocks", []),
                    }
                )
                scene_counter += 1

        # 合并章节级新增人物
        for chap in chapter_scripts:
            for char in chap.get("characters", []):
                if not any(c.get("id") == char.get("id") for c in characters):
                    characters.append(char)

        return {
            "script": {
                "meta": {
                    "title": title,
                    "author": author or global_data.get("author", ""),
                    "source_novel": title,
                    "version": "1.0.0",
                    "created_at": now,
                    "updated_at": now,
                    "genre": global_data.get("genre", ""),
                    "logline": global_data.get("logline", ""),
                    "notes": global_data.get("notes", ""),
                },
                "characters": characters,
                "locations": list(locations_map.values()),
                "acts": [
                    {
                        "act_number": 1,
                        "title": "第一幕",
                        "summary": global_data.get("global_summary", ""),
                        "scenes": all_scenes,
                    }
                ],
            }
        }


def _slugify(name: str) -> str:
    """将中文/英文名称转为 ID。"""
    import re

    # 简单拼音替代：取前几个字符的 hash
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]", "", name)
    if cleaned.isascii():
        return cleaned.lower()[:20] or "location"
    # 中文用地名 hash
    return "loc_" + hex(abs(hash(name)))[2:10]
