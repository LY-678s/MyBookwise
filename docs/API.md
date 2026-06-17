# MyBookwise REST API 文档

> 供 `mobile/` Android APP 调用。Web 端逻辑不变，API 与 `bookstore/views.py` 一一对应。  
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

| 方法 | 路径 | Web 对应 | 需登录 |
|------|------|----------|--------|
| POST | `/api/auth/login/` | `customer_login` | 否 |
| POST | `/api/auth/register/` | `customer_register` | 否 |
| POST | `/api/auth/logout/` | `customer_logout` | 是 |
| GET | `/api/auth/me/` | 账户摘要 | 是 |
| GET | `/api/books/` | `index` | 否 |
| GET | `/api/books/search/?q=` | `search` | 否 |
| GET | `/api/books/<isbn>/` | `book_detail` | 否 |
| GET | `/api/cart/` | `cart_detail` | 是 |
| POST | `/api/cart/items/` | `cart_add` | 是 |
| PUT | `/api/cart/items/<isbn>/` | `cart_update` | 是 |
| DELETE | `/api/cart/items/<isbn>/` | `cart_remove` | 是 |
| GET | `/api/orders/preview/` | `order_confirm` GET | 是 |
| GET | `/api/orders/` | `order_list` | 是 |
| POST | `/api/orders/` | `order_confirm` POST | 是 |
| GET | `/api/orders/<id>/` | `order_detail` | 是 |
| POST | `/api/orders/<id>/pay/` | `pay_order` | 是 |
| POST | `/api/orders/<id>/cancel/` | `cancel_order` | 是 |
| POST | `/api/orders/<id>/confirm-receipt/` | `confirm_receipt` | 是 |
| GET | `/api/account/` | `account_recharge` GET | 是 |
| PATCH | `/api/account/` | `account_edit` | 是 |
| POST | `/api/account/recharge/` | `account_recharge` POST | 是 |
| POST | `/api/account/repay/` | `repay_overdraft` | 是 |

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
  "customer": { "customerid": 1, "name": "Alice", "balance": "1000.00", ... }
}
```

### 加购

```http
POST /api/cart/items/
Authorization: Token xxx
{"isbn": "978-7-115-48935-5", "quantity": 2}
```

### 下单

```http
POST /api/orders/
Authorization: Token xxx
{
  "payment_choice": "balance",
  "shipping_name": "张三",
  "shipping_contact": "zhang@example.com",
  "shipping_address": "武汉市洪山区xxx"
}
```

`payment_choice`：`balance`（余额优先，可混用信用）| `credit`（纯信用，需 3 级及以上）

### 错误响应

```json
{"success": false, "error": "用户名或密码错误"}
```

---

## 状态码说明

| 字段 | 含义 |
|------|------|
| `paymentstatus` | 0=未付款 1=已全额支付 2=部分信用（未全额） |
| `status` | 0=待处理 1=已发货 2=已完成 4=已取消 |

---

## Android 联调

- 模拟器 baseUrl：`http://10.0.2.2:8000/api/`
- 真机：电脑局域网 IP，如 `http://192.168.1.100:8000/api/`
- 封面图 URL 为相对路径（如 `/static/images/xxx.jpg`），APP 需拼接 baseUrl 主机部分

---

## 模块结构

```text
bookstore/api/
├── auth_tokens.py      # Token 签发/校验（Cache）
├── authentication.py   # DRF 认证类
├── permissions.py    # IsCustomer 权限
├── serializers.py      # Model → JSON
├── services.py         # 业务逻辑（对齐 views.py）
├── views.py            # HTTP 入口
└── urls.py             # 路由
```

**购物车**：Web 与 APP **共用**同一份服务端购物车（`cart_store.py`，按 `customer_id` 存 Cache）。同一账号在网页加购后，APP 刷新即可看到相同内容。
