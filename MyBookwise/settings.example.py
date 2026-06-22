"""
Django settings 示例文件。

使用方法：
1. 复制本文件为 settings.py：  cp MyBookwise/settings.example.py MyBookwise/settings.py
2. 修改数据库密码等本地配置
3. 在 https://platform.deepseek.com/ 申请 DeepSeek API Key，填入 DEEPSEEK_API_KEY
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-emrbeuu1kr_*)z5@y43v5bh19o4zy-k@vc-j340de-6we$w)&k"

DEBUG = True

# 本机 + 局域网 + 内网穿透域名（见 README「跨网访问」）
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".trycloudflare.com",  # cloudflared 快速隧道（推荐，免注册）
    ".ngrok-free.app",     # ngrok 免费域名（可选）
]

# Web 端经 HTTPS 隧道访问时需配置，否则登录/表单会 CSRF 失败
# PowerShell 示例：$env:TUNNEL_ORIGIN = "https://xxxx.trycloudflare.com"
_tunnel_origin = os.environ.get("TUNNEL_ORIGIN", "").strip().rstrip("/")
CSRF_TRUSTED_ORIGINS = [_tunnel_origin] if _tunnel_origin else []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "bookstore.apps.BookstoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "MyBookwise.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "bookstore.context_processors.current_customer",
            ],
        },
    },
]

WSGI_APPLICATION = "MyBookwise.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "bookstoredb",
        "USER": "root",
        "PASSWORD": "your_mysql_password",
        "HOST": "localhost",
        "PORT": "3306",
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = False

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------- 图书封面配置（可选）----------
COVER_IMAGE_SUBDIR = "images"
DEFAULT_COVER_IMAGE_FILENAME = "Python编程从入门到实践.jpg"
COVER_IMAGE_MAPPINGS = {
    "python": "Python编程从入门到实践.jpg",
    "机器学习": "机器学习实战.jpg",
    "深入理解计算机": "深入理解计算机系统.jpg",
    "数据库": "数据库系统概念.png",
    "算法导论": "算法导论.png",
}

# ---------- AI 聊天配置（硅基流动 SiliconFlow）----------
# 免费申请 API Key：https://cloud.siliconflow.cn/account/ak
AI_PROVIDER = "deepseek"  # 复用 deepseek 通道，硅基流动接口格式相同

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")  # 在此填入你自己的硅基流动 API Key
DEEPSEEK_MODEL = "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"  # 免费模型
DEEPSEEK_API_BASE = "https://api.siliconflow.cn/v1"

# Gemini（备用）
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

AI_REQUEST_TIMEOUT = 60
