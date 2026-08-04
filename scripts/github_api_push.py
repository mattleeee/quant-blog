#!/usr/bin/env python3
"""
通过GitHub API推送文件，绕过git的DNS/网络问题
"""

import os
import sys
import json
import base64
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

GITHUB_API = "https://api.github.com"
REPO = "mattleeee/quant-blog"


def get_headers(token=None):
    """获取API请求头"""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def create_or_update_file(token, path, content, message, sha=None):
    """通过API创建或更新文件
    
    Args:
        token: GitHub Personal Access Token
        path: 文件路径（相对于仓库根目录）
        content: 文件内容（字符串）
        message: commit message
        sha: 文件的SHA（更新时需要）
    
    Returns:
        True/False
    """
    url = f"{GITHUB_API}/repos/{REPO}/contents/{path}"
    
    # base64编码内容
    content_bytes = content.encode("utf-8")
    content_b64 = base64.b64encode(content_bytes).decode("ascii")
    
    data = {
        "message": message,
        "content": content_b64,
    }
    if sha:
        data["sha"] = sha
    
    try:
        response = requests.put(url, headers=get_headers(token), json=data, timeout=30)
        if response.status_code in (200, 201):
            print(f"  推送成功: {path}")
            return True
        else:
            print(f"  推送失败: {path} - {response.status_code} {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  推送异常: {path} - {e}")
        return False


def get_file_sha(token, path):
    """获取文件的SHA（如果文件存在）"""
    url = f"{GITHUB_API}/repos/{REPO}/contents/{path}"
    try:
        response = requests.get(url, headers=get_headers(token), timeout=15)
        if response.status_code == 200:
            return response.json().get("sha")
    except Exception:
        pass
    return None


def push_all_files(token, base_dir, commit_msg=None):
    """推送所有文件到GitHub"""
    if commit_msg is None:
        commit_msg = f"发布文章 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    print(f"\n========== 通过GitHub API推送 ==========")
    print(f"仓库: {REPO}")
    print(f"提交信息: {commit_msg}")
    
    # 需要推送的文件列表
    files_to_push = []
    
    # 收集所有需要推送的文件
    for root, dirs, files in os.walk(base_dir):
        # 跳过.git目录
        if ".git" in root:
            continue
        # 跳过logs目录
        if "logs" in root:
            continue
            
        for filename in files:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, base_dir).replace("\\", "/")
            
            # 跳过.gitignore
            if rel_path == ".gitignore":
                continue
            
            # 只推送特定类型的文件
            ext = os.path.splitext(filename)[1]
            if ext in ('.py', '.md', '.css', '.html', '.xml', '.json', '', '.nojekyll'):
                files_to_push.append((rel_path, filepath))
    
    print(f"共 {len(files_to_push)} 个文件需要推送")
    
    success_count = 0
    fail_count = 0
    
    for rel_path, filepath in files_to_push:
        # 读取文件内容
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # 二进制文件跳过
            continue
        except Exception as e:
            print(f"  读取失败: {rel_path} - {e}")
            fail_count += 1
            continue
        
        # 获取已有文件的SHA（用于更新）
        sha = get_file_sha(token, rel_path)
        
        # 推送
        if create_or_update_file(token, rel_path, content, commit_msg, sha):
            success_count += 1
        else:
            fail_count += 1
        
        # 避免API限频
        import time
        time.sleep(0.5)
    
    print(f"\n推送完成: 成功 {success_count}, 失败 {fail_count}")
    return fail_count == 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        print("请提供GitHub Personal Access Token")
        print("用法: python github_api_push.py <token>")
        print("\n获取Token步骤:")
        print("1. 打开 https://github.com/settings/tokens")
        print("2. 点 Generate new token (classic)")
        print("3. 勾选 repo 权限")
        print("4. 生成后复制token")
        sys.exit(1)
    
    push_all_files(token, config.BASE_DIR)
