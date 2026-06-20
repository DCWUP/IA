# Novel Writer — 小说续写技能

## 描述
用于在 IA（员工管理系统）项目中续写小说。自动加载小说上下文（大纲、章节、人物、规则），遵循规则进行续写。

## 使用方式
- 会话启动后，AI 主动询问用户选择哪本小说
- 加载完毕后自动汇报小说状态
- 用户给出续写指令后，AI 依据规则和大纲进行续写
- 每轮续写需用户确认后再写入数据库

## 规则
1. 启动必须主动查询小说列表
2. 续写前必须加载全部规则并遵守
3. 保持文风、人称、时态与已有章节一致
4. 续写方向必须符合大纲
5. 尊重角色设定
6. 每次输出后等待用户确认再保存

## 数据模型（SQL Server / FastAPI）

| 实体 | 说明 |
|------|------|
| Novel | 小说，含 Title、Outline |
| Chapter | 章节，含 Title、Content、SortOrder |
| Character | 人物，含 Name、Traits、Description |
| Rule | 规则，含 Category、Content（写作时必须遵守） |

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

## 下一步

1. 询问用户：`cmd /c "curl -s http://localhost/api/novels"`
2. 加载选定小说：`cmd /c "curl -s http://localhost/api/novels/1"`
3. 加载规则：`cmd /c "curl -s http://localhost/api/novels/1/rules"`
4. 展示上下文，等待用户指令
