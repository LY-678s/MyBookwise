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

`ApiClient.kt` 第 16 行这一个常量控制所有请求地址：

```kotlin
const val SERVER_BASE = "http://10.0.2.2:8000"
```

| 场景 | 值 | 原理 |
|------|-----|------|
| **Android 模拟器**（当前默认） | `http://10.0.2.2:8000` | Android 模拟器把 `10.0.2.2` 映射到宿主机的 `localhost` |
| **真机**（手机和电脑同 Wi-Fi） | `http://192.168.x.x:8000` | 手机直接访问电脑局域网 IP |

## 真机联调怎么改

1. 查电脑的局域网 IP（PowerShell 执行 `ipconfig`，找 `WLAN` 的 IPv4 地址）
2. 把 `ApiClient.kt` 第 16 行改成：
   ```kotlin
   const val SERVER_BASE = "http://192.168.x.x:8000"  // 换成实际 IP
   ```
3. 后端必须用 `0.0.0.0:8000` 启动（已在 README 里）才能接受局域网请求：
   ```powershell
   python manage.py runserver 0.0.0.0:8000
   ```

手机和电脑在同一个 Wi-Fi 下就能联通。