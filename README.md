# MyBookwise

MyBookwise 是一个面向数据库课程设计的网上书店系统，包含 Web 端、Android App、管理员后台和 Docker 部署方案。项目支持图书浏览、搜索、分类分区、购物车、订单、收藏夹、最近浏览、排行榜、推荐系统、会员与积分、畅读卡和 AI 书小智等功能。

## 项目功能

### 1. 顾客端

- 账号注册、登录、个人信息维护
- 图书浏览、搜索、分类分区、排行榜、首页推荐
- 图书详情、加入购物车、收藏夹、最近浏览
- 购物车结算、Stripe 在线支付、订单列表、订单详情
- 会员开通、积分累计、畅读卡购买
- AI 书小智问答助手

### 2. 管理员端

- 图书、作者、出版社、供应商、客户、会员等级等基础数据维护
- 订单状态、缺货登记、采购记录管理
- Stripe 支付记录只读查看

### 3. Android App

- App 与 Web 共用同一套后端 API 和数据库
- 支持图书、搜索、详情、收藏、购物车、订单、会员与支付
- 服务器地址通过 `mobile/settings.properties` 配置，不再硬编码
- 支付使用 Stripe Checkout，并通过 deep link 返回 App

## 核心规则

### 会员与积分

- 用户可免费开通会员，开通后才累计积分
- 消费金额与积分按 1:1 累计
- 会员等级根据累计积分自动判定
- 会员等级影响购书折扣
- 畅读卡在会员折扣基础上继续叠加折扣

### 订单与支付

当前项目只保留 Stripe 在线支付作为实际购书支付方式。旧版“信用支付 / 信用还款 / 余额抵扣”已不再作为当前主流程。

1. 顾客从购物车提交订单
2. 后端生成待支付订单，并返回 Stripe Checkout 链接
3. 用户在 Stripe 页面完成支付
4. 支付成功后，后端确认支付结果并标记订单已支付
5. 系统清空购物车，并按会员规则累计积分

如果 `STRIPE_SECRET_KEY` 未配置，在线支付会显示为暂不可用。

### 购物车

购物车已改为数据库持久化存储，Web 和 App 共用同一份数据。这样在 Docker + Gunicorn 多 worker 环境下，不会因为请求落到不同 worker 而随机出现“购物车为空”。

## 数据库

数据库初始化文件位于：

```text
SetDatabase/bookstoredb.sql
```

首次导入本地 MySQL：

```powershell
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS bookstoredb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
cmd /c "mysql --default-character-set=utf8mb4 -u root -p bookstoredb < SetDatabase\bookstoredb.sql"
```

## 本地运行

后端：

```powershell
python manage.py runserver 0.0.0.0:8000
```

App 服务器地址配置：

```properties
server_base=https://ly.mybookwise.xyz
```

常见地址：

- Android 模拟器：`http://10.0.2.2:8000`
- 真机同 Wi-Fi：`http://电脑局域网IP:8000`
- 公网域名：`https://ly.mybookwise.xyz`

## Docker 部署

Docker 文件已集中放在 `docker/` 目录。

- `docker/docker-compose.yml`：编排 Web 和 MySQL 服务
- `docker/Dockerfile`：构建 Django Web 镜像
- `docker/entrypoint.sh`：容器启动前等待数据库并收集静态文件
- `docker/Dockerfile.dockerignore`：控制镜像构建时忽略哪些文件
- `docker/.env.docker.example`：Docker 环境变量模板
- `docker/README.md`：Docker 目录文件说明
- `docker/DOCKER_DEPLOY.md`：Docker 部署讲解文档

常用命令请在项目根目录执行：

```powershell
docker compose -f docker/docker-compose.yml up -d --build
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f web
docker compose -f docker/docker-compose.yml down
```

重置 Docker 数据库卷：

```powershell
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d --build
```

## Cloudflare Tunnel

当前固定域名示例：

```text
https://ly.mybookwise.xyz
```

本地 tunnel 配置文件：

```text
scripts/cloudflared-mybookwise.yml
```

启动命名隧道：

```powershell
scripts\start_tunnel_named.cmd
```

Cloudflare Tunnel 会把公网域名转发到本机：

```text
http://127.0.0.1:8000
```

所以必须保证本机 Docker Web 服务正在监听 8000 端口。

## AI 书小智配置

项目内置 AI 助手“书小智”，用于图书推荐、购书流程、会员规则和站内功能问答。

当前支持：

- `deepseek`：默认方案，支持 DeepSeek 官方或 OpenAI 兼容接口
- `gemini`：Google Gemini

相关配置：

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-ai/DeepSeek-R1-0528-Qwen3-8B
DEEPSEEK_API_BASE=https://api.siliconflow.cn/v1
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
```

本地和 Docker 都会读取 `.env`。如果 `.env` 中的 key 为空，代码会回退到 `settings.py` 中的默认配置。

## 管理员示例账号

导入 `SetDatabase/bookstoredb.sql` 后，可使用：

| 用户名 | 密码 | 邮箱 | 说明 |
| --- | --- | --- | --- |
| `admin` | `admin123` | admin@bookstore.com | 超级管理员 |
| `testadmin` | `admin123` | test@admin.com | 测试管理员 |

后台入口：

- 本地：`http://127.0.0.1:8000/admin/`
- 域名：`https://ly.mybookwise.xyz/admin/`
