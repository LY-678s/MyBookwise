mobile/app/src/main/java/com/example/bookwiseapp/
├── BookwiseApplication.kt        # App 入口，恢复 Token
├── MainActivity.kt                # 判断是否已登录，进入 AppNav
├── data/
│   ├── api/
│   │   ├── ApiClient.kt           # Retrofit 单例 + Token 拦截器
│   │   ├── ApiService.kt          # 22 个接口定义
│   │   └── model/ApiModels.kt     # 所有请求/响应数据类
│   ├── local/TokenStore.kt        # DataStore 持久化 Token
│   └── repository/               # 5 个 Repository，对应 API 分组
├── viewmodel/                    # 5 个 ViewModel（StateFlow）
└── ui/
    ├── component/CommonComponents.kt  # BookCover、LoadingOverlay、InfoRow 等
    ├── navigation/AppNav.kt       # Navigation + 底部 Tab
    └── screen/                   # 10 个页面
        ├── LoginScreen.kt
        ├── RegisterScreen.kt
        ├── HomeScreen.kt          # 书城首页（2 列网格）
        ├── SearchScreen.kt        # 书名/ISBN/关键字搜索
        ├── BookDetailScreen.kt    # 图书详情 + 加购
        ├── CartScreen.kt          # 购物车 + 数量调节
        ├── CheckoutScreen.kt      # 确认订单 + 收货信息 + 付款方式
        ├── OrderListScreen.kt     # 订单列表
        ├── OrderDetailScreen.kt   # 订单详情 + 操作（补款/取消/确认收货）
        └── AccountScreen.kt       # 账户 + 充值 + 还款 + 编辑资料

`ApiClient.kt` 中的 `SERVER_BASE` 控制所有请求地址：

```kotlin
const val SERVER_BASE = "http://10.0.2.2:8000"
```

| 场景 | 值 |
|------|-----|
| **Android 模拟器** | `http://10.0.2.2:8000` |
| **真机同 Wi-Fi** | `http://192.168.x.x:8000`（`ipconfig` 查电脑 IP） |
| **跨网（4G / 不同 Wi-Fi）** | `https://xxxx.trycloudflare.com`（见根 README「跨网访问」） |

## 真机联调（同局域网）

1. 查电脑 IP：`ipconfig` → WLAN 的 IPv4
2. 改 `SERVER_BASE` 为 `http://该IP:8000`
3. 后端：`python manage.py runserver 0.0.0.0:8000`

## 跨网联调（最简单：cloudflared）

手机和电脑不在同一网络时使用，**免注册**。完整步骤见项目根 [README.md](../README.md) 的「跨网访问」章节，简要流程：

1. 安装：`winget install Cloudflare.cloudflared`
2. 终端 A：`python manage.py runserver 0.0.0.0:8000`
3. 终端 B：`powershell -File scripts/start_tunnel.ps1`（或 `cloudflared tunnel --url http://localhost:8000`）
4. 复制输出的 `https://....trycloudflare.com`
5. 改 `SERVER_BASE` 为该地址（**https，无末尾斜杠**）
6. Rebuild APP；Web 演示还需在后端终端设 `$env:TUNNEL_ORIGIN` 并重启 runserver