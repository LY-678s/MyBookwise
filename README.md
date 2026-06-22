# MyBookwise 网上书店系统

双端课设项目：Web 端（Django）+ Android APP（Kotlin + Compose），共用同一套后端和 MySQL 数据库。

---

## 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置数据库
复制 `MyBookwise/settings.example.py` 为 `MyBookwise/settings.py`，修改数据库账号密码：
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "bookstoredb",
        "USER": "root",
        "PASSWORD": "你的密码",
        "HOST": "localhost",
        "PORT": "3306",
    }
}
```

### 3. 初始化数据库（首次）
见下方「数据库导入指南」。

### 4. 启动后端
```bash
# 仅本机访问（Web 开发）
python manage.py runserver

# 允许手机/APP 访问（真机联调）
python manage.py runserver 0.0.0.0:8000
```

### 5. 访问
- **Web**：http://127.0.0.1:8000
- **Admin 后台**：http://127.0.0.1:8000/admin（账号 admin，密码见 setdatabase.sql）
- **APP**：Android Studio 打开 `mobile/` 目录，配置 `ApiClient.kt` 中的服务器地址后运行

---

## 数据库导入指南

### 首次建库（新成员/新环境）

**步骤 1：创建数据库**
```sql
-- 在 MySQL 中执行
CREATE DATABASE bookstoredb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**步骤 2：导入基础结构和初始数据**

> ⚠️ **必须用 Python 脚本导入，不要用 PowerShell 管道**，否则中文会变成 `?`。

```bash
# 在项目根目录执行
python SetDatabase/init_db.py
```

如果没有 `init_db.py`，也可以用 MySQL 命令行（注意加 `--default-character-set`）：
```bash
# Windows CMD（不是 PowerShell）
mysql --default-character-set=utf8mb4 -u root -p bookstoredb < SetDatabase/setdatabase.sql

# PowerShell 需要用管道方式，不支持 < 重定向
Get-Content "SetDatabase\setdatabase.sql" -Encoding UTF8 | mysql --default-character-set=utf8mb4 -u root -p bookstoredb
```

**步骤 3：导入豆瓣图书数据集（可选，约 1000 本中文书）**
```bash
# 需要先有 SetDatabase/book_douban.csv
python SetDatabase/import_douban.py
```

---

### 恢复初始数据库（测试后重置）

测试过程中可能会产生大量订单、修改余额、触发缺货记录等。如需恢复到初始演示状态：

**方式 A：只重置业务数据（保留图书，不重建表）**
```bash
python SetDatabase/reset_demo_data.py
```

**方式 B：完整重建（清空所有数据，重新导入）**
```bash
# 1. 重新导入完整 SQL（重建表结构和初始数据）
Get-Content "SetDatabase\setdatabase.sql" -Encoding UTF8 | mysql --default-character-set=utf8mb4 -u root -p bookstoredb

# 2. 重新导入图书数据集
python SetDatabase/import_douban.py
```

---

### 重置演示数据说明（reset_demo_data.py）

该脚本将以下数据恢复到初始状态，不影响图书表：

| 表 | 操作 |
|---|---|
| `customer` | 恢复 5 个演示顾客的余额/信用/等级 |
| `orders` / `orderdetail` | 清空所有订单 |
| `shortagerecord` | 清空缺货记录 |
| `procurement` / `procurementdetail` | 清空采购记录 |

---

## 测试流程（演示用例）

### 顾客端
#### 1. 注册
通过账号密码注册，并可以引导输入个人详细信息——地址、联系方式等。

#### 2. 搜索
书名 / 关键字 / ISBN

#### 3. 购物车添加
可以调整数量，点击即可成功添加至购物车。
当输入数量大于库存时，会提示需要输入 ≤ 库存的数量。

#### 4. 下单与付款

##### 4.1 信用等级 1/2 级（只能余额支付）
```
CustomerID=1, TotalSpent=285.30, Balance=714.70, LevelID=1
CustomerID=4, TotalSpent=1300.00, Balance=2000.00, LevelID=2
ISBN='978-7-115-48935-5', StockQty=40, quantity=5
```
预期：下单时 TotalSpent 增加，Balance 减少；明细全部 IsShipped=1 后订单 Status 变为 1。

##### 4.2 信用等级 3/4/5 级（可使用信用支付）
```
CustomerID=5, TotalSpent=2022.15, Balance=3000.00, LevelID=3
CustomerID=2, TotalSpent=1300.00, Balance=2000.00, LevelID=4
CustomerID=3, TotalSpent=285.30,  Balance=714.70,  LevelID=5
```
五种场景：余额充足 / 仅余额 / 混合 / 均不足 / 纯信用。

##### 5. 信用升级
```
CustomerID=5, TotalSpent=2022.15, LevelID=3
ISBN='978-7-302-51123-4', quantity=12
ISBN='978-7-111-54425-7', quantity=10
预期：totalamount=2181.10，等级由 3 升至 4
```

#### 6. 我的订单
历史订单详情、补款、确认收货。

#### 7. 我的主页
修改密码、联系方式、地址；充值；查看余额/信用等级/信用余额。

---

### 管理员端
#### 1. 缺货登记和采购单
- 顾客下单导致库存低于 MinStockLimit 时自动生成缺货记录和采购单
- 采购单标记为「已到货入库」时自动补库存、标记缺货单已处理
- 可手动添加、可搜索

#### 2. 订单管理
- 修改订单状态：已发货 / 已完成 / 已取消
- 禁止将已取消订单重新打开

#### 3. 数据管理
客户、图书、图书作者、信用等级规则、供应商信息、供货关系均可增删改查。

---

## APP 联调地址

修改 `mobile/app/src/main/java/com/example/bookwiseapp/data/api/ApiClient.kt` 中的 `SERVER_BASE`：

| 场景 | SERVER_BASE |
|---|---|
| Android 模拟器 | `http://10.0.2.2:8000` |
| 真机（同 Wi-Fi / USB 共享网络） | `http://电脑局域网IP:8000` |
| **跨网访问（手机 4G、不同 Wi-Fi）** | `https://xxxx.trycloudflare.com`（见下方） |

后端须以 `0.0.0.0:8000` 启动才能接受手机请求。

---

## 跨网访问（内网穿透）

手机和电脑**不在同一局域网**时（例如手机用 4G、同学在别的网络），需要把本机 Django 暴露到公网。推荐 **cloudflared**（Cloudflare 快速隧道）：**免注册、一条命令**。

### 一次性安装 cloudflared

```powershell
# 方式 A：winget（Windows 推荐）
winget install Cloudflare.cloudflared

# 方式 B：手动下载
# https://github.com/cloudflare/cloudflared/releases
# 下载 cloudflared-windows-amd64.exe，放到 PATH 或项目根 directory
```

安装后执行 `cloudflared --version` 确认可用。

### 每次演示操作（两个终端）

**终端 1 — 启动 Django**

```powershell
cd d:\Engineering\MyBookwise

# 先启动隧道拿到 URL 后，在本终端设置（Web 登录需要，APP 可省略）
# 把下面的地址换成终端 2 输出的 https://....trycloudflare.com
$env:TUNNEL_ORIGIN = "https://xxxx.trycloudflare.com"

python manage.py runserver 0.0.0.0:8000
```

**终端 2 — 启动隧道**

```powershell
cloudflared tunnel --url http://localhost:8000
```

终端 2 会输出类似：

```
Your quick Tunnel has been created! Visit it at:
https://random-words-xxxx.trycloudflare.com
```

复制这个 **https** 地址，按下面三步配置。

### 配置清单

| 步骤 | 做什么 |
|------|--------|
| ① | 终端 1 设置 `$env:TUNNEL_ORIGIN = "https://你复制的地址"`，**重启** `runserver`（Web 表单需要） |
| ② | 修改 `ApiClient.kt`：`const val SERVER_BASE = "https://你复制的地址"`（不要末尾斜杠） |
| ③ | Android Studio **Rebuild** 后安装到手机 |

### 验证

- 手机浏览器（可开 4G）打开 `https://xxxx.trycloudflare.com` → 应看到书城首页
- 打开 APP → 登录 `zhangsan` / `pass123` → 首页能加载图书即成功

### 注意事项

- **隧道 URL 每次重启 cloudflared 都会变**，需重复上述 ①② 步
- **电脑和 cloudflared 必须保持运行**，关掉后外网无法访问
- 仅用于课设演示，`DEBUG=True` 不要长期暴露公网
- 穿透走 **HTTPS**，APP 无需改 `network_security_config.xml`
- 也可用项目脚本一键开隧道：`powershell -File scripts/start_tunnel.ps1`

### 常见问题

| 现象 | 处理 |
|------|------|
| `DisallowedHost` | 确认 `settings.py` 含 `.trycloudflare.com`，重启 Django |
| Web 登录报 CSRF 403 | 设置 `$env:TUNNEL_ORIGIN` 并重启 runserver |
| APP 网络错误 | 检查 `SERVER_BASE` 是否为 **https** 且与隧道地址一致 |
| cloudflared 找不到命令 | 重新打开终端，或把 exe 所在路径加入 PATH |
