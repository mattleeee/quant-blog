#!/usr/bin/env python3
"""
掘金自动发布脚本
通过模拟登录cookie发布文章到掘金
"""

import os
import sys
import json
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


JUEJIN_API_PUBLISH = "https://api.juejin.cn/content_api/v1/article/publish"
JUEJIN_API_DRAFT = "https://api.juejin.cn/content_api/v1/article/draft_create"
JUEJIN_API_UPDATE = "https://api.juejin.cn/content_api/v1/article/draft_update"


def get_headers():
    """获取请求头"""
    if not config.JUEJIN_COOKIE:
        print("掘金cookie未配置，跳过掘金发布")
        return None
    
    return {
        "Cookie": config.JUEJIN_COOKIE,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://juejin.cn/editor/drafts/new",
        "Origin": "https://juejin.cn",
    }


def publish_to_juejin(post_info, content):
    """发布文章到掘金
    
    Args:
        post_info: 文章元数据
        content: markdown内容
    
    Returns:
        article_id: 掘金文章ID，失败返回None
    """
    headers = get_headers()
    if not headers:
        return None
    
    print(f"正在发布到掘金: {post_info['title']}")
    
    # 构建请求数据
    # 掘金要求把markdown转为特定格式
    brief = post_info.get("excerpt", "")[:100] if post_info.get("excerpt") else ""
    
    payload = {
        "title": post_info["title"],
        "content": content,
        "brief_content": brief,
        "category_id": "6809637767543259144",  # 后端分类
        "tag_ids": get_tag_ids(post_info.get("keywords", [])),
        "cover_image": "",
        "edit_type": 10,  # markdown
        "theme_id": "",
        "draft_type": 1,
    }
    
    try:
        # 先创建草稿
        response = requests.post(JUEJIN_API_DRAFT, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        if result.get("err_no") != 0:
            print(f"创建草稿失败: {result.get('err_msg', '未知错误')}")
            return None
        
        draft_id = result["data"]["article"]["draft_id"]
        article_id = result["data"]["article"]["article_id"]
        print(f"草稿创建成功: draft_id={draft_id}")
        
        # 发布
        publish_payload = {
            "draft_id": draft_id,
            "sync_to_org": False,
        }
        
        response = requests.post(JUEJIN_API_PUBLISH, headers=headers, json=publish_payload, timeout=30)
        result = response.json()
        
        if result.get("err_no") == 0:
            article_id = result["data"]["article_id"]
            print(f"掘金发布成功! article_id={article_id}")
            print(f"访问地址: https://juejin.cn/post/{article_id}")
            return article_id
        else:
            print(f"发布失败: {result.get('err_msg', '未知错误')}")
            print(f"草稿已保存，可手动发布: https://juejin.cn/editor/drafts/{draft_id}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"掘金发布网络异常: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"掘金发布解析异常: {e}")
        return None


def get_tag_ids(keywords):
    """根据关键词获取掘金标签ID
    
    掘金标签需要使用预定义的标签ID
    这里做一个简单的关键词到标签ID的映射
    """
    # 掘金常用标签ID映射
    tag_map = {
        "python": "6809637773945442317",
        "Python": "6809637773945442317",
        "自动化": "6809637769494158350",
        "量化": "6809637771516833800",
        "量化交易": "6809637771516833800",
        "定时任务": "6809637769494158350",
        "windows": "6809637773945442317",
        "Windows": "6809637773945442317",
        "SQLite": "6809637773945442317",
        "API": "6809637773945442317",
        "后端": "6809637773945442317",
    }
    
    tag_ids = []
    for kw in keywords:
        if kw in tag_map and tag_map[kw] not in tag_ids:
            tag_ids.append(tag_map[kw])
    
    # 默认标签：Python
    if not tag_ids:
        tag_ids.append("6809637773945442317")
    
    # 掘金最多3个标签
    return tag_ids[:3]


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
                publish_to_juejin(article, content)
            else:
                print(f"文章文件不存在: {md_path}")
        else:
            print(f"文章不存在: {article_id}")
    else:
        print("用法: python juejin_publisher.py <article_id>")
