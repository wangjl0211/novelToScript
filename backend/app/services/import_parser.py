"""小说文本导入与章节切分。"""

import re
from io import BytesIO
from pathlib import Path

import chardet
from docx import Document

from app.domain.models import Chapter, ParsedNovel

# 章节标题正则（支持中英文多种格式）
CHAPTER_PATTERNS = [
    re.compile(r"^第[零一二三四五六七八九十百千万\d]+章[\s:：\-—]*(.*)$", re.MULTILINE),
    re.compile(r"^Chapter\s+(\d+)[\s:：\-—]*(.*)$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^CHAPTER\s+(\d+)[\s:：\-—]*(.*)$", re.MULTILINE),
]

MAX_CHAPTER_WORDS = 8081


def detect_encoding(raw: bytes) -> str:
    """检测文本编码并返回解码用编码名。"""
    result = chardet.detect(raw)
    encoding = result.get("encoding") or "utf-8"
    # 常见误检修正
    if encoding.lower() in ("gb2312", "iso-8859-1"):
        encoding = "gbk"
    return encoding


def read_txt(content: bytes) -> str:
    """读取 TXT 并统一为 UTF-8 字符串。"""
    encoding = detect_encoding(content)
    try:
        return content.decode(encoding)
    except UnicodeDecodeError:
        return content.decode("utf-8", errors="replace")


def read_docx(content: bytes) -> str:
    """读取 DOCX 文件内容。"""
    doc = Document(BytesIO(content))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def preprocess_text(text: str) -> str:
    """清洗文本：统一换行、去除多余空白。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_chapters(text: str) -> list[tuple[str, str]]:
    """
    按章节标题切分文本。
    返回 [(章节标题, 章节内容), ...]
    """
    # 合并所有模式为单一正则
    combined = re.compile(
        r"(?:^|\n)("
        r"第[零一二三四五六七八九十百千万\d]+章[\s:：\-—]*[^\n]*"
        r"|Chapter\s+\d+[\s:：\-—]*[^\n]*"
        r"|CHAPTER\s+\d+[\s:：\-—]*[^\n]*"
        r")",
        re.MULTILINE | re.IGNORECASE,
    )

    matches = list(combined.finditer(text))
    if not matches:
        return []

    chapters: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            chapters.append((title, content))

    return chapters


def split_long_chapter(title: str, content: str, base_index: int) -> list[Chapter]:
    """超长章节按段落二次切分。"""
    if len(content) <= MAX_CHAPTER_WORDS:
        return [
            Chapter(
                index=base_index,
                title=title,
                content=content,
                word_count=len(content),
            )
        ]

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    result: list[Chapter] = []
    buffer = ""
    part = 1
    idx = base_index

    for para in paragraphs:
        if len(buffer) + len(para) > MAX_CHAPTER_WORDS and buffer:
            result.append(
                Chapter(
                    index=idx,
                    title=f"{title}（{part}）",
                    content=buffer.strip(),
                    word_count=len(buffer.strip()),
                )
            )
            idx += 1
            part += 1
            buffer = para + "\n\n"
        else:
            buffer += para + "\n\n"

    if buffer.strip():
        suffix = f"（{part}）" if part > 1 else ""
        result.append(
            Chapter(
                index=idx,
                title=f"{title}{suffix}",
                content=buffer.strip(),
                word_count=len(buffer.strip()),
            )
        )
    return result


def infer_title(text: str, filename: str) -> str:
    """从正文或文件名推断书名。"""
    first_line = text.split("\n", 1)[0].strip()
    if first_line and len(first_line) <= 50 and "章" not in first_line:
        return first_line
    stem = Path(filename).stem
    return stem or "未命名小说"


def parse_novel_file(filename: str, content: bytes) -> ParsedNovel:
    """
    解析上传的小说文件。
    支持 TXT、DOCX 格式。
    """
    ext = Path(filename).suffix.lower()
    if ext == ".txt":
        text = read_txt(content)
    elif ext == ".docx":
        text = read_docx(content)
    else:
        raise ValueError(f"不支持的文件格式: {ext}，请上传 TXT 或 DOCX")

    text = preprocess_text(text)
    if not text:
        raise ValueError("文件内容为空")

    title = infer_title(text, filename)
    raw_chapters = split_chapters(text)

    if not raw_chapters:
        raise ValueError("未能识别章节结构，请确保文本包含「第X章」或「Chapter X」格式的章节标题")

    chapters: list[Chapter] = []
    idx = 1
    for chap_title, chap_content in raw_chapters:
        split_result = split_long_chapter(chap_title, chap_content, idx)
        for ch in split_result:
            ch.index = idx
            chapters.append(ch)
            idx += 1

    if len(chapters) < 3:
        raise ValueError(f"章节数不足 3 章（当前 {len(chapters)} 章），请上传包含至少 3 章的小说")

    return ParsedNovel(title=title, author=None, chapters=chapters)
