# AGENTS.md — IA (员工管理系统)

## 启动

```bash
# 全栈启动（含构建）
docker-compose --env-file .env.docker up -d --build

# 仅重启某个服务
docker-compose restart backend
docker-compose restart frontend
```

## 关键路径

| 作用 | 路径 |
|------|------|
| 前端源码 | `client/` (Vite vanilla JS, pnpm) |
| 后端 | `server.js` (Express) |
| Nginx 配置 | `nginx/default.conf` |
| 前端 Docker | `Dockerfile.frontend` (多阶段构建) |
| 后端 Docker | `Dockerfile.backend` |
| 编排 | `docker-compose.yml` (3 services) |
| 数据库密码 | `.env.docker` |

## 架构

```
Nginx:80 → Node:3000 → SQL Server:1433
```

## 数据库操作

- sqlcmd 路径 `/opt/mssql-tools18/bin/sqlcmd`（不是 tools）
- 需要 `-C` 参数信任自签名证书
- 默认密码在 `.env.docker` 中
- Docker 数据卷用命名卷 `sqlserver-data`（Windows 路径 bind mount 会导致权限错误）

## Windows / PowerShell 注意事项

- PowerShell 不支持 `&&`，用 `; if ($?) { ... }` 或 `cmd /c "... && ..."`
- npm 的 .ps1 可能被执行策略拦截，用 `cmd /c "npm ..."`
- 防火墙放行 80 端口即可局域网访问

## 前端构建

```bash
# 本地构建
cd client && pnpm install && pnpm build   # 输出到 client/dist/

# Docker 内构建（Dockerfile.frontend 自动执行）
```

## 前端注意

- `client/src/main.js` 是 ES Module，内联 `onclick` 调用的函数需挂到 `window` 上（如 `window.deleteEmployee`）
- 修改 `client/src/main.js` 后需要 `docker-compose up -d --build frontend` 重新构建

## 提交

```bash
git add <files>
git commit -m "说明"
git push origin main
```

## 插件

- `.opencode.json`: `opencode-storyclaw`, `opencode-novel-plugin`
- 安装: `npm install -g opencode-storyclaw opencode-novel-plugin`
