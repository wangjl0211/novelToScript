"""章节切分与文件解析测试。"""

import pytest

from app.services.import_parser import parse_novel_file, preprocess_text, split_chapters


SAMPLE_NOVEL = """第一章 开端

李明走进房间，阳光洒满地板。他轻声自语："今天会是不同的一天。"

小红从厨房探出头，笑着说："你终于起来了！"

第二章 转折

午后，两人在街角咖啡馆坐下。李明犹豫着是否该说出真相。

第三章 结局

夜幕降临，李明终于做出了决定。小红握住他的手，一切归于平静。
"""


def test_preprocess_text():
    text = "  hello   world  \n\n\n\n  foo  "
    result = preprocess_text(text)
    assert "hello world" in result
    assert "\n\n\n" not in result


def test_split_chapters():
    chapters = split_chapters(SAMPLE_NOVEL)
    assert len(chapters) == 3
    assert "开端" in chapters[0][0]
    assert "转折" in chapters[1][0]


def test_parse_novel_txt():
    content = SAMPLE_NOVEL.encode("utf-8")
    novel = parse_novel_file("test.txt", content)
    assert novel.title
    assert len(novel.chapters) == 3
    assert all(ch.word_count > 0 for ch in novel.chapters)


def test_parse_novel_too_few_chapters():
    text = "第一章 开端\n内容一\n\n第二章 转折\n内容二"
    with pytest.raises(ValueError):
        parse_novel_file("short.txt", text.encode("utf-8"))
