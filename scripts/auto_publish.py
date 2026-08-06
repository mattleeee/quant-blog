#!/usr/bin/env python3
"""
自动发布调度脚本 - 每天自动生成文章并发布
这个脚本由Windows计划任务定时调用

流程：
1. 调用generate_article.py生成下一篇文章
2. 调用publish.py发布到GitHub Pages
3. 如果配置了cookie，同步发布到掘金
4. 推送微信通知
"""

import os
import sys
import json
import subprocess
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def log(msg):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    
    # 同时写入日志文件
    log_file = os.path.join(config.LOGS_DIR, f"auto_publish_{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")


def run_script(script_name):
    """运行脚本"""
    script_path = os.path.join(config.SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        log(f"脚本不存在: {script_path}")
        return False
    
    log(f"运行脚本: {script_name}")
    
    # 设置环境变量
    env = os.environ.copy()
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    env["OMP_NUM_THREADS"] = "1"
    
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env,
        cwd=config.BASE_DIR
    )
    
    if result.stdout:
        log(result.stdout)
    if result.stderr:
        log(f"STDERR: {result.stderr}")
    
    return result.returncode == 0


def get_latest_post():
    """获取最新发布的文章信息"""
    manifest_path = os.path.join(config.PUBLISHED_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return manifest[-1] if manifest else None
    return None


def get_post_content(post_id):
    """获取文章内容"""
    md_path = os.path.join(config.PUBLISHED_DIR, f"{post_id}.md")
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 去掉front matter
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                content = content[end+3:].strip()
        return content
    return None


def main():
    log("=" * 60)
    log("自动发布调度开始")
    log("=" * 60)
    
    # 第一步：生成文章
    log(">>> 第一步：生成文章")
    gen_script = os.path.join(config.SCRIPTS_DIR, "generate_article.py")
    
    # 设置环境变量
    env = os.environ.copy()
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    env["OMP_NUM_THREADS"] = "1"
    
    result = subprocess.run(
        [sys.executable, gen_script],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env,
        cwd=config.BASE_DIR
    )
    
    if result.stdout:
        log(result.stdout)
    if result.stderr:
        log(f"STDERR: {result.stderr}")
    
    if result.returncode != 0:
        log("文章生成失败！")
        send_error_notification("文章生成失败")
        return
    
    # 检查是否有新文章
    latest_post = get_latest_post()
    if not latest_post:
        log("没有找到文章")
        return
    
    # 如果文章日期是今天，说明是新文章
    today = datetime.now().strftime("%Y-%m-%d")
    if latest_post.get("date") != today:
        log("今日文章未生成或所有文章已发布")
        return
    
    log(f"新文章已生成: {latest_post['title']}")
    
    # 第二步：发布到GitHub
    log(">>> 第二步：发布到GitHub Pages")
    pub_result = run_script("publish.py")
    
    if not pub_result:
        log("GitHub发布失败")
        send_error_notification("GitHub发布失败")
        return
    
    # 第三步：同步到掘金（如果配置了cookie）
    if config.JUEJIN_COOKIE:
        log(">>> 第三步：同步到掘金")
        from juejin_publisher import publish_to_juejin
        content = get_post_content(latest_post["id"])
        if content:
            juejin_id = publish_to_juejin(latest_post, content)
            if juejin_id:
                log(f"掘金发布成功: https://juejin.cn/post/{juejin_id}")
            else:
                log("掘金发布失败，但博客已发布")
    else:
        log(">>> 第三步：跳过掘金（未配置cookie）")
    
    # 第四步：同步到CSDN（如果配置了cookie）
    if config.CSDN_COOKIE:
        log(">>> 第四步：同步到CSDN")
        from csdn_publisher import publish_to_csdn
        content = get_post_content(latest_post["id"])
        if content:
            csdn_id = publish_to_csdn(latest_post, content)
            if csdn_id:
                log(f"CSDN发布成功: https://blog.csdn.net/m0_74899575/article/details/{csdn_id}")
            else:
                log("CSDN发布失败，但博客已发布")
    else:
        log(">>> 第四步：跳过CSDN（未配置cookie）")
    
    log("=" * 60)
    log("自动发布完成")
    log("=" * 60)


def send_error_notification(error_msg):
    """发送错误通知"""
    if not config.PUSHPLUS_TOKEN:
        return
    
    import requests
    payload = {
        "token": config.PUSHPLUS_TOKEN,
        "title": f"星辰智能体推送|博客发布异常",
        "content": f"错误信息: {error_msg}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "template": "markdown"
    }
    try:
        requests.post(config.PUSHPLUS_URL, json=payload, timeout=30)
    except Exception:
        pass


if __name__ == "__main__":
    main()
