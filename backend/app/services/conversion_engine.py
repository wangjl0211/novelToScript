"""AI 转换引擎：编排分章转换流程。"""

import asyncio
from typing import Any, Callable, Awaitable

from app.domain.models import (
    Chapter,
    ChapterScript,
    ChapterStatus,
    ConversionProgress,
    ConversionResult,
    ConversionStatus,
    ParsedNovel,
    StoryContext,
)
from app.infrastructure.file_storage import FileStorage
from app.infrastructure.llm_client import LLMClient
from app.services.element_extractor import ElementExtractor
from app.services.yaml_handler import YAMLHandler


class ConversionEngine:
    """小说转剧本转换引擎。"""

    def __init__(
        self,
        llm: LLMClient | None = None,
        storage: FileStorage | None = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self.extractor = ElementExtractor(self.llm)
        self.yaml_handler = YAMLHandler()
        self.storage = storage or FileStorage()
        from app.config import get_settings

        self.settings = get_settings()

    async def convert_project(
        self,
        project_id: str,
        on_progress: Callable[[ConversionProgress], Awaitable[None]] | None = None,
    ) -> ConversionResult:
        """主入口：逐章转换并合并为完整剧本。"""
        novel = self.storage.load_novel(project_id)
        if novel is None:
            return ConversionResult(success=False, errors=["未找到小说数据，请先上传文件"])

        if not self.llm.has_api_key() and not self.settings.mock_llm:
            return ConversionResult(
                success=False,
                errors=["未配置 API Key，请在设置页配置或启用 Mock 模式"],
            )

        total = len(novel.chapters)
        chapter_statuses = {ch.index: ChapterStatus.WAITING for ch in novel.chapters}
        logs: list[str] = []

        async def emit(
            status: ConversionStatus,
            completed: int,
            current: int | None = None,
            message: str = "",
        ) -> None:
            progress = ConversionProgress(
                project_id=project_id,
                status=status,
                total_chapters=total,
                completed_chapters=completed,
                current_chapter=current,
                message=message,
                chapter_statuses=chapter_statuses,
                logs=logs[-50:],
            )
            if on_progress:
                await on_progress(progress)

        await emit(ConversionStatus.RUNNING, 0, message="开始全书分析...")
        logs.append("开始全书分析")

        try:
            global_data = await self.extractor.analyze_novel(novel.chapters)
        except Exception as e:
            logs.append(f"全书分析失败: {e}")
            await emit(ConversionStatus.FAILED, 0, message=str(e))
            return ConversionResult(success=False, errors=[str(e)])

        logs.append("全书分析完成")
        context = StoryContext(
            title=novel.title,
            global_summary=global_data.get("global_summary", ""),
            characters=global_data.get("characters", []),
        )

        semaphore = asyncio.Semaphore(self.settings.max_concurrent_requests)
        chapter_results: dict[int, ChapterScript] = {}
        errors: list[str] = []

        async def convert_one(chapter: Chapter) -> None:
            async with semaphore:
                chapter_statuses[chapter.index] = ChapterStatus.RUNNING
                await emit(
                    ConversionStatus.RUNNING,
                    len(chapter_results),
                    chapter.index,
                    f"正在转换第 {chapter.index} 章",
                )
                logs.append(f"开始转换: {chapter.title}")

                for attempt in range(self.settings.chapter_retry_count + 1):
                    try:
                        ctx = StoryContext(
                            title=context.title,
                            global_summary=context.global_summary,
                            characters=context.characters,
                            previous_summaries=[
                                chapter_results[i].summary
                                for i in sorted(chapter_results.keys())
                            ],
                        )
                        elements = await asyncio.wait_for(
                            self.extractor.extract_chapter_elements(chapter, ctx),
                            timeout=self.settings.chapter_timeout_seconds,
                        )
                        script_data = await asyncio.wait_for(
                            self.extractor.convert_chapter_to_script(chapter, ctx, elements),
                            timeout=self.settings.chapter_timeout_seconds,
                        )
                        chapter_results[chapter.index] = ChapterScript(
                            chapter_index=chapter.index,
                            summary=elements.get("summary", ""),
                            characters=elements.get("characters", []),
                            locations=elements.get("locations", []),
                            scenes=script_data.get("scenes", []),
                        )
                        chapter_statuses[chapter.index] = ChapterStatus.COMPLETED
                        logs.append(f"完成: {chapter.title}")
                        await emit(
                            ConversionStatus.RUNNING,
                            len(chapter_results),
                            chapter.index,
                            f"已完成 {len(chapter_results)}/{total} 章",
                        )
                        return
                    except Exception as e:
                        if attempt < self.settings.chapter_retry_count:
                            logs.append(f"第 {chapter.index} 章重试 ({attempt + 1}): {e}")
                        else:
                            chapter_statuses[chapter.index] = ChapterStatus.FAILED
                            errors.append(f"第 {chapter.index} 章转换失败: {e}")
                            logs.append(f"失败: {chapter.title} - {e}")

        await asyncio.gather(*[convert_one(ch) for ch in novel.chapters])

        if not chapter_results:
            await emit(ConversionStatus.FAILED, 0, message="所有章节转换失败")
            return ConversionResult(success=False, errors=errors or ["转换失败"])

        # 合并剧本
        await emit(ConversionStatus.RUNNING, len(chapter_results), message="合并剧本...")
        merged = self._merge_scripts(list(chapter_results.values()))
        script_doc = self.yaml_handler.build_script_document(
            title=novel.title,
            author=novel.author,
            global_data=global_data,
            chapter_scripts=[m.model_dump() for m in merged],
        )

        validation_errors = self.yaml_handler.validate(script_doc)
        if validation_errors:
            logs.append(f"Schema 校验警告: {validation_errors[:3]}")

        yaml_content = self.yaml_handler.to_yaml_string(script_doc)
        self.storage.save_script_yaml(project_id, yaml_content)

        final_status = (
            ConversionStatus.COMPLETED if not errors else ConversionStatus.PARTIAL
        )
        await emit(
            final_status,
            len(chapter_results),
            message="转换完成" if not errors else f"部分章节失败 ({len(errors)})",
        )

        return ConversionResult(
            success=True,
            script_yaml=yaml_content,
            errors=errors,
        )

    def _merge_scripts(self, chapters: list[ChapterScript]) -> list[ChapterScript]:
        """合并各章剧本，按章节序号排序。"""
        return sorted(chapters, key=lambda c: c.chapter_index)
