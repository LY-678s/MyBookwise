# Docker Files

这个目录集中存放 MyBookwise 的 Docker 部署文件。

## 文件说明

- `docker-compose.yml`
  - Docker Compose 编排文件。
  - 负责同时启动 `web` 和 `db` 两个服务。
  - `web` 运行 Django + Gunicorn。
  - `db` 运行 MySQL 8.0。
  - 首次创建数据库卷时，会把 `../SetDatabase/bookstoredb.sql` 导入 MySQL。

- `Dockerfile`
  - Web 服务镜像的构建文件。
  - 基于 `python:3.11-slim-bookworm`。
  - 安装 `requirements.txt` 里的 Python 依赖。
  - 复制项目代码到容器内的 `/app`。
  - 最终用 Gunicorn 启动 Django。

- `entrypoint.sh`
  - Web 容器启动入口脚本。
  - 启动前等待 MySQL 端口可连接。
  - 执行 `collectstatic` 收集静态文件。
  - 最后交给 Dockerfile 中的 Gunicorn 命令运行网站。

- `Dockerfile.dockerignore`
  - Web 镜像构建时的忽略文件。
  - 避免把 `.git`、虚拟环境、测试缓存、Android 构建产物、本地 `.env` 等无关或敏感文件复制进镜像。
  - 因为 Dockerfile 放在本目录，文件名使用 Docker 支持的专用格式 `Dockerfile.dockerignore`。

- `.env.docker.example`
  - Docker 部署环境变量模板。
  - 可复制到项目根目录 `.env` 后按本机情况修改。
  - 真实 `.env` 不应提交到 Git。

- `DOCKER_DEPLOY.md`
  - 更偏讲解型的 Docker 部署说明。
  - 包含常用命令、端口说明和 Gunicorn 并发参数解释。

## 常用命令

以下命令请在项目根目录执行：

```powershell
docker compose -f docker/docker-compose.yml up -d --build
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f web
docker compose -f docker/docker-compose.yml down
```

如果需要删除数据库卷并重新初始化数据库：

```powershell
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d --build
```
