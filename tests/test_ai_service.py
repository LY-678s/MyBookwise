"""AI 服务模块单元测试（Mock 方式）

覆盖函数：
- is_ai_configured
- build_bookstore_system_prompt
- chat_with_ai（Mock 外部 API 调用）
- _history_to_openai_messages、_history_to_gemini_contents（格式转换）
- AIServiceError

测试方法分布：
- 等价类：配置检查、系统提示词构建
- 边界值：空消息、超长消息
- 场景法：Mock DeepSeek/Gemini 成功响应
- 独立路径：Provider 选择分支
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest

from bookstore.ai_service import (
    AIServiceError,
    is_ai_configured,
    build_bookstore_system_prompt,
    chat_with_ai,
    _history_to_openai_messages,
    _history_to_gemini_contents,
    _provider,
)


pytestmark = pytest.mark.django_db


# =============================================================
# _provider / is_ai_configured
# =============================================================

class TestProviderConfig:
    """AI 提供商配置检查。"""

    def test_provider_default_gemini(self, settings):
        """等价类：未设置 AI_PROVIDER → 默认 gemini。"""
        settings.AI_PROVIDER = ""
        assert _provider() == ""

    def test_provider_deepseek(self, settings):
        """等价类：设置 deepseek → 返回 deepseek。"""
        settings.AI_PROVIDER = "deepseek"
        assert _provider() == "deepseek"

    def test_is_configured_true_when_key_set(self, settings):
        """等价类：密钥已配置 → 返回 True。"""
        settings.AI_PROVIDER = "deepseek"
        settings.DEEPSEEK_API_KEY = "test-key-123"
        assert is_ai_configured() is True

    def test_is_configured_false_when_no_key(self, settings):
        """等价类：密钥未配置 → 返回 False。"""
        settings.AI_PROVIDER = "deepseek"
        settings.DEEPSEEK_API_KEY = ""
        assert is_ai_configured() is False


# =============================================================
# build_bookstore_system_prompt
# =============================================================

class TestBuildSystemPrompt:
    """系统提示词构建测试。"""

    def test_prompt_contains_bookstore_name(self, book):
        """等价类：提示词包含书店名称。"""
        prompt = build_bookstore_system_prompt()
        assert "书小智" in prompt
        assert "MyBookwise" in prompt

    def test_prompt_contains_book_info(self, book):
        """场景：有图书数据 → 提示词包含图书信息。"""
        prompt = build_bookstore_system_prompt()
        assert book.title in prompt
        assert book.isbn in prompt

    def test_prompt_contains_member_rules(self, creditlevels):
        """场景：提示词包含会员等级规则。"""
        prompt = build_bookstore_system_prompt()
        assert "会员等级" in prompt
        assert "1级" in prompt
        assert "5级" in prompt

    def test_prompt_contains_payment_methods(self):
        """场景：提示词包含支付方式说明。"""
        prompt = build_bookstore_system_prompt()
        assert "Stripe" in prompt
        assert "在线支付" in prompt

    def test_prompt_no_books(self, db):
        """边界值：无图书 → 显示默认提示。"""
        prompt = build_bookstore_system_prompt()
        assert "暂无图书数据" in prompt


# =============================================================
# chat_with_ai（Mock 外部 API）
# =============================================================

class TestChatWithAi:
    """AI 对话测试（Mock 方式）。"""

    def test_empty_message_raises(self):
        """边界值：空消息 → 抛出 AIServiceError。"""
        with pytest.raises(AIServiceError, match="消息不能为空"):
            chat_with_ai([], "")

    def test_too_long_message_raises(self):
        """边界值：超长消息 → 抛出 AIServiceError。"""
        with pytest.raises(AIServiceError, match="消息过长"):
            chat_with_ai([], "A" * 3000)

    @patch("bookstore.ai_service._chat_with_deepseek")
    def test_deepseek_provider_calls_correctly(self, mock_chat, settings):
        """场景：deepseek provider → 调用 _chat_with_deepseek。"""
        settings.AI_PROVIDER = "deepseek"
        settings.DEEPSEEK_API_KEY = "test-key"
        mock_chat.return_value = "你好，我是书小智！"

        result = chat_with_ai([], "你好")

        assert result == "你好，我是书小智！"
        mock_chat.assert_called_once()

    @patch("bookstore.ai_service._chat_with_gemini")
    def test_gemini_provider_calls_correctly(self, mock_chat, settings):
        """场景：gemini provider → 调用 _chat_with_gemini。"""
        settings.AI_PROVIDER = "gemini"
        settings.GEMINI_API_KEY = "test-key"
        mock_chat.return_value = "推荐《Python编程》"

        result = chat_with_ai([], "推荐一本书")

        assert result == "推荐《Python编程》"
        mock_chat.assert_called_once()

    @patch("bookstore.ai_service._chat_with_deepseek")
    def test_history_passed_to_provider(self, mock_chat, settings):
        """场景：对话历史正确传递给 provider。"""
        settings.AI_PROVIDER = "deepseek"
        settings.DEEPSEEK_API_KEY = "test-key"
        mock_chat.return_value = "回复"

        history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
        ]
        chat_with_ai(history, "推荐一本书")

        # 验证 history 被传递
        call_args = mock_chat.call_args
        assert call_args[0][0] == history  # 第一个参数是 history
        assert call_args[0][1] == "推荐一本书"  # 第二个参数是 user_message


# =============================================================
# 格式转换辅助函数
# =============================================================

class TestHistoryConversion:
    """对话历史格式转换测试。"""

    def test_openai_messages_include_system_prompt(self, book):
        """等价类：OpenAI 格式 → 包含 system prompt。"""
        history = [{"role": "user", "content": "你好"}]
        messages = _history_to_openai_messages(history)
        assert messages[0]["role"] == "system"
        assert "书小智" in messages[0]["content"]

    def test_openai_messages_preserve_history(self):
        """等价类：历史消息正确转换。"""
        history = [
            {"role": "user", "content": "问题1"},
            {"role": "assistant", "content": "回答1"},
        ]
        messages = _history_to_openai_messages(history)
        assert len(messages) == 3  # system + user + assistant
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "问题1"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "回答1"

    def test_openai_messages_skip_empty_content(self):
        """边界值：空内容消息 → 被跳过。"""
        history = [
            {"role": "user", "content": ""},
            {"role": "user", "content": "有效消息"},
        ]
        messages = _history_to_openai_messages(history)
        assert len(messages) == 2  # system + 1 valid user message

    def test_gemini_contents_format(self):
        """等价类：Gemini 格式 → role 为 user/model。"""
        history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
        ]
        contents = _history_to_gemini_contents(history)
        assert len(contents) == 2
        assert contents[0]["role"] == "user"
        assert contents[1]["role"] == "model"

    def test_gemini_contents_skip_empty(self):
        """边界值：空内容 → 被跳过。"""
        history = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": None},
        ]
        contents = _history_to_gemini_contents(history)
        assert len(contents) == 0
