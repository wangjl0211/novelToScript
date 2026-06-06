"""LLM 客户端封装，支持 OpenAI 兼容 API 与 Mock 模式。"""

import json
import re
from pathlib import Path
from typing import Any

import keyring
from jinja2 import Environment, FileSystemLoader
from openai import AsyncOpenAI

from app.config import get_settings

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class LLMClient:
    """大语言模型调用客户端。"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.jinja = Environment(
            loader=FileSystemLoader(str(PROMPTS_DIR)),
            autoescape=False,
        )

    def get_api_key(self) -> str | None:
        """从钥匙串或环境变量获取 API Key。"""
        try:
            key = keyring.get_password(
                self.settings.keyring_service,
                self.settings.keyring_username,
            )
            if key:
                return key
        except Exception:
            pass
        import os

        return os.environ.get("LLM_API_KEY")

    def set_api_key(self, api_key: str) -> None:
        """保存 API Key 到系统钥匙串。"""
        keyring.set_password(
            self.settings.keyring_service,
            self.settings.keyring_username,
            api_key,
        )

    def has_api_key(self) -> bool:
        return bool(self.get_api_key())

    def _resolve_model(self) -> str:
        mode = self.settings.quality_mode
        return self.settings.quality_model_map.get(mode, self.settings.llm_model)

    def _build_client(self) -> AsyncOpenAI | None:
        if self.settings.mock_llm:
            return None
        api_key = self.get_api_key()
        if not api_key:
            return None
        return AsyncOpenAI(
            api_key=api_key,
            base_url=self.settings.llm_base_url,
        )

    def render_prompt(self, template_name: str, **kwargs: Any) -> str:
        """渲染 Jinja2 Prompt 模板。"""
        template = self.jinja.get_template(template_name)
        return template.render(**kwargs)

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """从 LLM 响应中提取 JSON。"""
        text = text.strip()
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # 提取 markdown 代码块
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            return json.loads(match.group(1).strip())
        # 提取首个 JSON 对象
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        raise ValueError("无法从 LLM 响应中解析 JSON")

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """调用 LLM 并返回 JSON 对象。"""
        if self.settings.mock_llm or not self._build_client():
            return self._mock_response(user_prompt)

        client = self._build_client()
        assert client is not None

        response = await client.chat.completions.create(
            model=self._resolve_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature or self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        return self._extract_json(content)

    def _mock_response(self, user_prompt: str) -> dict[str, Any]:
        """Mock 模式：返回符合 Prompt 类型的示例 JSON。"""
        if "全书分析" in user_prompt or "global" in user_prompt.lower():
            return {
                "title": "示例剧本",
                "logline": "一个关于成长与选择的故事。",
                "global_summary": "主角在困境中寻找自我，最终完成蜕变。",
                "characters": [
                    {
                        "id": "liming",
                        "name": "李明",
                        "aliases": [],
                        "description": "故事主角，性格内敛坚韧。",
                    },
                    {
                        "id": "xiaohong",
                        "name": "小红",
                        "aliases": [],
                        "description": "李明的朋友，开朗活泼。",
                    },
                ],
                "relationships": "李明与小红是多年好友。",
            }
        if "元素提取" in user_prompt or "extract" in user_prompt.lower():
            return {
                "summary": "本章讲述主角与好友的一次重要谈话。",
                "characters": [
                    {"id": "liming", "name": "李明", "aliases": [], "description": "主角"},
                ],
                "locations": [
                    {"id": "cafe", "name": "街角咖啡馆", "description": "小型咖啡馆", "interior": True},
                ],
                "time_markers": ["下午"],
                "props": ["咖啡杯"],
                "inner_thoughts": [{"character_id": "liming", "text": "他在犹豫是否该说出真相。"}],
            }
        # 默认：章节剧本
        return {
            "scenes": [
                {
                    "heading": {
                        "int_ext": "INT",
                        "location": "街角咖啡馆",
                        "time_of_day": "日",
                    },
                    "time": "下午",
                    "cast": ["liming", "xiaohong"],
                    "props": ["咖啡杯"],
                    "summary": "两人在咖啡馆交谈。",
                    "blocks": [
                        {
                            "type": "action",
                            "text": "李明坐在靠窗的位置，手指无意识地摩挲着咖啡杯。",
                        },
                        {
                            "type": "dialogue",
                            "character_id": "xiaohong",
                            "lines": ["你最近怎么了？看起来心事重重的。"],
                        },
                        {
                            "type": "voiceover",
                            "character_id": "liming",
                            "text": "真相就在嘴边，却怎么也说不出口。",
                        },
                    ],
                }
            ]
        }
