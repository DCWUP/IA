You are in a novel writing project (IA). The project has a FastAPI backend + SQL Server with a multi-novel writing platform. When working with novels, follow this protocol:

## 启动协议

1. **主动询问**: 会话开始时，主动调用 `GET http://localhost/api/novels` 获取小说列表，展示给用户，询问"你要续写哪本小说？"
2. **加载小说**: 用户选定后，调用 `GET http://localhost/api/novels/{novelId}` 获取完整数据（大纲、章节、人物、规则）
3. **展示上下文**: 向用户简要汇报当前小说状态：章节数、人物数、规则数、最新章节进展

## API 基础

- 通过 nginx: `http://localhost/api/...`
- 直接后端: `http://localhost:8000/api/...`
- 使用 `bash` 工具 + `curl` 进行 API 调用

### 常用 API

```bash
# 列出所有小说
cmd /c "curl -s http://localhost/api/novels"

# 获取单本小说完整数据（含章节、人物、规则）
cmd /c "curl -s http://localhost/api/novels/1"

# 更新章节 (index 从 0 开始)
cmd /c "curl -s -X PUT http://localhost/api/novels/1/chapters/0 -H \"Content-Type: application/json\" -d \"{\\\"title\\\":\\\"...\\\",\\\"content\\\":\\\"...\\\"}\""

# 新增章节 (默认追加到末尾)
cmd /c "curl -s -X POST http://localhost/api/novels/1/chapters -H \"Content-Type: application/json\" -d \"{\\\"title\\\":\\\"...\\\",\\\"content\\\":\\\"...\\\"}\""

# 全量同步（替换所有章节+人物+大纲）
cmd /c "curl -s -X POST http://localhost/api/novels/1/sync -H \"Content-Type: application/json\" -d @-"
<paste full JSON body here>

# 获取规则
cmd /c "curl -s http://localhost/api/novels/1/rules"

# AIGC 分析
cmd /c "curl -s -X POST http://localhost/api/aigc/analyze -H \"Content-Type: application/json\" -d \"{\\\"content\\\":\\\"...\\\"}\""
```

## 续写工作流

在继续小说写作时必须严格遵守以下流程：

### 1. 理解上下文
- 阅读小说大纲（Outline），理解当前进度
- 阅读所有规则（Rules），写作时必须遵守
- 阅读人物列表（Characters），了解角色设定
- 阅读所有已有章节，理解情节发展和文风

### 2. 续写规则
- **必须遵守所有规则**，每条规则是硬性约束
- 保持与已有章节一致的文风、人称、时态
- 续写内容必须符合大纲方向
- 尊重人物设定（Characters），不 OOC
- 章节标题保持格式一致

### 3. 输出格式
- 每次续写返回完整章节内容（Markdown 格式）
- 先向用户概述你要写的内容方向
- 用户确认后再实际写入
- 写入前用最新的大纲和规则再次验证

### 4. 保存
- 用户确认内容后，调用 `PUT /api/novels/{id}/chapters/{index}` 更新已有章节，或 `POST /api/novels/{id}/chapters` 新增章节
- 通知用户保存成功

## 独立会话管理

每个 opencode 会话独立管理一本小说：
- 会话启动时，如果未载入小说数据，必须先询问
- 用户可能中途切换小说，调用 `GET /api/novels` 重新选择
- 切换后重新加载全部上下文
