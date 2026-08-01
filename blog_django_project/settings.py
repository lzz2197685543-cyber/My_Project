"""
Django settings for blog_django_project project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-fp0w=gena+kcx$p$r!c$nayi5#=j&au+q)l3d%7=_&jz0(o1c='

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG 通过环境变量控制
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# ALLOWED_HOSTS = []
# 允许访问的主机名
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blog',  # 注册博客应用
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'blog_django_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'blog_django_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'  # 中文
TIME_ZONE = 'Asia/Shanghai'  # 北京时间
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'

# 认证配置
# 文件路径：blog_django_project/settings.py

# 认证配置 - 修改这几行
LOGIN_URL = 'blog:login'                    # 加上 blog: 命名空间
LOGIN_REDIRECT_URL = 'blog:index'           # 加上 blog: 命名空间
LOGOUT_REDIRECT_URL = 'blog:index'          # 加上 blog: 命名空间

# 安全密钥从环境变量读取（不要硬编码在代码中）
SECRET_KEY = os.environ.get('SECRET_KEY', '开发环境默认密钥')

# 静态文件收集目录
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')   # 项目根目录下的 staticfiles/
STATIC_URL = '/static/'