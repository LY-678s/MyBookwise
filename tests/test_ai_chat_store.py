"""AI 聊天历史存储模块单元测试

覆盖函数：get_ai_history、save_ai_history、clear_ai_history、
         get_ai_history_for_request、save_ai_history_for_request、
         clear_ai_history_for_request、attach_customer_ai_history

测试方法分布：
- 等价类：正常读写、空历史
- 边界值：超过 20 条消息截断
- 场景法：登录合并 session 历史
- 独立路径：已登录/未登录分支
"""
from __future__ import annotations

import pytest

from bookstore.ai_chat_store import (
    get_ai_history,
    save_ai_history,
    clear_ai_history,
    get_ai_history_for_request,
    save_ai_history_for_request,
    clear_ai_history_for_request,
    attach_customer_ai_history,
    _MAX_MESSAGES,
)


pytestmark = pytest.mark.django_db


class _FakeSession(dict):
    """模拟 Django Session，支持 .modified 和 .pop()。"""
    modified = False

    def pop(self, key, *args):
        try:
            return super().pop(key, *args)
        except (KeyError, TypeError):
            return args[0] if args else None


def _make_request(session_data=None):
    """创建一个带 FakeSession 的简单 request 对象。"""
    class FakeRequest:
        pass
    req = FakeRequest()
    req.session = _FakeSession(session_data or {})
    return req


# =============================================================
# get / save / clear（按 customer_id 操作 cache）
# =============================================================

class TestAiHistoryBasic:
    """基础 CRUD 测试。"""

    def test_get_empty_history(self):
        """等价类：无历史 → 返回空列表。"""
        result = get_ai_history(999)
        assert result == []

    def test_save_and_get(self):
        """等价类：保存后读取 → 数据一致。"""
        history = [{"role": "user", "content": "你好"}]
        save_ai_history(1, history)
        result = get_ai_history(1)
        assert result == history

    def test_clear_removes_history(self):
        """场景：清空后读取 → 空列表。"""
        save_ai_history(1, [{"role": "user", "content": "测试"}])
        clear_ai_history(1)
        assert get_ai_history(1) == []

    def test_history_truncated_to_max(self):
        """边界值：超过 _MAX_MESSAGES 条 → 只保留最后 N 条。"""
        history = [{"role": "user", "content": f"消息{i}"} for i in range(30)]
        save_ai_history(1, history)
        result = get_ai_history(1)
        assert len(result) == _MAX_MESSAGES
        # 保留的是最后 _MAX_MESSAGES 条
        assert result[-1]["content"] == "消息29"

    def test_different_customers_isolated(self):
        """场景：不同顾客的历史互不影响。"""
        save_ai_history(1, [{"role": "user", "content": "顾客1"}])
        save_ai_history(2, [{"role": "user", "content": "顾客2"}])
        assert get_ai_history(1)[0]["content"] == "顾客1"
        assert get_ai_history(2)[0]["content"] == "顾客2"


# =============================================================
# get_ai_history_for_request（已登录 vs 未登录）
# =============================================================

class TestGetAiHistoryForRequest:

    def test_logged_in_reads_from_cache(self):
        """等价类：已登录 → 从 cache 读取。"""
        save_ai_history(42, [{"role": "user", "content": "缓存数据"}])
        req = _make_request({"customer_id": 42})
        result = get_ai_history_for_request(req)
        assert result[0]["content"] == "缓存数据"

    def test_not_logged_in_reads_from_session(self):
        """等价类：未登录 → 从 session 读取。"""
        req = _make_request({"ai_chat_history": [{"role": "user", "content": "临时"}]})
        result = get_ai_history_for_request(req)
        assert result[0]["content"] == "临时"

    def test_not_logged_in_no_session_history(self):
        """边界值：未登录且无 session 历史 → 空列表。"""
        req = _make_request({})
        result = get_ai_history_for_request(req)
        assert result == []


# =============================================================
# save_ai_history_for_request
# =============================================================

class TestSaveAiHistoryForRequest:

    def test_logged_in_saves_to_cache(self):
        """等价类：已登录 → 保存到 cache，session 中不保留。"""
        req = _make_request({"customer_id": 10, "ai_chat_history": [{"old": True}]})
        save_ai_history_for_request(req, [{"role": "user", "content": "新消息"}])
        # cache 中应有数据
        assert get_ai_history(10) == [{"role": "user", "content": "新消息"}]
        # session 中的临时历史应被清除
        assert "ai_chat_history" not in req.session

    def test_not_logged_in_saves_to_session(self):
        """等价类：未登录 → 保存到 session。"""
        req = _make_request({})
        save_ai_history_for_request(req, [{"role": "user", "content": "临时"}])
        assert req.session["ai_chat_history"] == [{"role": "user", "content": "临时"}]
        assert req.session.modified is True


# =============================================================
# clear_ai_history_for_request
# =============================================================

class TestClearAiHistoryForRequest:

    def test_logged_in_clears_cache(self):
        """等价类：已登录 → 清空 cache 中的历史。"""
        save_ai_history(5, [{"role": "user", "content": "要清除"}])
        req = _make_request({"customer_id": 5})
        clear_ai_history_for_request(req)
        assert get_ai_history(5) == []

    def test_not_logged_in_clears_session(self):
        """等价类：未登录 → 清空 session 中的历史。"""
        req = _make_request({"ai_chat_history": [{"role": "user", "content": "临时"}]})
        clear_ai_history_for_request(req)
        assert "ai_chat_history" not in req.session


# =============================================================
# attach_customer_ai_history（登录时合并）
# =============================================================

class TestAttachCustomerAiHistory:

    def test_merge_session_into_cache(self):
        """场景：登录时，session 历史合并进 cache。"""
        # 预置 cache 中有 1 条
        save_ai_history(7, [{"role": "user", "content": "已有"}])
        # session 中有 1 条
        req = _make_request({"ai_chat_history": [{"role": "user", "content": "新增"}]})

        attach_customer_ai_history(req, 7)

        result = get_ai_history(7)
        assert len(result) == 2
        assert result[0]["content"] == "已有"
        assert result[1]["content"] == "新增"
        # session 中的临时历史应被清除
        assert "ai_chat_history" not in req.session

    def test_no_session_history_no_change(self):
        """边界值：session 无历史 → cache 不变。"""
        save_ai_history(8, [{"role": "user", "content": "不变"}])
        req = _make_request({})

        attach_customer_ai_history(req, 8)

        result = get_ai_history(8)
        assert result == [{"role": "user", "content": "不变"}]

    def test_empty_cache_merge(self):
        """边界值：cache 无历史，session 有历史 → 直接存入。"""
        req = _make_request({"ai_chat_history": [{"role": "user", "content": "新的"}]})
        attach_customer_ai_history(req, 9)
        assert get_ai_history(9) == [{"role": "user", "content": "新的"}]
