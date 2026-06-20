---
name: novel-writer
description: 小说续写技能 - 基于现有规则和大纲续写小说章节。启动后会主动查询小说列表并询问用户选择，加载大纲/章节/人物/规则后按规则续写，用户确认后再保存。
---

当你加载这个技能时，你正在参与一个小说写作项目。

## 工作流

1. 调用 `cmd /c "curl -s http://localhost/api/novels"` 获取小说列表展示给用户
2. 询问"你要续写哪本小说？"
3. 用户选定后加载小说完整数据、规则
4. 展示上下文（章节数、人物、规则数、最新章节进展）
5. 用户给出续写指令后，遵守规则和大纲续写
6. 用户确认后再保存到数据库

## API 端点

| Method | Endpoint | 用途 |
|--------|----------|------|
| GET | /api/novels | 列出所有小说 |
| GET | /api/novels/{id} | 获取小说完整数据 |
| PUT | /api/novels/{id}/chapters/{index} | 更新章节 |
| POST | /api/novels/{id}/chapters | 新增章节 |
| POST | /api/novels/{id}/sync | 全量同步 |
| GET | /api/novels/{id}/rules | 获取规则 |
| POST | /api/aigc/analyze | 分析 AIGC 率 |

## 规则

- 续写前必须加载全部规则并遵守
- 保持文风、人称、时态与已有章节一致
- 续写方向必须符合大纲
- 尊重角色设定
- 每次输出后等待用户确认再保存
