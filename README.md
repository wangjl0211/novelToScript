# NovelToScript

AI 辅助小说转剧本工具 — 帮助作者将小说改编为结构化 YAML 剧本。

## 功能

- 导入 TXT / DOCX 小说（≥ 3 章）
- AI 自动提取人物、场景、对话、动作并转换为剧本
- YAML 格式输出，符合 JSON Schema 校验
- Monaco 编辑器 + 结构预览
- 导出 YAML / JSON / Fountain
- WebSocket 实时转换进度

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+

### 后端

```bash
cd backend
pip install -e ".[dev]"
cd ..
copy .env.example .env

cd backend
uvicorn app.main:app --reload --port 8081
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173

## 测试

```bash
cd backend
pytest -v
```

## 文档

- [开发设计文档](docs/DEVELOPMENT_DESIGN.md)
- [YAML Schema 定义](docs/YAML_SCHEMA.md)
- [实施记录](docs/IMPLEMENTATION.md)
