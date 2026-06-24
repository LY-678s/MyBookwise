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

服务器地址在 **`mobile/settings.properties`**（勿提交 Git）：

```powershell
cd mobile
copy settings.properties.example settings.properties
# 编辑 server_base=...
```

| 场景 | `server_base` 示例 |
|------|-----|
| **公网 / 队友子域名** | `https://mybookwise.xyz` 或 `https://xxx.example.com` |
| **Android 模拟器** | `http://10.0.2.2:8000` |
| **真机同 Wi-Fi** | `http://192.168.x.x:8000`（`ipconfig` 查电脑 IP） |
| **临时隧道** | `https://xxxx.trycloudflare.com` |

修改后 **Sync Gradle + Rebuild**；`ApiClient` 通过 BuildConfig 读取，无需改 Kotlin 源码。

## 真机联调（同局域网）

1. 查电脑 IP：`ipconfig` → WLAN 的 IPv4
2. 在 `settings.properties` 设置 `server_base=http://该IP:8000`
3. 后端：`python manage.py runserver 0.0.0.0:8000`

## 跨网联调（cloudflared）

见项目根 [README.md](../README.md)。隧道地址写入 `settings.properties` 的 `server_base`（**https，无末尾斜杠**），Rebuild APP。