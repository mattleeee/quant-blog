#!/usr/bin/env python3
"""
文章生成器：调用DeepSeek API自动生成博客文章
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from articles_plan import ARTICLES, get_article_by_id, get_unpublished_articles, get_total_count


def generate_article_content(article):
    """调用DeepSeek API生成文章内容"""
    prompt = f"""你是一个Python技术博客作者，博客名是"{config.BLOG_TITLE}"，专注于Python量化交易与自动化实战。

请根据以下主题写一篇技术博客文章：

标题：{article['title']}
分类：{article['category']}
关键词：{', '.join(article['keywords'])}

写作要求：
1. 用Markdown格式输出
2. 中文写作，技术术语保留英文
3. 务实风格，不说空话
4. 必须包含具体的Python代码示例（用```python代码块）
5. 文章结构清晰，有二级和三级标题
6. 字数2000-3000字
7. 代码要可以直接运行或参考使用
8. 不要写"免责声明"或"投资建议"之类的内容
9. 技术方法论为主，不推荐任何具体交易品种
10. 开头直接进入主题，不要寒暄
11. 文章末尾自然过渡到"更多内容请关注本站"

{article['prompt']}
"""

    headers = {
        "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": config.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "你是一个专业的Python技术博客作者，擅长写量化交易和自动化相关的技术文章。写作风格务实、简洁、有代码、有干货。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
        "stream": False
    }

    print(f"正在调用DeepSeek API生成文章: {article['title']}")
    
    try:
        response = requests.post(
            config.DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        print(f"文章生成成功，长度: {len(content)} 字")
        return content
        
    except requests.exceptions.Timeout:
        print("API调用超时")
        return None
    except requests.exceptions.RequestException as e:
        print(f"API调用失败: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"解析API响应失败: {e}")
        return None


def generate_excerpt(content, max_length=150):
    """从文章内容生成摘要"""
    # 去掉markdown标记
    import re
    text = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    text = re.sub(r'#{1,6}\s+', '', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'[#*`>\-]', '', text)
    text = text.strip()[:max_length]
    
    # 截取到最近的句号
    last_period = text.rfind('。')
    if last_period > 50:
        text = text[:last_period + 1]
    
    return text + "..."


def save_article(article, content):
    """保存文章到published目录"""
    # 保存Markdown
    md_path = os.path.join(config.PUBLISHED_DIR, f"{article['id']}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"---\n")
        f.write(f"title: {article['title']}\n")
        f.write(f"date: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"category: {article['category']}\n")
        f.write(f"keywords: {', '.join(article['keywords'])}\n")
        f.write(f"---\n\n")
        f.write(content)
    
    # 更新manifest
    manifest_path = os.path.join(config.PUBLISHED_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = []
    
    # 检查是否已存在
    manifest = [m for m in manifest if m["id"] != article["id"]]
    
    post_info = {
        "id": article["id"],
        "title": article["title"],
        "category": article["category"],
        "keywords": article["keywords"],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "excerpt": generate_excerpt(content),
        "description": generate_excerpt(content, 120)
    }
    
    manifest.append(post_info)
    manifest.sort(key=lambda x: x["id"])
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"文章已保存: {md_path}")
    return post_info


def get_published_ids():
    """获取已发布的文章ID列表"""
    manifest_path = os.path.join(config.PUBLISHED_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return [m["id"] for m in manifest]
    return []


def generate_next_article():
    """生成下一篇文章"""
    published_ids = get_published_ids()
    unpublished = get_unpublished_articles(published_ids)
    
    if not unpublished:
        print("所有文章已发布完毕！")
        return None
    
    print(f"已发布 {len(published_ids)}/{get_total_count()} 篇")
    print(f"待发布 {len(unpublished)} 篇")
    
    # 取下一篇
    next_article = unpublished[0]
    print(f"\n下一篇: [{next_article['id']}] {next_article['title']}")
    
    # 生成内容
    content = generate_article_content(next_article)
    if not content:
        print("文章生成失败！")
        return None
    
    # 保存
    post_info = save_article(next_article, content)
    
    return post_info


if __name__ == "__main__":
    result = generate_next_article()
    if result:
        print(f"\n文章生成完成: {result['title']}")
    else:
        print("\n没有生成文章")
