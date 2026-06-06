"""剧本导出服务。"""

import json
from typing import Any

from app.services.yaml_handler import YAMLHandler


class ExportService:
    """多格式剧本导出。"""

    def __init__(self) -> None:
        self.yaml_handler = YAMLHandler()

    def export(self, yaml_content: str, fmt: str) -> tuple[str, str, str]:
        """
        导出剧本。
        返回 (内容, MIME 类型, 文件扩展名)
        """
        fmt = fmt.lower()
        if fmt == "yaml":
            return yaml_content, "application/x-yaml", "yaml"
        if fmt == "json":
            data = self.yaml_handler.parse_yaml(yaml_content)
            return (
                json.dumps(data, ensure_ascii=False, indent=2),
                "application/json",
                "json",
            )
        if fmt == "fountain":
            data = self.yaml_handler.parse_yaml(yaml_content)
            return self._to_fountain(data), "text/plain", "fountain"
        raise ValueError(f"不支持的导出格式: {fmt}")

    def _to_fountain(self, data: dict[str, Any]) -> str:
        """将 YAML 剧本转为 Fountain 格式。"""
        script = data.get("script", {})
        meta = script.get("meta", {})
        lines: list[str] = [
            f"Title: {meta.get('title', '未命名')}",
            f"Author: {meta.get('author', '')}",
            "",
        ]

        char_map = {c["id"]: c["name"] for c in script.get("characters", [])}

        for act in script.get("acts", []):
            lines.append(f"/* 第 {act.get('act_number', 1)} 幕: {act.get('title', '')} */")
            lines.append("")
            for scene in act.get("scenes", []):
                heading = scene.get("heading", {})
                display = heading.get("display") or (
                    f"{heading.get('int_ext', 'INT')}. {heading.get('location', '')}"
                    f" - {heading.get('time_of_day', '')}"
                )
                lines.append(display.upper())
                lines.append("")

                for block in scene.get("blocks", []):
                    btype = block.get("type")
                    if btype == "action":
                        lines.append(block.get("text", ""))
                        lines.append("")
                    elif btype == "dialogue":
                        char_name = char_map.get(block.get("character_id", ""), "未知")
                        lines.append(char_name.upper())
                        if block.get("parenthetical"):
                            lines.append(f"({block['parenthetical']})")
                        for line in block.get("lines", []):
                            lines.append(line)
                        lines.append("")
                    elif btype == "parenthetical":
                        lines.append(f"({block.get('text', '')})")
                        lines.append("")
                    elif btype == "transition":
                        lines.append(f"> {block.get('text', '')}")
                        lines.append("")
                    elif btype == "voiceover":
                        char_name = char_map.get(block.get("character_id", ""), "旁白")
                        lines.append(f"{char_name.upper()} (V.O.)")
                        lines.append(block.get("text", ""))
                        lines.append("")

        return "\n".join(lines)
