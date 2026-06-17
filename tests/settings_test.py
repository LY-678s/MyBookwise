"""
测试专用 Django settings：
- 用 SQLite 内存库替代 MySQL，避免污染真库、加快测试速度
- 禁用 bookstore 的 migrations（项目原本就没有；测试时靠 --run-syncdb 自动建表）
- 关闭不必要的中间件与密码哈希加速测试
"""
from MyBookwise.settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

MIGRATION_MODULES = {
    "bookstore": None,
    "admin": None,
    "auth": None,
    "contenttypes": None,
    "sessions": None,
    "messages": None,
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

DEBUG = False
TEMPLATE_DEBUG = False
LOGGING_CONFIG = None

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# AI 测试用占位配置
AI_PROVIDER = "deepseek"
DEEPSEEK_API_KEY = "test-key"
GEMINI_API_KEY = "test-key"