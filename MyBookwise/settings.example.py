from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: list[str]) -> list[str]:
    value = os.environ.get(name, "")
    if not value.strip():
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-emrbeuu1kr_*)z5@y43v5bh19o4zy-k@vc-j340de-6we$w)&k",
)

DEBUG = _env_bool("DJANGO_DEBUG", True)

_DEFAULT_ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "mybookwise.xyz",
    "www.mybookwise.xyz",
    "ly.mybookwise.xyz",
    ".trycloudflare.com",
    ".ngrok-free.app",
]
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", _DEFAULT_ALLOWED_HOSTS)

_PUBLIC_ORIGINS = [
    "https://mybookwise.xyz",
    "https://www.mybookwise.xyz",
    "https://ly.mybookwise.xyz",
]
_tunnel_origin = os.environ.get("TUNNEL_ORIGIN", "").strip().rstrip("/")
_default_csrf_origins = _PUBLIC_ORIGINS + (
    [_tunnel_origin] if _tunnel_origin and _tunnel_origin not in _PUBLIC_ORIGINS else []
)
CSRF_TRUSTED_ORIGINS = _env_list("DJANGO_CSRF_TRUSTED_ORIGINS", _default_csrf_origins)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
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
        "NAME": os.environ.get("MYSQL_DATABASE", "bookstoredb"),
        "USER": os.environ.get("MYSQL_USER", "root"),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD", "your_mysql_password"),
        "HOST": os.environ.get("MYSQL_HOST", "localhost"),
        "PORT": os.environ.get("MYSQL_PORT", "3306"),
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

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------- REST API（Android APP Token 认证）----------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "bookstore.api.authentication.CustomerTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [],
}

# ---------- 图书封面配置（可选）----------
COVER_IMAGE_SUBDIR = "images"
DEFAULT_COVER_IMAGE_FILENAME = "default_cover.png"
DEFAULT_COVER_IMAGE_FILENAME = "default_cover.png"
COVER_IMAGE_MAPPINGS = {
    "python": "default_cover.png",
    "机器学习": "default_cover.png",
    "深入理解计算机": "default_cover.png",
    "数据库": "default_cover.png",
    "算法导论": "default_cover.png",
}

AI_PROVIDER = "deepseek"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
# 硅基流动 OpenAI 兼容接口（有免费额度；密钥：https://cloud.siliconflow.cn）
DEEPSEEK_MODEL = "deepseek-ai/DeepSeek-V3"
DEEPSEEK_API_BASE = "https://api.siliconflow.cn/v1"
# 官方 DeepSeek（付费）：DEEPSEEK_MODEL = "deepseek-chat"  DEEPSEEK_API_BASE = "https://api.deepseek.com"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

AI_REQUEST_TIMEOUT = 60

# ---------- Stripe Test Mode（会员支付）----------
#
# 【在哪填】https://dashboard.stripe.com/test/apikeys （Test mode / 沙盒）
#   STRIPE_SECRET_KEY      ← sk_test_... 私钥
#   STRIPE_PUBLISHABLE_KEY ← pk_test_... 公钥
#   STRIPE_WEBHOOK_SECRET  ← 可选 whsec_...
#
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_MEMBERSHIP_AMOUNT_CENTS = 2999
SITE_URL = os.environ.get("SITE_URL", "https://mybookwise.xyz")
