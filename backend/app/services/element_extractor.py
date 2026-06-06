"""AI 元素提取服务。"""

from typing import Any

from app.domain.models import Chapter, StoryContext
from app.infrastructure.llm_client import LLMClient


class ElementExtractor:
    """从章节文本中提取剧本元素。"""

    SYSTEM_PROMPT = (
        "你是一位资深影视编剧与剧本分析专家。"
        "请严格按 JSON 格式输出，不得添加任何解释性文字。"
        "不得改变原作情节，不得新增或删除角色。"
    )

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    async def analyze_novel(self, chapters: list[Chapter]) -> dict[str, Any]:
        """全书分析：提取主角、关系网、故事线。"""
        # 取各章前 500 字作为样本
        samples = []
        for ch in chapters[:10]:
            samples.append(f"【{ch.title}】\n{ch.content[:500]}...")
        overview = "\n\n".join(samples)

        user_prompt = self.llm.render_prompt(
            "analyze.j2",
            overview=overview,
            chapter_count=len(chapters),
        )
        return await self.llm.chat_json(self.SYSTEM_PROMPT, user_prompt)

    async def extract_chapter_elements(
        self,
        chapter: Chapter,
        context: StoryContext,
    ) -> dict[str, Any]:
        """单章元素提取。"""
        user_prompt = self.llm.render_prompt(
            "extract.j2",
            chapter_title=chapter.title,
            chapter_index=chapter.index,
            chapter_content=chapter.content[:12000],
            global_summary=context.global_summary,
            characters=context.characters,
            previous_summaries=context.previous_summaries[-3:],
        )
        return await self.llm.chat_json(self.SYSTEM_PROMPT, user_prompt)

    async def convert_chapter_to_script(
        self,
        chapter: Chapter,
        context: StoryContext,
        elements: dict[str, Any],
    ) -> dict[str, Any]:
        """基于元素提取结果生成章节剧本块。"""
        user_prompt = self.llm.render_prompt(
            "convert.j2",
            chapter_title=chapter.title,
            chapter_index=chapter.index,
            chapter_content=chapter.content[:12000],
            global_summary=context.global_summary,
            characters=context.characters,
            elements=elements,
        )
        return await self.llm.chat_json(self.SYSTEM_PROMPT, user_prompt)
