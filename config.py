# ========== 博客系统配置 ==========

import os

# GitHub 仓库配置
GITHUB_REPO = "https://github.com/mattleeee/quant-blog.git"
GITHUB_USERNAME = "mattleeee"
GITHUB_EMAIL = "77168944@qq.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # 从环境变量读取，避免泄露
# GitHub仓库所有者/仓库名
GITHUB_API_REPO = "mattleeee/quant-blog"

# 域名配置（eu.org审核通过后启用）
DOMAIN = "hkcode.eu.org"
# eu.org审核期间临时使用GitHub Pages域名
TEMP_DOMAIN = "mattleeee.github.io"

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")  # 从环境变量读取
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# PushPlus 推送配置
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")  # 从环境变量读取
PUSHPLUS_URL = "http://www.pushplus.plus/send"

# 掘金平台配置
JUEJIN_COOKIE = os.environ.get("JUEJIN_COOKIE", "")  # 从环境变量读取

# CSDN平台配置
CSDN_COOKIE = os.environ.get("CSDN_COOKIE", "")  # 从环境变量读取

# 博客信息
BLOG_TITLE = "代码与量化"
BLOG_SUBTITLE = "Python量化交易与自动化实战"
BLOG_AUTHOR = "mattleeee"
BLOG_DESCRIPTION = "分享Python量化回测、技术指标实战、自动化运维经验"

# 发布配置
PUBLISH_INTERVAL_MINUTES = 5  # 文章发布最小间隔（模拟人工）
POSTS_PER_DAY = 1  # 每天发布文章数量

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(BASE_DIR, "posts")
PUBLISHED_DIR = os.path.join(BASE_DIR, "published")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

# Git 路径（TeleAgent自带的PortableGit）
GIT_PATH = r"C:\Users\liyaming\.workbuddy\vendor\PortableGit\cmd\git.exe"

# Node.js 路径
NODE_PATH = r"C:\Users\liyaming\.local\share\TeleAgent\runtimes\node\node.exe"
