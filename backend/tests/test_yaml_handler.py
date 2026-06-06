"""YAML 校验测试。"""

from datetime import datetime, timezone

import pytest

from app.services.yaml_handler import YAMLHandler


@pytest.fixture
def handler():
    return YAMLHandler()


@pytest.fixture
def valid_script():
    now = datetime.now(timezone.utc).isoformat()
    return {
        "script": {
            "meta": {
                "title": "测试剧本",
                "version": "1.0.0",
                "created_at": now,
            },
            "characters": [
                {"id": "liming", "name": "李明"},
            ],
            "locations": [
                {"id": "cafe", "name": "咖啡馆"},
            ],
            "acts": [
                {
                    "act_number": 1,
                    "title": "第一幕",
                    "scenes": [
                        {
                            "scene_id": "sc001",
                            "heading": {
                                "int_ext": "INT",
                                "location": "咖啡馆",
                                "time_of_day": "日",
                            },
                            "blocks": [
                                {"type": "action", "text": "李明推门而入。"},
                                {
                                    "type": "dialogue",
                                    "character_id": "liming",
                                    "lines": ["你好。"],
                                },
                            ],
                        }
                    ],
                }
            ],
        }
    }


def test_validate_valid_script(handler, valid_script):
    errors = handler.validate(valid_script)
    assert errors == []


def test_validate_invalid_script(handler):
    errors = handler.validate({"script": {}})
    assert len(errors) > 0


def test_yaml_roundtrip(handler, valid_script):
    yaml_str = handler.to_yaml_string(valid_script)
    data, errors = handler.validate_yaml(yaml_str)
    assert errors == []
    assert data is not None
    assert data["script"]["meta"]["title"] == "测试剧本"
