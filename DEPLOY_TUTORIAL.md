# MyBookwise 部署与使用教程

这份文档是给第一次接触这个项目的人看的。目标很简单：照着做，就能把网站、App、Docker 和 Cloudflare 隧道跑起来。

## 1. 先准备环境

你需要先装好这些东西：

- Python
- MySQL
- Docker Desktop
- Android Studio
- `cloudflared`

如果你只想先看 Web 页面，最少只需要 Python、MySQL 和 Docker Desktop。

## 2. 启动 Docker

先打开 Docker Desktop，确认它是运行状态。

然后在项目根目录执行：

```powershell
docker compose up -d --build
```

这一步会启动两个容器：

- `web`：Django 网站
- `db`：MySQL 数据库

检查是否启动成功：

```powershell
docker compose ps
```

如果看到 `web` 和 `db` 都是 `Up`，说明成功了。

## 3. 打开本地网站

浏览器访问：

```text
http://127.0.0.1:8000
```

如果能打开首页，说明 Docker 里的网站已经跑起来。

## 4. 配置 Cloudflare 域名

如果你要让外网访问，就要用 Cloudflare Tunnel。

先确认你已经拿到了 Cloudflare 账号权限，并且能看到域名，比如：

- `mybookwise.xyz`
- `ly.mybookwise.xyz`

然后检查本机隧道配置文件：

```text
scripts/cloudflared-mybookwise.yml
```

这个文件里要写：

- `tunnel` 的 UUID
- `credentials-file` 的本机路径
- `hostname` 对应你要使用的域名

启动隧道：

```powershell
scripts\start_tunnel_named.cmd
```

如果一切正常，就可以访问：

```text
https://ly.mybookwise.xyz
```

或者你的主域名：

```text
https://mybookwise.xyz
```

## 5. 配置 App

App 的后端地址放在：

```text
mobile/settings.properties
```

先复制示例文件：

```powershell
cd mobile
copy settings.properties.example settings.properties
```

然后修改：

```properties
server_base=https://ly.mybookwise.xyz
```

如果你想连主域名，就写：

```properties
server_base=https://mybookwise.xyz
```

修改后要重新运行或 Rebuild Android 项目。

## 6. App 怎么用

App 里主要看这几个页面：

- 首页
- 搜索
- 图书详情
- 购物车
- 收藏夹
- 订单列表
- 账户页面

App 的请求都走后端 API，不直接连数据库。

## 7. 数据库从哪里来

Docker 里的数据库第一次启动时，会自动导入：

```text
SetDatabase/bookstoredb.sql
```

所以 Docker 数据库和你本地 Navicat 里的数据库不是同一个。你本地改库，不会自动影响 Docker。

如果你想重新初始化 Docker 数据库：

```powershell
docker compose down -v
docker compose up -d --build
```

## 8. 常见问题

如果 Cloudflare 报 `127.0.0.1:8000 refused`，先检查：

- Docker 的 `web` 容器是否还在运行
- 本机 `http://127.0.0.1:8000` 能不能打开
- `cloudflared` 是否还在运行

如果 App 打不开网站，先检查：

- `mobile/settings.properties` 里的 `server_base`
- 你是否重新 Rebuild 了 App
- 域名是否和 cloudflared 配置一致

## 9. 最短启动顺序

```powershell
docker compose up -d --build
scripts\start_tunnel_named.cmd
```

然后：

- 浏览器访问域名
- App 重新构建后使用同一个域名访问后端
