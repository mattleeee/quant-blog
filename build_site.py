#!/usr/bin/env python3
"""
博客静态站点生成器
将posts目录下的markdown文章生成静态HTML页面
"""

import os
import markdown
import json
from datetime import datetime
from html import escape
import config


def load_posts():
    """加载所有已发布文章的元数据"""
    manifest_path = os.path.join(config.PUBLISHED_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def render_markdown(md_text):
    """将markdown转换为HTML"""
    md = markdown.Markdown(extensions=["codehilite", "fenced_code", "tables", "toc"])
    return md.convert(md_text)


def generate_article_html(post, content_html):
    """生成单篇文章HTML"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(post['title'])} - {config.BLOG_TITLE}</title>
    <meta name="description" content="{escape(post.get('description', post['title']))}">
    <meta name="keywords" content="{escape(','.join(post.get('keywords', [])))}">
    <meta name="author" content="{config.BLOG_AUTHOR}">
    <meta property="og:title" content="{escape(post['title'])}">
    <meta property="og:description" content="{escape(post.get('description', ''))}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="{config.BLOG_TITLE}">
    <link rel="stylesheet" href="/css/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11/styles/github-dark.min.css">
</head>
<body>
    <header>
        <nav>
            <a href="/" class="logo">{config.BLOG_TITLE}</a>
            <div class="nav-links">
                <a href="/">首页</a>
                <a href="/categories.html">分类</a>
                <a href="/about.html">关于</a>
            </div>
        </nav>
    </header>
    <main>
        <article class="post">
            <h1>{escape(post['title'])}</h1>
            <div class="post-meta">
                <span class="date">{post.get('date', '')}</span>
                <span class="category">分类: <a href="/category/{post.get('category', '')}.html">{post.get('category', '')}</a></span>
            </div>
            <div class="post-content">
                {content_html}
            </div>
            <div class="post-footer">
                <p>本文首发于 <a href="https://{config.DOMAIN}">{config.BLOG_TITLE}</a></p>
                <p>更多内容请关注: <a href="https://github.com/{config.GITHUB_USERNAME}">GitHub</a></p>
            </div>
        </article>
    </main>
    <footer>
        <p>&copy; {datetime.now().year} {config.BLOG_TITLE}. All rights reserved.</p>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/highlight.js@11/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>
</body>
</html>"""
    return html


def generate_index_html(posts):
    """生成首页"""
    posts_sorted = sorted(posts, key=lambda x: x.get("date", ""), reverse=True)
    
    post_list_html = ""
    for post in posts_sorted:
        post_list_html += f"""
        <article class="post-card">
            <h2><a href="/posts/{post['id']}.html">{escape(post['title'])}</a></h2>
            <div class="post-meta">
                <span class="date">{post.get('date', '')}</span>
                <span class="category">{post.get('category', '')}</span>
            </div>
            <p class="excerpt">{escape(post.get('excerpt', ''))}</p>
            <a href="/posts/{post['id']}.html" class="read-more">阅读更多 →</a>
        </article>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.BLOG_TITLE} - {config.BLOG_SUBTITLE}</title>
    <meta name="description" content="{config.BLOG_DESCRIPTION}">
    <meta name="keywords" content="Python,量化交易,自动化,技术指标,回测">
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header>
        <nav>
            <a href="/" class="logo">{config.BLOG_TITLE}</a>
            <div class="nav-links">
                <a href="/">首页</a>
                <a href="/categories.html">分类</a>
                <a href="/about.html">关于</a>
            </div>
        </nav>
    </header>
    <main>
        <section class="hero">
            <h1>{config.BLOG_TITLE}</h1>
            <p>{config.BLOG_SUBTITLE}</p>
        </section>
        <section class="post-list">
            <h2>最新文章</h2>
            {post_list_html}
        </section>
    </main>
    <footer>
        <p>&copy; {datetime.now().year} {config.BLOG_TITLE}. All rights reserved.</p>
    </footer>
</body>
</html>"""
    return html


def generate_categories_html(posts):
    """生成分类页"""
    categories = {}
    for post in posts:
        cat = post.get("category", "未分类")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(post)

    cat_html = ""
    for cat, cat_posts in sorted(categories.items()):
        cat_html += f"""
        <div class="category-section">
            <h2>{escape(cat)} ({len(cat_posts)}篇)</h2>
            <ul>"""
        for post in sorted(cat_posts, key=lambda x: x.get("date", ""), reverse=True):
            cat_html += f'\n                <li><a href="/posts/{post["id"]}.html">{escape(post["title"])}</a> <span>{post.get("date", "")}</span></li>'
        cat_html += "\n            </ul>\n        </div>"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>分类 - {config.BLOG_TITLE}</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header>
        <nav>
            <a href="/" class="logo">{config.BLOG_TITLE}</a>
            <div class="nav-links">
                <a href="/">首页</a>
                <a href="/categories.html">分类</a>
                <a href="/about.html">关于</a>
            </div>
        </nav>
    </header>
    <main>
        <h1>文章分类</h1>
        {cat_html}
    </main>
    <footer>
        <p>&copy; {datetime.now().year} {config.BLOG_TITLE}. All rights reserved.</p>
    </footer>
</body>
</html>"""
    return html


def generate_about_html():
    """生成关于页"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>关于 - {config.BLOG_TITLE}</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header>
        <nav>
            <a href="/" class="logo">{config.BLOG_TITLE}</a>
            <div class="nav-links">
                <a href="/">首页</a>
                <a href="/categories.html">分类</a>
                <a href="/about.html">关于</a>
            </div>
        </nav>
    </header>
    <main>
        <article class="post">
            <h1>关于本站</h1>
            <div class="post-content">
                <p>{config.BLOG_DESCRIPTION}</p>
                <h2>作者简介</h2>
                <p>Python开发者，专注于量化交易系统开发与自动化运维。</p>
                <h2>技术栈</h2>
                <ul>
                    <li>Python 量化回测与策略开发</li>
                    <li>Windows 定时任务自动化</li>
                    <li>技术指标实战（均线、RSI、MACD）</li>
                    <li>系统架构设计与运维</li>
                </ul>
                <h2>联系方式</h2>
                <p>GitHub: <a href="https://github.com/{config.GITHUB_USERNAME}">@{config.GITHUB_USERNAME}</a></p>
            </div>
        </article>
    </main>
    <footer>
        <p>&copy; {datetime.now().year} {config.BLOG_TITLE}. All rights reserved.</p>
    </footer>
</body>
</html>"""
    return html


def generate_sitemap(posts):
    """生成sitemap.xml"""
    urls = [f"\n  <url>\n    <loc>https://{config.DOMAIN}/</loc>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>"]
    for post in posts:
        urls.append(f'\n  <url>\n    <loc>https://{config.DOMAIN}/posts/{post["id"]}.html</loc>\n    <lastmod>{post.get("date", "")}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>')
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{''.join(urls)}
</urlset>"""
    return xml


def generate_rss(posts):
    """生成RSS"""
    items = ""
    for post in sorted(posts, key=lambda x: x.get("date", ""), reverse=True)[:20]:
        items += f"""
        <item>
            <title>{escape(post['title'])}</title>
            <link>https://{config.DOMAIN}/posts/{post['id']}.html</link>
            <description>{escape(post.get('excerpt', ''))}</description>
            <pubDate>{post.get('date', '')}</pubDate>
            <category>{escape(post.get('category', ''))}</category>
        </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>{config.BLOG_TITLE}</title>
        <link>https://{config.DOMAIN}</link>
        <description>{config.BLOG_DESCRIPTION}</description>
        <language>zh-CN</language>
        {items}
    </channel>
</rss>"""
    return rss


def build_site(output_dir=None):
    """构建整个站点"""
    if output_dir is None:
        output_dir = os.path.join(config.BASE_DIR, "docs")
    
    # 创建输出目录
    posts_output = os.path.join(output_dir, "posts")
    css_output = os.path.join(output_dir, "css")
    os.makedirs(posts_output, exist_ok=True)
    os.makedirs(css_output, exist_ok=True)

    # 加载已发布文章
    posts = load_posts()
    
    print(f"已加载 {len(posts)} 篇文章")

    # 生成每篇文章
    for post in posts:
        md_path = os.path.join(config.PUBLISHED_DIR, f"{post['id']}.md")
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
            content_html = render_markdown(md_content)
            article_html = generate_article_html(post, content_html)
            output_path = os.path.join(posts_output, f"{post['id']}.html")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(article_html)
            print(f"  生成文章: {post['title']}")

    # 生成首页
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(generate_index_html(posts))
    print("  生成首页")

    # 生成分类页
    with open(os.path.join(output_dir, "categories.html"), "w", encoding="utf-8") as f:
        f.write(generate_categories_html(posts))
    print("  生成分类页")

    # 生成关于页
    with open(os.path.join(output_dir, "about.html"), "w", encoding="utf-8") as f:
        f.write(generate_about_html())
    print("  生成关于页")

    # 生成sitemap
    with open(os.path.join(output_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(generate_sitemap(posts))
    print("  生成sitemap.xml")

    # 生成RSS
    with open(os.path.join(output_dir, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(generate_rss(posts))
    print("  生成rss.xml")

    # 复制CSS
    import shutil
    css_src = os.path.join(config.STATIC_DIR, "css", "style.css")
    if os.path.exists(css_src):
        shutil.copy(css_src, os.path.join(css_output, "style.css"))

    # 生成CNAME文件（自定义域名）
    cname_path = os.path.join(output_dir, "CNAME")
    with open(cname_path, "w", encoding="utf-8") as f:
        f.write(config.DOMAIN)
    print("  生成CNAME")

    print(f"\n站点构建完成，输出目录: {output_dir}")
    print(f"共 {len(posts)} 篇文章")


if __name__ == "__main__":
    build_site()
