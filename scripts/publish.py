#!/usr/bin/env python3
"""
发布脚本：构建站点 + 推送到GitHub + 推送通知
优先使用GitHub API推送（绕过git DNS/网络问题），fallback到git push
"""

import os
import sys
import json
import base64
import subprocess
import requests
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def run_command(cmd, cwd=None, check=True):
    """运行命令并打印输出"""
    print(f">>> {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True,
        encoding='utf-8', errors='replace'
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if check and result.returncode != 0:
        print(f"命令执行失败，退出码: {result.returncode}")
    return result


def build_site():
    """构建静态站点"""
    print("\n========== 构建站点 ==========")
    base_dir = config.BASE_DIR
    result = run_command(
        f'python "{os.path.join(base_dir, "build_site.py")}"',
        cwd=base_dir
    )
    return result.returncode == 0


# ========== GitHub API 推送 ==========

GITHUB_API = "https://api.github.com"

def _gh_headers(token):
    return {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {token}",
    }

def _get_file_sha(token, path):
    """获取远端文件的SHA（存在则返回，不存在返回None）"""
    url = f"{GITHUB_API}/repos/{config.GITHUB_API_REPO}/contents/{path}"
    try:
        r = requests.get(url, headers=_gh_headers(token), timeout=15)
        if r.status_code == 200:
            return r.json().get("sha")
    except Exception:
        pass
    return None

def _push_one_file(token, local_path, repo_path, commit_msg, sha=None):
    """通过API推送单个文件"""
    try:
        with open(local_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("ascii")
    except Exception as e:
        print(f"  读取失败: {repo_path} - {e}")
        return False

    url = f"{GITHUB_API}/repos/{config.GITHUB_API_REPO}/contents/{repo_path}"
    data = {"message": commit_msg, "content": content_b64}
    if sha:
        data["sha"] = sha

    try:
        r = requests.put(url, headers=_gh_headers(token), json=data, timeout=30)
        if r.status_code in (200, 201):
            print(f"  OK: {repo_path}")
            return True
        else:
            print(f"  FAIL: {repo_path} - {r.status_code} {r.text[:150]}")
            return False
    except Exception as e:
        print(f"  异常: {repo_path} - {e}")
        return False


def github_api_push(token=None):
    """通过GitHub API推送docs目录下的所有文件"""
    if token is None:
        token = config.GITHUB_TOKEN
    if not token:
        return False

    print("\n========== 通过GitHub API推送 ==========")
    commit_msg = f"发布文章 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    docs_dir = os.path.join(config.BASE_DIR, "docs")
    if not os.path.exists(docs_dir):
        print("docs目录不存在，请先构建站点")
        return False

    skip_dirs = {".git", "logs", "__pycache__", ".temp"}
    skip_files = {".gitignore"}
    files_to_push = []
    for root, dirs, files in os.walk(docs_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fn in files:
            if fn in skip_files:
                continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, config.BASE_DIR).replace("\\", "/")
            files_to_push.append((fp, rel))

    print(f"共 {len(files_to_push)} 个文件需要推送")
    ok, fail = 0, 0
    for fp, rel in files_to_push:
        sha = _get_file_sha(token, rel)
        if _push_one_file(token, fp, rel, commit_msg, sha):
            ok += 1
        else:
            fail += 1
        time.sleep(0.4)

    print(f"\n推送完成: 成功 {ok}, 失败 {fail}")
    return fail == 0


def git_push():
    """传统git推送（fallback方案）"""
    print("\n========== Git 推送 (fallback) ==========")
    base_dir = config.BASE_DIR
    git = config.GIT_PATH

    git_dir = os.path.join(base_dir, ".git")
    if not os.path.exists(git_dir):
        print("初始化Git仓库...")
        run_command(f'"{git}" init', cwd=base_dir)
        run_command(f'"{git}" remote remove origin 2>nul', cwd=base_dir)
        run_command(f'"{git}" remote add origin {config.GITHUB_REPO}', cwd=base_dir)
        run_command(f'"{git}" branch -M main', cwd=base_dir)

    run_command(f'"{git}" config user.name "{config.GITHUB_USERNAME}"', cwd=base_dir)
    run_command(f'"{git}" config user.email "{config.GITHUB_EMAIL}"', cwd=base_dir)
    run_command(f'"{git}" add -A', cwd=base_dir)

    status = run_command(f'"{git}" status --porcelain', cwd=base_dir)
    if not status.stdout.strip():
        print("没有文件变更，跳过推送")
        return True

    commit_msg = f"发布文章 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    run_command(f'"{git}" commit -m "{commit_msg}"', cwd=base_dir)

    result = run_command(f'"{git}" push -u origin main', cwd=base_dir)
    if result.returncode == 0:
        print("推送成功！")
        return True
    else:
        print("推送失败，尝试pull --rebase后重推")
        run_command(f'"{git}" pull origin main --rebase', cwd=base_dir)
        result = run_command(f'"{git}" push -u origin main', cwd=base_dir)
        return result.returncode == 0


def send_pushplus_notification(title, content):
    """发送PushPlus微信推送通知"""
    if not config.PUSHPLUS_TOKEN:
        print("PushPlus token未配置，跳过推送通知")
        return

    print("\n========== 推送微信通知 ==========")
    payload = {
        "token": config.PUSHPLUS_TOKEN,
        "title": f"星辰智能体推送|{title}",
        "content": content,
        "template": "markdown"
    }
    try:
        response = requests.post(config.PUSHPLUS_URL, json=payload, timeout=30)
        result = response.json()
        if result.get("code") == 200:
            print("微信推送成功")
        else:
            print(f"微信推送失败: {result.get('msg', '未知错误')}")
    except Exception as e:
        print(f"微信推送异常: {e}")


def publish():
    """完整发布流程"""
    print(f"\n{'='*60}")
    print(f"博客发布流程开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # 检查文章
    manifest_path = os.path.join(config.PUBLISHED_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"当前共 {len(manifest)} 篇文章")
    else:
        print("还没有文章，请先运行generate_article.py生成文章")
        return False

    # 构建站点
    if not build_site():
        print("站点构建失败！")
        send_pushplus_notification("博客发布失败", "站点构建失败")
        return False

    # 推送：优先GitHub API，fallback到git
    push_ok = False
    if config.GITHUB_TOKEN:
        push_ok = github_api_push()
        if not push_ok:
            print("GitHub API推送失败，尝试git推送...")
            push_ok = git_push()
    else:
        print("未配置GitHub Token，尝试直接git推送...")
        push_ok = git_push()

    if not push_ok:
        print("推送失败！")
        send_pushplus_notification("博客发布失败", "GitHub推送失败")
        return False

    # 推送通知
    latest_post = manifest[-1] if manifest else None
    if latest_post:
        domain = config.DOMAIN if config.DOMAIN else config.TEMP_DOMAIN
        title = f"博客文章已发布: {latest_post['title']}"
        content = f"""
## 新文章已发布

**标题**: {latest_post['title']}

**分类**: {latest_post['category']}

**日期**: {latest_post['date']}

**摘要**: {latest_post.get('excerpt', '')}

**访问地址**: https://{domain}/posts/{latest_post['id']}.html

共已发布 {len(manifest)} 篇文章
"""
        send_pushplus_notification(title, content)

    print(f"\n{'='*60}")
    print(f"发布完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    return True


if __name__ == "__main__":
    publish()
