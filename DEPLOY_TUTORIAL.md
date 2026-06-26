# MyBookwise 部署与使用教程

这份文档面向第一次接触项目的人。按步骤操作，可以启动 Web、Docker、Cloudflare Tunnel，并让 Android App 连接后端。

## 1. 准备环境

需要安装：

- Python
- MySQL
- Docker Desktop
- Android Studio
- `cloudflared`

如果只运行 Docker 版 Web，至少需要 Docker Desktop。

## 2. 启动 Docker

先打开 Docker Desktop，确认它处于运行状态。

在项目根目录执行：

```powershell
docker compose -f docker/docker-compose.yml up -d --build
```

查看容器状态：

```powershell
docker compose -f docker/docker-compose.yml ps
```

看到 `mybookwise-web` 和 `mybookwise-db` 都是 `Up`，说明启动成功。

浏览器访问：

```text
http://127.0.0.1:8000
```

## 3. Docker 数据库从哪里来

Docker 的 MySQL 首次创建数据库卷时，会自动导入：

```text
SetDatabase/bookstoredb.sql
```

Docker 数据库和你 Navicat 里本地手动连接的数据库不是同一个。修改本地 Navicat 数据库，不会自动影响 Docker 数据库。

如果需要删除 Docker 数据库卷并重新导入 SQL：

```powershell
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d --build
```

## 4. 配置 Cloudflare 域名

固定域名访问依赖 Cloudflare Tunnel。你需要有 Cloudflare 账号权限，并能管理对应域名，例如：

```text
ly.mybookwise.xyz
```

本地隧道配置文件：

```text
scripts/cloudflared-mybookwise.yml
```

里面需要包含：

- `tunnel`：隧道 UUID
- `credentials-file`：本机凭证 JSON 路径
- `hostname`：要绑定的域名
- `service`：本机源站地址，当前为 `http://127.0.0.1:8000`

启动隧道：

```powershell
scripts\start_tunnel_named.cmd
```

成功后访问：

```text
https://ly.mybookwise.xyz
```

## 5. 配置 Android App

App 后端地址在：

```text
mobile/settings.properties
```

可以从示例文件复制：

```powershell
cd mobile
copy settings.properties.example settings.properties
```

然后修改：

```properties
server_base=https://ly.mybookwise.xyz
```

修改后需要重新构建或运行 Android 项目。

## 6. App 使用说明

App 通过后端 API 访问数据，不直接连接数据库。主要页面包括：

- 首页
- 搜索
- 图书详情
- 购物车
- 收藏夹
- 订单列表
- 账户页面
- AI 书小智

## 7. 常见问题

### Cloudflare 显示 `127.0.0.1:8000 refused`

通常说明本机 8000 端口没有服务在运行。先检查：

```powershell
docker compose -f docker/docker-compose.yml ps
```

再看 Web 日志：

```powershell
docker compose -f docker/docker-compose.yml logs -f web
```

### Cloudflare 显示 `EOF`

通常说明 8000 端口有服务，但连接中途断开。常见原因是 Web 容器重启、Gunicorn worker 报错、请求触发后端异常或超时。

处理顺序：

1. 打开 `http://127.0.0.1:8000` 确认本地能访问
2. 查看 `web` 容器日志
3. 确认 Docker 是用最新命令启动的

### App 访问不了后端

检查：

- `mobile/settings.properties` 的 `server_base`
- App 是否重新构建
- Cloudflare Tunnel 是否正在运行
- Docker Web 是否正在运行

## 8. 最短启动顺序

```powershell
docker compose -f docker/docker-compose.yml up -d --build
scripts\start_tunnel_named.cmd
```

然后浏览器访问域名，App 重新构建后连接同一个域名。
