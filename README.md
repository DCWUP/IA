# IA - 员工管理系统

一个简单的员工管理系统，使用 Node.js + Express + SQL Server + Nginx 构建。

## 功能

- 查看员工列表
- 新增员工
- 编辑员工信息
- 删除员工
- 局域网访问

## 快速开始

### 1. 一键启动所有服务

```bash
docker-compose --env-file .env.docker up -d --build
```

### 2. 初始化数据库

数据库启动后，执行以下命令创建表和示例数据：

```bash
docker exec sqlserver-demo /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "YourStrong!Password123" -C -Q "CREATE DATABASE DemoDB"

docker exec sqlserver-demo /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "YourStrong!Password123" -C -d DemoDB -Q "
CREATE TABLE Employees (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(100) NOT NULL,
    Department NVARCHAR(50),
    Salary DECIMAL(10,2),
    HireDate DATE
);

INSERT INTO Employees (Name, Department, Salary, HireDate) VALUES
(N'张三', N'技术部', 15000, '2020-01-15'),
(N'李四', N'市场部', 12000, '2021-03-20'),
(N'王五', N'技术部', 18000, '2019-06-10'),
(N'赵六', N'人事部', 11000, '2022-08-01'),
(N'钱七', N'市场部', 13500, '2020-11-25');
"
```

### 3. 访问应用

- 本机访问：http://localhost
- 局域网访问：http://<你的IP>

## 服务架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│  Node.js    │────▶│ SQL Server  │
│   (80)      │     │  (3000)     │     │  (1433)     │
└─────────────┘     └─────────────┘     └─────────────┘
   前端静态文件        API 后端            数据库
```

## 常用命令

```bash
# 启动所有服务
docker-compose --env-file .env.docker up -d --build

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启某个服务
docker-compose restart backend

# 进入容器
docker exec -it nginx-frontend sh
docker exec -it node-backend sh
docker exec -it sqlserver-demo bash

# 连接数据库
docker exec sqlserver-demo /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "YourStrong!Password123" -C

# 备份数据库
docker exec sqlserver-demo /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "YourStrong!Password123" -C -Q "BACKUP DATABASE DemoDB TO DISK='/var/opt/mssql/DemoDB.bak'"

# 恢复数据库
docker exec sqlserver-demo /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "YourStrong!Password123" -C -Q "RESTORE DATABASE DemoDB FROM DISK='/var/opt/mssql/DemoDB.bak'"
```

## 配置

### 环境变量

复制 `.env.docker` 为 `.env.docker.local` 并修改密码：

```bash
cp .env.docker .env.docker.local
```

编辑 `.env.docker.local`：

```
SA_PASSWORD=YourNewPassword123
```

### 数据库连接

```
Server: sqlserver
Database: DemoDB
User: SA
Password: YourStrong!Password123
```

## 防火墙配置

如需局域网访问，需开放 80 端口：

```powershell
netsh advfirewall firewall add rule name="Nginx Frontend" dir=in action=allow protocol=TCP localport=80
```

## 技术栈

- 前端：Vite + HTML + CSS + JavaScript
- 后端：Node.js + Express
- 数据库：SQL Server 2022
- 反向代理：Nginx
- 容器化：Docker Compose
