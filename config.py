# ========== 博客系统配置 ==========

import os

# GitHub 仓库配置
GITHUB_REPO = "https://github.com/mattleeee/quant-blog.git"
GITHUB_USERNAME = "mattleeee"
GITHUB_EMAIL = "77168944@qq.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # 从环境变量读取，避免泄露
# GitHub仓库所有者/仓库名
GITHUB_API_REPO = "mattleeee/quant-blog"

# 域名配置
DOMAIN = "www.hkcode.dpdns.org"  # eu.org审核通过后生效
# 备用GitHub Pages域名
TEMP_DOMAIN = "mattleeee.github.io"

# 站点URL前缀
# 自定义域名时为 ""（根路径），GitHub Pages项目站点时为 "/quant-blog"
SITE_PREFIX = ""  # eu.org审核通过后改为 ""

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")  # 从环境变量读取
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# PushPlus 推送配置
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")  # 从环境变量读取
PUSHPLUS_URL = "https://www.pushplus.plus/send"

# 掘金平台配置
# 优先从本地文件加载（避免bat中%特殊字符被CMD吞掉导致cookie损坏）
def _load_juejin_cookie():
    """加载掘金cookie：优先文件，其次环境变量"""
    import json
    # 1) 文件方式（最可靠，避免CMD % 展开问题）
    cookie_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "juejin_cookie.json")
    if os.path.exists(cookie_file):
        try:
            with open(cookie_file, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                cookie = data.get("cookie", "")
                if cookie:
                    return cookie
        except Exception:
            pass
    # 2) 环境变量方式（兼容直接命令行运行）
    return os.environ.get("JUEJIN_COOKIE", "")

JUEJIN_COOKIE = _load_juejin_cookie()

# CSDN平台配置（优先文件，其次环境变量，避免bat传递问题）
def _load_csdn_cookie():
    """加载CSDN cookie：优先文件，其次环境变量"""
    cookie_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "csdn_cookie.json")
    if os.path.exists(cookie_file):
        try:
            with open(cookie_file, "r", encoding="utf-8-sig") as f:
                import json
                data = json.load(f)
                cookie = data.get("cookie", "")
                if cookie:
                    return cookie
        except Exception:
            pass
    return os.environ.get("CSDN_COOKIE", "")

CSDN_COOKIE = _load_csdn_cookie()

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

# Git 路径（自动探测，兼容不同用户名和安装位置）
def _find_git():
    """自动探测 git.exe 路径"""
    import shutil
    # 1) TeleAgent 自带 PortableGit
    _candidate = os.path.join(os.environ.get("USERPROFILE", ""), ".workbuddy", "vendor", "PortableGit", "cmd", "git.exe")
    if os.path.exists(_candidate):
        return _candidate
    # 2) TeleAgent runtimes 下的 git
    _candidate2 = os.path.join(os.environ.get("USERPROFILE", ""), ".local", "share", "TeleAgent", "runtimes", "git", "cmd", "git.exe")
    if os.path.exists(_candidate2):
        return _candidate2
    # 3) 系统 PATH 中的 git
    _sys_git = shutil.which("git")
    if _sys_git:
        return _sys_git
    # 4) 默认值（兼容旧路径）
    return _candidate

# Node.js 路径（自动探测）
def _find_node():
    """自动探测 node.exe 路径"""
    import shutil
    # 1) TeleAgent 自带 Node
    _candidate = os.path.join(os.environ.get("USERPROFILE", ""), ".local", "share", "TeleAgent", "runtimes", "node", "node.exe")
    if os.path.exists(_candidate):
        return _candidate
    # 2) 系统 PATH 中的 node
    _sys_node = shutil.which("node")
    if _sys_node:
        return _sys_node
    # 3) 默认值
    return _candidate

GIT_PATH = _find_git()

# Node.js 路径
NODE_PATH = _find_node()
