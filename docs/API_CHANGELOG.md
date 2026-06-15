# API 更改清单（供后期合并参考）

**分支建议**：`feature/mobile-app` 或 `feature/api`  
**日期**：2026-06-14  
**作者**：全栈（APP + API）  
**说明**：新增 REST API 层，**未修改** Web 端 `views.py` / 模板；Web 行为保持不变。

---

## 新增文件

| 文件 | 说明 |
|------|------|
| `bookstore/api/__init__.py` | API 包说明 |
| `bookstore/api/auth_tokens.py` | Token 签发/注销（Django Cache，无新表） |
| `bookstore/api/authentication.py` | DRF `CustomerTokenAuthentication` |
| `bookstore/api/permissions.py` | `IsCustomer` 权限（对应 `@customer_required`） |
| `bookstore/api/serializers.py` | JSON 序列化（图书封面、订单、账户） |
| `bookstore/api/services.py` | 业务逻辑层，对齐 `views.py` 各函数 |
| `bookstore/api/views.py` | API 视图（含 Web 对应关系注释） |
| `bookstore/api/urls.py` | `/api/` 路由表 |
| `requirements.txt` | 项目依赖（含 `djangorestframework`） |
| `docs/API.md` | 接口文档 |
| `docs/API_CHANGELOG.md` | 本文件 |

---

## 修改文件

| 文件 | 改动 |
|------|------|
| `MyBookwise/settings.py` | `INSTALLED_APPS` 增加 `rest_framework`；新增 `REST_FRAMEWORK` 配置块 |
| `MyBookwise/urls.py` | 增加 `path("api/", include("bookstore.api.urls"))` |

---

## 未改动（刻意保留给 Web 组 / 原功能）

| 文件 | 说明 |
|------|------|
| `bookstore/views.py` | Web 页面逻辑原样保留 |
| `bookstore/models.py` | 无变更 |
| `bookstore/signals.py` | 无变更；API 通过 `process_payment` 等同函数复用 |
| `bookstore/admin.py` | 无变更 |
| `templates/` | 无变更 |
| `mobile/` | APP 端待对接新 API |

---

## 依赖安装

```bash
pip install -r requirements.txt
# 或仅 API：
pip install djangorestframework
```

---

## 合并时注意

1. **settings.py 冲突**：保留 `rest_framework` 与 `REST_FRAMEWORK` 两段配置。  
2. **urls.py 冲突**：`/api/` 路由应放在 Web 路由 `""` **之前**。  
3. **购物车统一**：Web 与 API 均使用 `bookstore/cart_store.py`（Cache key: `cart:{customer_id}`），同一账号双端购物车一致。  
4. **Token 存储**：默认 Django 内存 Cache，**重启 runserver 后 Token 失效**；生产可改 `CACHES` 为 Redis。  
5. **settings.py 在 .gitignore 中**：若协作者本地无此文件，需手动添加上述 DRF 配置或提供 `settings.example.py`。

---

## API ↔ Web 功能映射速查

```
auth/login          → customer_login
auth/register       → customer_register
auth/logout         → customer_logout
books/              → index
books/search        → search
books/<isbn>        → book_detail
cart/               → cart_detail
cart/items          → cart_add
cart/items/<isbn>   → cart_update / cart_remove
orders/preview      → order_confirm (GET)
orders/ (POST)      → order_confirm (POST)
orders/ (GET)       → order_list
orders/<id>         → order_detail
orders/<id>/pay     → pay_order
orders/<id>/cancel  → cancel_order
orders/<id>/confirm-receipt → confirm_receipt
account/            → account_recharge (GET) + account_edit (PATCH)
account/recharge    → account_recharge (POST)
account/repay       → repay_overdraft (POST)
```

---

## 后续 APP 对接 TODO

- [ ] Retrofit `baseUrl` 指向 `/api/`
- [ ] 登录后持久化 `token`（SharedPreferences）
- [ ] 静态封面 URL 拼接服务器地址
- [ ] 按 `docs/API.md` 实现各页面
