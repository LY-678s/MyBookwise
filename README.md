# 1. 启动后端（Web + API 同一个服务）

python manage.py runserver 0.0.0.0:8000

# 2. Web：浏览器打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)

开启隧道后打开[https://mybookwise.xyz](https://mybookwise.xyz)

# 3. APP：mobile/ 里单独 build/run，baseUrl 指向后端

Android 模拟器常用 [http://10.0.2.2:8000](http://10.0.2.2:8000)
真机演示用电脑局域网 IP，如 [http://192.168.x.x:8000](http://192.168.x.x:8000)

---

## 数据库

**唯一数据文件**：`SetDatabase/bookstoredb.sql`

已包含完整库结构、演示数据，以及会员体系 / Stripe 支付表 / 库存触发器修复等全部变更，**无需再执行其他 SQL**。

### 首次导入

```powershell
# 1. 创建数据库（MySQL 中执行一次即可）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS bookstoredb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. 导入（在项目根目录；PowerShell 不要用 <，任选其一）

# 方式 A：cmd 重定向
cmd /c "mysql --default-character-set=utf8mb4 -u root -p bookstoredb < SetDatabase\bookstoredb.sql"

# 方式 B：PowerShell 管道
Get-Content SetDatabase\bookstoredb.sql -Raw -Encoding UTF8 | mysql --default-character-set=utf8mb4 -u root -p bookstoredb
```

`settings.py` 中 `DATABASES` 的库名、用户名、密码需与上面一致。

### 重置数据库（测试后恢复初始状态）

测试过程中若产生大量订单、积分变动等，用同一 SQL **整库覆盖**即可：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u root -p bookstoredb < SetDatabase\bookstoredb.sql"
# 或
Get-Content SetDatabase\bookstoredb.sql -Raw -Encoding UTF8 | mysql --default-character-set=utf8mb4 -u root -p bookstoredb
```

> 会清空并重建 `bookstoredb` 内所有表和数据，图书、顾客、订单等均回到 SQL 文件中的初始状态。

导入完成后重启 Django：`python manage.py runserver 0.0.0.0:8000`

---

# 数据库课设——网上图书管理系统

以下是主要功能模块测试流程示例

## 顾客端

### 1.注册

通过账号密码注册，并可以引导输入个人详细信息——地址、联系方式等。

### 2.搜索

书名/关键字/isbn

### 3.购物车添加

可以调整数量，点击即可成功添加至购物车。
当输入数量大于库存时，会提示需要输入<=库存的数

### 4. 会员与积分

- 注册后默认为**非会员**（0 级），无折扣、不累计积分
- 在「会员与积分」页**免费开通会员**后，才按等级享受折扣并获得积分
- 积分与人民币 1:1（每消费 1 元得 1 积分）
- 等级由累计积分决定：1 级（0+）→ 2 级（1000+）→ 3 级（2000+）→ 4 级（5000+）→ 5 级（10000+，最高档积分显示 max）
- 各等级折扣见「会员与积分」页「详情」按钮
- 会员可购买 **¥20/月畅读卡**，在等级折扣基础上再享 7.2 折（叠加计算）

### 5. 下单与在线支付

- 加购 → 订单确认页填写收货信息 → 提交后跳转 **Stripe 在线支付**
- 支付成功后订单变为已付款，购物车清空；**会员**消费金额按 1:1 累计积分
- **未支付订单**不在「我的订单」中展示；支付取消或放弃会自动作废
- 非会员下单无折扣，仍可正常购书
- 需在 `settings.py` 配置 Stripe 测试密钥后支付流程才可用

### 6. 我的订单

- 仅展示**已支付**及之后状态的订单
- 待发货订单可取消（已付金额退回、扣回积分）
- 已发货订单不可取消；收货后可「确认收货」完成订单

### 7. 我的主页 / 会员与积分

- 修改密码、联系方式、地址
- 查看会员等级、积分、畅读卡有效期
- 免费开通会员、购买畅读卡（在线支付）

## 管理员端

入口：`http://127.0.0.1:8000/admin/`（公网：`https://mybookwise.xyz/admin/`）

### 登录账号（`auth_user` 表，演示数据）

| 用户名 | 密码 | 邮箱 | 说明 |
|--------|------|------|------|
| `admin` | `admin123` | admin@bookstore.com | 超级管理员 |
| `testadmin` | `admin123` | test@admin.com | 超级管理员（测试用） |

> 若无法登录，在项目根目录执行：`python manage.py changepassword admin`

导入 `SetDatabase/bookstoredb.sql` 后上述账号即可使用。顾客端账号（如 `zhangsan` / `pass123`）**不能**登录管理员后台。

### 与当前业务的对齐情况

| 模块 | 管理员端能力 |
|------|----------------|
| **订单** | 仅查看与改状态（已下单 / 已发货 / 已完成 / 已取消）；**不可**在后台创建订单；`paymentstatus` 只读（Stripe 在线支付后自动更新） |
| **顾客** | 维护账号、等级（`levelid`）；会员积分在「会员档案」中维护 |
| **会员档案** | 查看/编辑积分、`member_since`、畅读卡到期时间（`customer_profile`） |
| **Stripe 支付记录** | 只读查看 Checkout 会话（订单 / 畅读卡） |
| **会员等级** | 维护 `creditlevel`（含 0 级非会员、1–5 级会员折扣） |
| **图书 / 作者 / 供应商 / 采购 / 缺货** | 增删改查，逻辑未变 |

订单由顾客端下单并经 **Stripe 支付** 完成后才出现在列表（未支付订单会被系统自动作废，不在顾客端展示）。

### 1. 缺货登记和采购单

- 当顾客端订单使得库存低于最小限制时，将在数据库中自动生成缺货登记和采购单
- 当采购单状态为已到货入库时，缺货单要自动将 status 标记为 1（已处理），且图书库存也自动补上
- 可以手动添加采购记录和缺货登记
- 可搜索

### 2. 订单

- 批量操作：标记为已发货、已完成、已取消
- 可搜索、按付款状态与日期筛选
- 禁止将已取消订单重新打开（数据库触发器会拦截）

### 3. 客户、图书、会员等级、供应商等

均可实现增删改查（支付相关字段由系统维护，不可手改）。

1. **客户**：用户名、密码、地址、等级等；会员积分在「会员档案」中维护
2. **会员档案**：积分、开通时间、畅读卡有效期
3. **图书 / 作者**：书目与作者关系管理
4. **会员等级（creditlevel）**：0 级（非会员）与 1–5 级折扣规则
5. **供应商 / 供货 / 采购 / 缺货**：供应链与库存补货流程

---

## APP 联调地址

修改 `mobile/app/src/main/java/com/example/bookwiseapp/data/api/ApiClient.kt` 中的 `SERVER_BASE`：


| 场景                     | SERVER_BASE                      |
| ---------------------- | -------------------------------- |
| Android 模拟器            | `http://10.0.2.2:8000`           |
| 真机（同 Wi-Fi / USB 共享网络） | `http://电脑局域网IP:8000`            |
| **公网固定域名（推荐）**         | `https://mybookwise.xyz`         |
| 临时穿透（快速隧道）             | `https://xxxx.trycloudflare.com` |


后端须以 `0.0.0.0:8000` 启动才能接受手机请求。

---

## 公网域名 mybookwise.xyz（固定地址，推荐）

域名已通过 Cloudflare 管理时，用 **命名隧道** 把本机 Django 映射到 `https://mybookwise.xyz`，地址固定、APP 不用反复改。

### 一次性配置

**1. 域名接入 Cloudflare**

- 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)，添加站点 `mybookwise.xyz`
- 在域名注册商处把 **DNS 服务器** 改为 Cloudflare 提供的 NS（状态变为 Active）

**2. 安装 cloudflared**

```powershell
winget install Cloudflare.cloudflared
```

**3. 登录并创建隧道**

```powershell
cloudflared tunnel login
cloudflared tunnel create mybookwise
```

记下输出的 **Tunnel UUID**（形如 `a1b2c3d4-...`）。

**4. 绑定 DNS（CNAME 指向隧道）**

```powershell
cloudflared tunnel route dns mybookwise mybookwise.xyz
cloudflared tunnel route dns mybookwise www.mybookwise.xyz
```

在 Cloudflare DNS 页面应出现两条 CNAME，Proxied（橙色云）即可。

**5. 本地隧道配置文件**

```powershell
cd d:\Engineering\MyBookwise
copy scripts\cloudflared-mybookwise.yml.example scripts\cloudflared-mybookwise.yml
```

编辑 `scripts/cloudflared-mybookwise.yml`，填入：

- `tunnel:` 你的 UUID
- `credentials-file:` 凭证路径，一般为 `C:\Users\你的用户名\.cloudflared\<UUID>.json`

> `cloudflared-mybookwise.yml` 含本机路径，已在 `.gitignore`，勿提交 Git。

**6. 项目内网络配置（已完成，核对即可）**


| 位置                       | 配置                                                                                   |
| ------------------------ | ------------------------------------------------------------------------------------ |
| `MyBookwise/settings.py` | `ALLOWED_HOSTS` 含 `mybookwise.xyz`；`CSRF_TRUSTED_ORIGINS` 含 `https://mybookwise.xyz` |
| `ApiClient.kt`           | `SERVER_BASE = "https://mybookwise.xyz"`                                             |


修改 settings 后需重启 Django。

### 每次演示（两个终端）

**终端 1 — Django**

```powershell
cd d:\Engineering\MyBookwise
python manage.py runserver 0.0.0.0:8000
```

**终端 2 — 命名隧道**

```powershell
scripts\start_tunnel_named.cmd
```

验证：浏览器打开 [https://mybookwise.xyz](https://mybookwise.xyz) ；手机 4G 打开 APP（Rebuild 后）。

### 常见问题


| 现象               | 处理                                                        |
| ---------------- | --------------------------------------------------------- |
| 域名无法访问           | 确认隧道终端在跑、DNS 已生效（可能需等待几分钟）                                |
| `DisallowedHost` | 检查 `settings.py` 的 `ALLOWED_HOSTS`，重启 Django              |
| Web 登录 CSRF 403  | 确认 `CSRF_TRUSTED_ORIGINS` 含 `https://mybookwise.xyz`      |
| APP 连不上          | `SERVER_BASE` 为 `https://mybookwise.xyz`（无末尾 `/`），Rebuild |


---

## 跨网访问（临时快速隧道，备选）

不想配固定域名、或隧道未就绪时，仍可用 **trycloudflare.com** 临时地址：

### 一次性安装

```powershell
winget install Cloudflare.cloudflared
```

### 每次演示（两个终端）

**终端 1 — Django**

```powershell
cd d:\Engineering\MyBookwise
# 拿到隧道 URL 后设置（Web 登录需要）
$env:TUNNEL_ORIGIN = "https://xxxx.trycloudflare.com"
python manage.py runserver 0.0.0.0:8000
```

**终端 2 — 隧道**

```powershell
scripts\start_tunnel.cmd
# 或：cloudflared tunnel --url http://localhost:8000
```

复制终端 2 输出的 `https://....trycloudflare.com`，写入 `$env:TUNNEL_ORIGIN` 和 `ApiClient.kt` 的 `SERVER_BASE`，Rebuild APP。

### 常见问题


| 现象               | 处理                                             |
| ---------------- | ---------------------------------------------- |
| `DisallowedHost` | `settings.py` 含 `.trycloudflare.com`，重启 Django |
| Web 登录 CSRF 403  | 设置 `$env:TUNNEL_ORIGIN` 并重启 runserver          |
| APP 网络错误         | `SERVER_BASE` 用 **https** 且与隧道地址一致             |


