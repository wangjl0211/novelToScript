# 剧本 YAML Schema 技术文档

| 文档版本 | v1.0.0 |
|---------|--------|
| Schema 文件 | `schemas/script.schema.json` |
| 适用工具版本 | novelToScript v1.0.0 |

---

## 1. 概述

本 Schema 定义了 AI 辅助小说转剧本工具的输出格式，旨在：

1. **人类可读**：YAML 格式便于作者直接编辑
2. **机器可校验**：JSON Schema 约束确保结构完整
3. **行业兼容**：参考 Fountain 与中国影视剧本惯例

---

## 2. 顶层结构

```yaml
script:
  meta:          # 元数据（必填）
  characters:    # 人物表（必填，≥1）
  locations:     # 场景地点表（必填，可为空数组）
  acts:          # 幕列表（必填，≥1）
```

---

## 3. 字段定义

### 3.1 `script.meta` — 元数据

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| `title` | string | 是 | 剧本标题 |
| `author` | string | 否 | 编剧/作者 |
| `source_novel` | string | 否 | 源小说名称 |
| `version` | string | 是 | 语义化版本，格式 `x.y.z` |
| `created_at` | datetime | 是 | ISO 8601 创建时间 |
| `updated_at` | datetime | 否 | 最后更新时间 |
| `genre` | string | 否 | 类型标签 |
| `logline` | string | 否 | 一句话梗概 |
| `notes` | string | 否 | 备注 |

**使用场景**：项目标识、版本管理、导出文件头信息。

### 3.2 `script.characters[]` — 人物表

| 字段 | 类型 | 必填 | 约束 | 说明 |
|-----|-----|-----|-----|-----|
| `id` | string | 是 | `^[a-z][a-z0-9_]*$` | 全局唯一标识 |
| `name` | string | 是 | minLength: 1 | 显示名称 |
| `aliases` | string[] | 否 | — | 别名列表 |
| `description` | string | 否 | — | 人物简介 |
| `age` | string | 否 | — | 年龄描述 |
| `gender` | string | 否 | — | 性别 |

**设计依据**：中国影视剧本惯例要求附人物表；ID 用于对白引用，避免姓名变更导致引用断裂。

### 3.3 `script.locations[]` — 场景地点表

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| `id` | string | 是 | 地点唯一 ID |
| `name` | string | 是 | 地点名称 |
| `description` | string | 否 | 地点描述 |
| `interior` | boolean | 否 | 是否为内景 |

### 3.4 `script.acts[]` — 幕

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| `act_number` | integer | 是 | 幕序号，≥1 |
| `title` | string | 是 | 幕标题 |
| `summary` | string | 否 | 幕摘要 |
| `scenes` | scene[] | 是 | 场景列表，≥1 |

**设计决策**：v1.0 默认将所有场景归入第一幕；长篇可在编辑阶段手动拆分幕结构。

### 3.5 `scenes[]` — 场

| 字段 | 类型 | 必填 | 说明 |
|-----|-----|-----|-----|
| `scene_id` | string | 是 | 格式 `sc001`，全局唯一 |
| `chapter_source` | integer | 否 | 来源小说章节号 |
| `heading` | object | 是 | 场景标题 |
| `location_id` | string | 否 | 关联 locations.id |
| `time` | string | 否 | 具体时间描述 |
| `weather` | string | 否 | 天气 |
| `cast` | string[] | 否 | 出场人物 ID 列表 |
| `props` | string[] | 否 | 道具列表 |
| `summary` | string | 否 | 场景摘要 |
| `blocks` | block[] | 是 | 内容块，≥1 |

### 3.6 `heading` — 场景标题

| 字段 | 类型 | 必填 | 枚举/约束 | 说明 |
|-----|-----|-----|---------|-----|
| `int_ext` | string | 是 | INT, EXT, INT/EXT | 内景/外景 |
| `location` | string | 是 | minLength: 1 | 地点名 |
| `time_of_day` | string | 是 | 日/夜/晨/昏/连续 | 时间段 |
| `display` | string | 否 | — | 渲染用完整标题 |

**行业参考**：对应 Fountain 的 Scene Heading（如 `INT. COFFEE SHOP - DAY`）。

### 3.7 `blocks[]` — 内容块

内容块采用 `type` 字段区分类型（oneOf 约束）：

#### `action` — 动作/环境

```yaml
type: action
text: "李明推开门，阳光洒进房间。"
```

#### `dialogue` — 对白

```yaml
type: dialogue
character_id: liming
parenthetical: "（低声）"
lines:
  - "我有话要对你说。"
```

#### `parenthetical` — 括号说明

```yaml
type: parenthetical
text: "（沉默片刻）"
```

#### `transition` — 转场

```yaml
type: transition
text: "切至"
```

#### `voiceover` — 画外音/旁白

```yaml
type: voiceover
character_id: liming
text: "那一刻，他终于明白了。"
```

**心理活动转化规则**（写入 AI Prompt）：
- 可外化 → `action`
- 可表达 → `dialogue`
- 不可外化 → `voiceover`

---

## 4. 设计理论依据

| 参考标准 | 采纳内容 | 理由 |
|---------|---------|-----|
| **Fountain** | 场景标题、人物、对白、转场 | 国际通用剧本概念 |
| **中国影视剧本格式** | 人物表、分场、内景/外景 | 国内行业习惯 |
| **YAML** | 全文格式 | 版本控制友好、人类可编辑 |
| **JSON Schema** | 机器校验 | 编辑器智能提示、拦截格式错误 |

---

## 5. 完整示例

```yaml
script:
  meta:
    title: 归途
    author: AI 辅助生成
    source_novel: 归途
    version: 1.0.0
    created_at: "2026-06-06T10:00:00+00:00"
    genre: 都市
    logline: 一个关于回归与抉择的故事

  characters:
    - id: liming
      name: 李明
      description: 故事主角，内敛坚韧
    - id: xiaohong
      name: 小红
      description: 李明的好友

  locations:
    - id: liming_home
      name: 李明旧居
      interior: true
    - id: cafe
      name: 街角咖啡馆
      interior: true

  acts:
    - act_number: 1
      title: 第一幕
      summary: 李明回归，与小红重逢并做出抉择
      scenes:
        - scene_id: sc001
          chapter_source: 1
          heading:
            int_ext: INT
            location: 李明旧居
            time_of_day: 日
            display: 内景 李明旧居 - 日
          location_id: liming_home
          cast: [liming, xiaohong]
          blocks:
            - type: action
              text: 李明推开旧木门，阳光涌入房间。
            - type: dialogue
              character_id: xiaohong
              lines:
                - "你终于回来了。"
            - type: voiceover
              character_id: liming
              text: 这次回来，是为了做一个迟到的决定。

        - scene_id: sc002
          chapter_source: 2
          heading:
            int_ext: INT
            location: 街角咖啡馆
            time_of_day: 日
            display: 内景 街角咖啡馆 - 日
          location_id: cafe
          cast: [liming, xiaohong]
          blocks:
            - type: action
              text: 两人相对而坐，咖啡早已凉透。
            - type: dialogue
              character_id: xiaohong
              lines:
                - "你打算什么时候告诉我真相？"
            - type: transition
              text: 切至
```

---

## 6. 校验

```bash
# Python
from app.domain.script_schema import validate_script_data
errors = validate_script_data(data)

# 前端/后端 API
POST /api/projects/{id}/script/validate
```

---

*Schema 变更请同步更新 `schemas/script.schema.json` 与本文件。*
