#!/usr/bin/env python3
"""
CSDN自动发布脚本
通过Cookie + HMAC-SHA256签名方式发布文章到CSDN
CSDN使用阿里云API网关，需要x-ca-key/x-ca-nonce/x-ca-signature签名头
"""

import os
import sys
import json
import hmac
import hashlib
import uuid
import time
import re
import requests
from base64 import b64encode
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# CSDN API网关签名参数
CSDN_API_SAVE = "https://bizapi.csdn.net/blog-console-api/v3/mdeditor/saveArticle"
CA_KEY = "203803574"
HMAC_KEY = "9znpamsyl2c7cdrr9sas0le9vbc3r6ba"


def get_csdn_sign(url, method="POST"):
    """构造CSDN阿里云API网关HMAC-SHA256签名
    
    Args:
        url: 请求URL
        method: HTTP方法（POST/GET）
    
    Returns:
        (nonce, signature): 随机串和签名
    """
    nonce = str(uuid.uuid4())
    s = urlparse(url)
    
    if method == "POST":
        # POST请求签名串不含query string
        to_enc = (
            f"POST\n"
            f"*/*\n"                    # Accept
            f"\n"                       # 空 Content-MD5
            f"application/json\n"       # Content-Type
            f"\n"                       # 空 Date
            f"x-ca-key:{CA_KEY}\n"
            f"x-ca-nonce:{nonce}\n"
            f"{s.path}"                 # POST不含query
        ).encode()
    else:
        # GET请求签名串包含query string
        query_part = f"?{s.query}" if s.query else ""
        to_enc = (
            f"GET\n"
            f"*/*\n\n\n\n"
            f"x-ca-key:{CA_KEY}\n"
            f"x-ca-nonce:{nonce}\n"
            f"{s.path}{query_part}"
        ).encode()
    
    sign = b64encode(
        hmac.new(HMAC_KEY.encode(), to_enc, digestmod=hashlib.sha256).digest()
    ).decode()
    return nonce, sign


def build_headers(cookie_str, url, method="POST"):
    """构建带签名的请求头
    
    Args:
        cookie_str: CSDN cookie字符串
        url: 请求URL
        method: HTTP方法
    
    Returns:
        dict: 完整请求头
    """
    nonce, sign = get_csdn_sign(url, method)
    return {
        "x-ca-key": CA_KEY,
        "x-ca-nonce": nonce,
        "x-ca-signature": sign,
        "x-ca-signature-headers": "x-ca-key,x-ca-nonce",
        "content-type": "application/json",
        "accept": "*/*",
        "origin": "https://mp.csdn.net",
        "referer": "https://mp.csdn.net/",
        "cookie": cookie_str,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }


def check_cookie(cookie_str):
    """探活：空body POST到saveArticle，不真的创建文章
    
    Args:
        cookie_str: CSDN cookie字符串
    
    Returns:
        bool: cookie是否有效
    """
    if not cookie_str:
        return False
    try:
        headers = build_headers(cookie_str, CSDN_API_SAVE, "POST")
        r = requests.post(CSDN_API_SAVE, headers=headers, json={}, timeout=10)
        result = r.json()
        # code=200表示凭证有效，空body不会创建文章
        if result.get("code") == 200:
            print("CSDN cookie探活通过")
            return True
        else:
            print(f"CSDN cookie探活失败: {json.dumps(result, ensure_ascii=False)[:200]}")
            return False
    except Exception as e:
        print(f"CSDN cookie探活异常: {e}")
        return False


def md_to_html(md_content):
    """将Markdown转为HTML（CSDN的content字段需要HTML）
    
    Args:
        md_content: Markdown文本
    
    Returns:
        str: HTML文本
    """
    try:
        import markdown
        # 支持表格、代码块、代码高亮等扩展
        extensions = ['tables', 'fenced_code', 'codehilite', 'toc', 'nl2br']
        html = markdown.markdown(md_content, extensions=extensions)
        return html
    except ImportError:
        # 如果没有markdown库，做简单转换
        print("警告: 未安装markdown库，使用简单HTML转换")
        html = md_content
        # 代码块
        html = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code class="\1">\2</code></pre>', html, flags=re.DOTALL)
        # 行内代码
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        # 粗体
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        # 斜体
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        # 标题
        for i in range(6, 0, -1):
            html = re.sub(r'^#{' + str(i) + r'}\s+(.+)$', f'<h{i}>\\1</h{i}>', html, flags=re.MULTILINE)
        # 段落（简单处理）
        lines = html.split('\n')
        processed = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('<'):
                processed.append(f'<p>{stripped}</p>')
            else:
                processed.append(line)
        return '\n'.join(processed)


def publish_to_csdn(post_info, content):
    """发布文章到CSDN
    
    Args:
        post_info: 文章元数据
        content: markdown内容
    
    Returns:
        article_id: CSDN文章ID，失败返回None
    """
    if not config.CSDN_COOKIE:
        print("CSDN cookie未配置，跳过CSDN发布")
        return None
    
    print(f"正在发布到CSDN: {post_info['title']}")
    
    # 构建摘要（CSDN要求至少50字）
    brief = post_info.get("excerpt", "") or ""
    if not brief:
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith(("#", ">", "```", "-", "|", "!", "[")):
                brief = line[:200]
                break
    if len(brief) < 50:
        brief = brief + "..." + "分享Python量化交易与自动化运维的实战经验，涵盖定时任务、脚本开发和系统管理等内容。"
    
    # 将Markdown转为HTML（CSDN content字段需要HTML）
    html_content = md_to_html(content)
    
    # 构建标签（CSDN格式）
    keywords = post_info.get("keywords", ["Python"])
    if isinstance(keywords, list):
        tags_str = ",".join(keywords[:3])
    else:
        tags_str = str(keywords)
    
    # CSDN发布参数（v3 mdeditor接口）
    payload = {
        "title": post_info["title"],
        "markdowncontent": content,          # Markdown原始内容
        "content": html_content,             # HTML内容（CSDN要求）
        "description": brief[:200],
        "categories": "Python",
        "tags": tags_str,
        "type": "original",                  # 原创
        "art_type": 1,
        "is_top": 0,
        "authorized_status": 0,
        "resource_id": "",
        "read_type": "public",
        "status": 0,                         # 0=草稿，1=发布
        "source": "pc_mdeditor",
        "pubStatus": "publish",
    }
    
    try:
        # 先探活检查cookie
        if not check_cookie(config.CSDN_COOKIE):
            print("CSDN cookie已失效，请更新cookie")
            return None
        
        # 保存并发布（saveArticle接口直接发布）
        headers = build_headers(config.CSDN_COOKIE, CSDN_API_SAVE, "POST")
        response = requests.post(CSDN_API_SAVE, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        if result.get("code") != 200:
            error_msg = result.get("msg", result.get("message", "未知错误"))
            print(f"CSDN发布失败: {error_msg}")
            print(f"响应详情: {json.dumps(result, ensure_ascii=False)[:300]}")
            return None
        
        # v3接口返回 data.id 或 data.articleId
        article_id = result.get("data", {}).get("id") or result.get("data", {}).get("articleId")
        article_url = result.get("data", {}).get("url", "")
        if not article_id:
            print(f"CSDN返回数据异常: {json.dumps(result, ensure_ascii=False)[:300]}")
            return None
        
        print(f"CSDN发布成功! article_id={article_id}")
        if article_url:
            print(f"访问地址: {article_url}")
        else:
            print(f"访问地址: https://blog.csdn.net/m0_74899575/article/details/{article_id}")
        return article_id
            
    except requests.exceptions.RequestException as e:
        print(f"CSDN发布网络异常: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"CSDN发布解析异常: {e}")
        return None


if __name__ == "__main__":
    # 测试
    if len(sys.argv) > 1:
        article_id = int(sys.argv[1])
        from articles_plan import get_article_by_id
        
        article = get_article_by_id(article_id)
        if article:
            md_path = os.path.join(config.PUBLISHED_DIR, f"{article_id}.md")
            if os.path.exists(md_path):
                with open(md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # 去掉front matter
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        content = content[end+3:].strip()
                publish_to_csdn(article, content)
            else:
                print(f"文章文件不存在: {md_path}")
        else:
            print(f"文章不存在: {article_id}")
    else:
        print("用法: python csdn_publisher.py <article_id>")
        print("示例: python csdn_publisher.py 1")
