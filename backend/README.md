# 后端服务

FastAPI 后端，负责文本解析、AI 转换、YAML 校验与文件存储。

## 启动

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8081
```

## API 文档

启动后访问 http://127.0.0.1:8081/docs

## 目录

- `app/api/` — REST 与 WebSocket 路由
- `app/services/` — 业务逻辑
- `app/infrastructure/` — LLM、存储、数据库
- `app/prompts/` — Jinja2 Prompt 模板
- `tests/` — 单元与集成测试
