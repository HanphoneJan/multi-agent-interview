---
name: deploy
description: 打包 bw-crash 项目用于生产部署。生成部署包到 tmp/ 目录，包含部署文档。
argument-hint:
---

# BW Crash 部署打包

执行此 skill 将打包项目用于生产环境部署。

## 执行步骤

### 1. 清理 tmp 目录

```bash
rm -rf tmp/*
mkdir -p tmp/bw-crash-deploy
```

### 2. 复制部署所需文件

将以下文件/目录复制到 `tmp/bw-crash-deploy/`:

```
docker-compose.prod.yml  → docker-compose.yml
.env.example             → .env.example
nginx/                   → nginx/
server/Dockerfile        → server/Dockerfile
server/package.json      → server/package.json
server/pnpm-lock.yaml    → server/pnpm-lock.yaml
server/prisma/           → server/prisma/
server/src/              → server/src/
server/clickhouse/       → server/clickhouse/
server/tsconfig*.json    → server/
server/nest-cli.json     → server/
```

### 3. 生成 DEPLOY.md

在 `tmp/bw-crash-deploy/` 目录下创建 `DEPLOY.md` 部署文档，内容包括：

- 服务器要求（Ubuntu 24.04, 4核8G+）
- Docker 和 Docker Compose 安装步骤
- 环境变量配置说明
- 启动命令
- 常用运维命令
- 数据备份方法

### 4. 打包压缩

```bash
cd tmp && tar -czvf bw-crash-deploy.tar.gz bw-crash-deploy/
```

### 5. 输出结果

告知用户:
- 部署包位置: `tmp/bw-crash-deploy.tar.gz`
- 解压后阅读 `DEPLOY.md` 开始部署

---

## DEPLOY.md 模板

```markdown
# BW Crash 部署指南

## 服务器要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Ubuntu 22.04+ | Ubuntu 24.04 LTS |
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 存储 | 50 GB SSD | 100 GB SSD |

## 1. 安装 Docker

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER

# 重新登录使生效
exit
```

## 2. 安装 Docker Compose

```bash
sudo apt install docker-compose-plugin -y

# 验证安装
docker compose version
```

## 3. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置（必须修改以下内容）
nano .env
```

**必须修改的配置项:**

```ini
# 数据库密码（使用强密码）
POSTGRES_PASSWORD=<生成强密码>
CLICKHOUSE_PASSWORD=<生成强密码>
REDIS_PASSWORD=<生成强密码>

# JWT 密钥（至少32位随机字符串）
JWT_SECRET=<使用 openssl rand -hex 32 生成>

# 访问域名（用于 CORS）
CORS_ORIGIN=https://your-domain.com
```

**生成随机密码:**

```bash
# 生成数据库密码
openssl rand -base64 24

# 生成 JWT 密钥
openssl rand -hex 32
```

## 4. 启动服务

```bash
# 首次启动（构建镜像）
docker compose up -d --build

# 查看日志
docker compose logs -f

# 查看服务状态
docker compose ps
```

## 5. 初始化数据库

```bash
# 执行 Prisma 迁移
docker compose exec server npx prisma migrate deploy
```

## 6. 验证服务状态（重要！）

部署完成后，**必须**验证所有服务是否正常运行。

### 检查所有服务状态

```bash
# 查看所有容器状态
docker compose ps

# 期望输出：所有服务状态应为 "running" 或 "Up"
# NAME         STATUS
# nginx        Up
# server       Up (healthy)
# postgres     Up (healthy)
# clickhouse   Up
# redis        Up
```

### 单独验证每个服务

```bash
# 1. 检查 PostgreSQL
docker compose exec postgres pg_isready -U bwcrash
# 期望输出: accepting connections

# 2. 检查 Redis
docker compose exec redis redis-cli ping
# 期望输出: PONG

# 3. 检查 ClickHouse
docker compose exec clickhouse clickhouse-client --query "SELECT 1"
# 期望输出: 1

# 4. 检查 Server API
curl -s http://localhost:17066/api/v1/health
# 期望输出: {"status":"ok"} 或类似健康响应

# 5. 检查 Nginx
curl -s http://localhost:17066/health
# 期望输出: healthy
```

### 一键健康检查脚本

创建 `check-health.sh` 脚本进行一键检查：

```bash
#!/bin/bash
# check-health.sh - 服务健康检查脚本

echo "=== BW Crash 服务健康检查 ==="
echo ""

FAILED=0

# 检查容器运行状态
echo "检查容器状态..."
CONTAINERS=$(docker compose ps --format json 2>/dev/null | jq -r '.State' | grep -v running | wc -l)
if [ "$CONTAINERS" -gt 0 ]; then
    echo "❌ 有容器未运行"
    docker compose ps
    FAILED=1
else
    echo "✅ 所有容器运行中"
fi

# 检查 PostgreSQL
echo ""
echo "检查 PostgreSQL..."
if docker compose exec -T postgres pg_isready -U bwcrash > /dev/null 2>&1; then
    echo "✅ PostgreSQL 正常"
else
    echo "❌ PostgreSQL 异常"
    FAILED=1
fi

# 检查 Redis
echo ""
echo "检查 Redis..."
if docker compose exec -T redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis 正常"
else
    echo "❌ Redis 异常"
    FAILED=1
fi

# 检查 ClickHouse
echo ""
echo "检查 ClickHouse..."
if docker compose exec -T clickhouse clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
    echo "✅ ClickHouse 正常"
else
    echo "❌ ClickHouse 异常"
    FAILED=1
fi

# 检查 API
echo ""
echo "检查 API 服务..."
if curl -sf http://localhost:17066/api/v1/health > /dev/null 2>&1; then
    echo "✅ API 服务正常"
else
    echo "❌ API 服务异常"
    FAILED=1
fi

echo ""
echo "==========================="
if [ "$FAILED" -eq 0 ]; then
    echo "✅ 所有服务健康运行！"
    exit 0
else
    echo "❌ 部分服务异常，请检查日志"
    echo ""
    echo "查看异常服务日志："
    echo "  docker compose logs <service-name>"
    exit 1
fi
```

使用方法：
```bash
chmod +x check-health.sh
./check-health.sh
```

### 自动修复未启动的服务

如果发现服务未启动，执行以下命令：

```bash
# 重启所有服务
docker compose up -d

# 或仅重启特定服务
docker compose restart <service-name>

# 查看失败服务的日志
docker compose logs --tail=50 <service-name>
```

### 常见问题处理

| 问题 | 可能原因 | 解决方法 |
|------|----------|----------|
| server 无法启动 | 数据库未就绪 | 等待 30 秒后重试，或检查 postgres 日志 |
| postgres 启动失败 | 权限或存储问题 | 检查 volume 权限，确保磁盘空间充足 |
| redis 连接拒绝 | 密码配置错误 | 检查 .env 中的 REDIS_PASSWORD |
| clickhouse 异常 | 内存不足 | 确保服务器至少有 4GB 可用内存 |

## 7. 访问服务

- API: http://your-server:17066/api/v1
- Swagger: http://your-server:17066/api/docs
- 健康检查: http://your-server:17066/health

## 常用运维命令

```bash
# 重启服务
docker compose restart

# 停止服务
docker compose down

# 查看日志
docker compose logs -f server
docker compose logs -f nginx

# 进入容器
docker compose exec server sh
docker compose exec postgres psql -U bwcrash

# 更新部署
docker compose pull
docker compose up -d --build
```

## 数据备份

### PostgreSQL 备份

```bash
# 备份
docker compose exec postgres pg_dump -U bwcrash bwcrash > backup_$(date +%Y%m%d).sql

# 恢复
cat backup.sql | docker compose exec -T postgres psql -U bwcrash bwcrash
```

### ClickHouse 备份

```bash
# 备份（导出 SQL）
docker compose exec clickhouse clickhouse-client --query "SELECT * FROM bw_crash.crash_events FORMAT Native" > crash_events.native

# 查看数据目录
docker volume inspect bwcrash_clickhouse_data
```

## 故障排查

### 服务无法启动

```bash
# 检查容器状态
docker compose ps -a

# 查看详细日志
docker compose logs server --tail=100
```

### 数据库连接失败

```bash
# 检查数据库是否就绪
docker compose exec postgres pg_isready
```

### ClickHouse 写入失败

```bash
# 检查 ClickHouse 状态
docker compose exec clickhouse clickhouse-client --query "SELECT 1"
```

---

*部署包生成时间: [TIMESTAMP]*
```

---

## 禁止事项

1. 不要复制 node_modules
2. 不要复制 .env 文件（只复制 .env.example）
3. 不要复制 dist/ 目录
4. 不要复制测试文件
