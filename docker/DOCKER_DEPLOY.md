# MyBookwise Docker 部署说明

MyBookwise 使用 Docker Compose 启动两个服务：

- `web`：Django + Gunicorn，负责处理网站和 API 请求
- `db`：MySQL 8.0，负责数据库存储

Docker 主要解决环境一致和部署方便的问题。并发能力主要来自 Gunicorn 的多 worker / 多线程配置，以及后续可扩展的反向代理、缓存和数据库优化。

## 首次启动

在项目根目录执行：

```powershell
copy docker\.env.docker.example .env
docker compose -f docker/docker-compose.yml up --build
```

启动成功后访问：

```text
http://127.0.0.1:8000
```

MySQL 容器首次初始化时会自动导入：

```text
SetDatabase/bookstoredb.sql
```

## 常用命令

后台启动：

```powershell
docker compose -f docker/docker-compose.yml up -d --build
```

查看容器：

```powershell
docker compose -f docker/docker-compose.yml ps
```

查看 Web 日志：

```powershell
docker compose -f docker/docker-compose.yml logs -f web
```

停止容器：

```powershell
docker compose -f docker/docker-compose.yml down
```

清空 Docker 数据库并重新导入 SQL：

```powershell
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up --build
```

## 端口说明

- 网站地址：`http://127.0.0.1:8000`
- Docker MySQL 暴露给宿主机：`127.0.0.1:3307`
- 容器内部 Django 连接 MySQL：`db:3306`

MySQL 映射到宿主机 `3307`，是为了避免和本机已有 MySQL 的 `3306` 冲突。

## 并发说明

`docker/Dockerfile` 默认使用 Gunicorn 启动 Django：

```text
gunicorn MyBookwise.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 25 --timeout 60
```

含义：

- `workers 4`：启动 4 个 worker 进程
- `threads 25`：每个 worker 使用 25 个线程
- `4 x 25 = 100`：理论上可同时容纳约 100 个请求处理槽位

这些参数可以在 `.env` 中调整：

```env
GUNICORN_WORKERS=4
GUNICORN_THREADS=25
GUNICORN_TIMEOUT=60
```

## 给老师解释

可以这样说明：

项目使用 Docker Compose 编排 Django Web 服务和 MySQL 数据库服务。Web 容器通过 Gunicorn 多 worker / 多线程运行，提高并发请求处理能力；数据库运行在独立 MySQL 容器中，并通过 Docker volume 持久化数据。首次启动时会自动导入初始化 SQL，保证部署环境可复现。
