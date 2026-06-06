"""剧本 Schema 加载与校验工具。"""

import json
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator

from app.config import SCHEMA_PATH


def load_schema() -> dict[str, Any]:
    """加载 JSON Schema 文件。"""
    with SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def get_validator() -> Draft202012Validator:
    """获取 Schema 校验器。"""
    schema = load_schema()
    return Draft202012Validator(schema)


def validate_script_data(data: dict[str, Any]) -> list[str]:
    """校验剧本数据，返回错误列表（空列表表示通过）。"""
    validator = get_validator()
    errors: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: e.path):
        path = ".".join(str(p) for p in error.path) or "root"
        errors.append(f"{path}: {error.message}")
    return errors
