"""
bookstore.api — 移动端 REST API

与 Web 端 views.py 功能一一对应，供 Android APP 调用。
认证方式：Header `Authorization: Token <token>`（登录/注册后返回）。
购物车：按 customer_id 存 Django Cache（与 Web Session 购物车独立，逻辑一致）。
"""
