# MyBookwise REST API 文档

> 供 `mobile/` Android APP 调用。Web 端与 API 共用 `bookstore/api/services.py` 业务逻辑。  
> 基础 URL：`http://<host>:8000/api/`

## 认证

登录/注册成功后返回 `token`，后续请求携带：

```http
Authorization: Token <token>
Content-Type: application/json
```

Token 有效期 7 天（Django Cache 存储，重启服务会失效）。

---

## 接口一览

| 方法 | 路径 | 说明 | 需登录 |
|------|------|------|--------|
| POST | `/api/auth/login/` | 登录 | 否 |
| POST | `/api/auth/register/` | 注册 | 否 |
| POST | `/api/auth/logout/` | 登出 | 是 |
| GET | `/api/auth/me/` | 当前用户摘要 | 是 |
| GET | `/api/books/` | 图书列表 | 否 |
| GET | `/api/books/search/?q=` | 搜索 | 否 |
| GET | `/api/books/<isbn>/` | 图书详情 | 否 |
| GET | `/api/cart/` | 购物车 | 是 |
| POST | `/api/cart/items/` | 加购 | 是 |
| PUT | `/api/cart/items/<isbn>/` | 改数量 | 是 |
| DELETE | `/api/cart/items/<isbn>/` | 移除 | 是 |
| GET | `/api/orders/preview/` | 下单预览 | 是 |
| GET | `/api/orders/` | 订单列表（仅已支付） | 是 |
| POST | `/api/orders/` | 创建订单并返回支付链接 | 是 |
| GET | `/api/orders/<id>/` | 订单详情 | 是 |
| POST | `/api/orders/<id>/abandon/` | 放弃待支付订单 | 是 |
| POST | `/api/orders/<id>/cancel/` | 取消订单 | 是 |
| POST | `/api/orders/<id>/confirm-receipt/` | 确认收货 | 是 |
| GET | `/api/account/` | 账户 / 会员摘要 | 是 |
| PATCH | `/api/account/` | 修改个人信息 | 是 |
| POST | `/api/membership/activate/` | 免费开通会员 | 是 |
| POST | `/api/membership/checkout/` | 购买畅读卡（返回 Stripe 链接） | 是 |
| POST | `/api/membership/confirm/` | 畅读卡支付完成确认 | 是 |
| POST | `/api/payments/stripe/webhook/` | Stripe Webhook（服务端） | 否 |

### 已废弃（返回 410 Gone）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/orders/<id>/pay/` | 请重新下单并完成支付 |
| POST | `/api/account/repay/` | 已移除信用购书/还款 |

---

## 请求/响应示例

### 登录

```http
POST /api/auth/login/
{"username": "alice", "password": "123456"}
```

```json
{
  "success": true,
  "message": "登录成功",
  "token": "a1b2c3...",
  "customer": {
    "customerid": 1,
    "name": "Alice",
    "levelid": 1,
    "discount_rate": "0.95",
    "discount_percent": "5.00"
  }
}
```

### 账户 / 会员摘要

```http
GET /api/account/
Authorization: Token xxx
```

```json
{
  "success": true,
  "account": {
    "customerid": 1,
    "username": "alice",
    "name": "Alice",
    "levelid": 2,
    "points": 1500,
    "is_member": true,
    "member_level": 2,
    "has_reading_pass": false,
    "effective_discount_rate": "0.93"
  },
  "stripe_configured": true,
  "member_level_guide": [
    {"level": 1, "points_required": 0, "discount_rate": "0.95", "discount_percent": "5.00"}
  ]
}
```

### 加购

```http
POST /api/cart/items/
Authorization: Token xxx
{"isbn": "978-7-115-48935-5", "quantity": 2}
```

### 下单（Stripe 在线支付）

```http
POST /api/orders/
Authorization: Token xxx
{
  "shipping_name": "张三",
  "shipping_contact": "zhang@example.com",
  "shipping_address": "武汉市洪山区xxx",
  "success_url": "bookwise://pay/success?order_id={order_id}&session_id={CHECKOUT_SESSION_ID}",
  "cancel_url": "bookwise://pay/cancel?order_id={order_id}"
}
```

```json
{
  "success": true,
  "message": "订单已创建，请完成支付",
  "order": { "orderid": 12, "paymentstatus": 0, "totalamount": "144.00" },
  "checkout_url": "https://checkout.stripe.com/..."
}
```

APP 应打开 `checkout_url` 完成支付；支付成功后调用 Stripe 回调或 `membership/confirm` / 订单 success URL 确认到账。

### 错误响应

```json
{"success": false, "error": "用户名或密码错误"}
```

---

## 状态码说明

| 字段 | 含义 |
|------|------|
| `paymentstatus` | 0=未付款 1=已付款 3=已退款（2 为历史遗留，对外显示为已支付） |
| `status` | 0=待处理 1=已发货 2=已完成 4=已取消 |

---

## Android 联调

- 模拟器 baseUrl：`http://10.0.2.2:8000/api/`
- 真机：电脑局域网 IP，如 `http://192.168.1.100:8000/api/`
- 公网：`https://mybookwise.xyz/api/`
- 封面图 URL 为相对路径（如 `/static/images/xxx.jpg`），APP 需拼接 baseUrl 主机部分
- Stripe 支付完成后通过 `bookwise://pay/...` deep link 回到 APP

---

## 模块结构

```text
bookstore/api/
├── auth_tokens.py      # Token 签发/校验（Cache）
├── authentication.py   # DRF 认证类
├── permissions.py      # IsCustomer 权限
├── serializers.py      # Model → JSON
├── services.py         # 业务逻辑（订单、会员、Stripe）
├── views.py            # HTTP 入口
└── urls.py             # 路由
```

**购物车**：Web 与 APP **共用**同一份服务端购物车（`cart_store.py`，按 `customer_id` 存 Cache）。同一账号在网页加购后，APP 刷新即可看到相同内容。
