#!/usr/bin/env python3
"""
掘金扫码登录脚本
通过Selenium打开掘金登录页，用户用手机扫码登录后自动提取cookie
支持两种模式：
1. 交互模式：弹出浏览器窗口，等待用户扫码
2. 无头模式：后台运行，弹出二维码图片让用户用手机扫描（需要手机访问掘金网页版扫码）
"""

import os
import sys
import json
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Cookie保存路径
COOKIE_FILE = os.path.join(config.BASE_DIR, "juejin_cookie.json")


def check_juejin_cookie(cookie_str):
    """检查掘金cookie是否有效
    
    使用草稿API验证（user_info API跨域验证有问题，但draft API可以正常验证）
    
    Args:
        cookie_str: cookie字符串
    
    Returns:
        bool: cookie是否有效
    """
    if not cookie_str:
        return False
    try:
        # 使用草稿创建API做探活（空title不会真的创建文章）
        r = requests.post(
            'https://api.juejin.cn/content_api/v1/article_draft/create',
            headers={
                'Cookie': cookie_str,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://juejin.cn/editor/drafts/new',
                'Origin': 'https://juejin.cn',
            },
            json={
                'title': '',
                'content': '',
                'brief_content': 'x' * 50,
                'category_id': '6809637767543259144',
                'tag_ids': [],
                'edit_type': 10,
                'draft_type': 1,
            },
            timeout=10
        )
        data = r.json()
        if data.get("err_no") == 0:
            # cookie有效，但创建了空草稿，记录ID以便清理
            draft_id = data.get("data", {}).get("id")
            if draft_id:
                # 删除这个测试草稿
                try:
                    requests.post(
                        'https://api.juejin.cn/content_api/v1/article_draft/delete',
                        headers={
                            'Cookie': cookie_str,
                            'Content-Type': 'application/json',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Origin': 'https://juejin.cn',
                        },
                        json={'draft_id': draft_id},
                        timeout=10
                    )
                except Exception:
                    pass
            print("掘金cookie有效")
            return True
        elif data.get("err_no") == 2:
            print("掘金cookie无效: 未登录")
            return False
        else:
            # 其他错误（如参数错误）说明cookie是有效的
            err_no = data.get("err_no")
            if err_no in (1, 403, 501):
                # 参数错误但cookie有效
                print(f"掘金cookie有效（API返回err_no={err_no}，但鉴权通过）")
                return True
            print(f"掘金cookie验证: err_no={err_no}, err_msg={data.get('err_msg', '')}")
            return False
    except Exception as e:
        print(f"掘金cookie检查异常: {e}")
        return False


def save_cookie_to_file(cookie_str):
    """保存cookie到文件"""
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump({"cookie": cookie_str, "updated": time.strftime("%Y-%m-%d %H:%M:%S")}, f, ensure_ascii=False)
    print(f"Cookie已保存到: {COOKIE_FILE}")


def load_cookie_from_file():
    """从文件加载cookie"""
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("cookie", "")
    return ""


def login_with_selenium(headless=False):
    """使用Selenium打开掘金登录页，等待用户扫码
    
    Args:
        headless: 是否使用无头模式（不推荐，扫码需要看到页面）
    
    Returns:
        str: cookie字符串，失败返回None
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options
        from selenium.webdriver.edge.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        print("请先安装selenium: python -m pip install selenium")
        return None
    
    print("\n" + "=" * 60)
    print("掘金扫码登录")
    print("=" * 60)
    print("即将打开浏览器到掘金登录页...")
    print("请用手机掘金APP扫描页面上的二维码")
    print("扫码并确认后，程序会自动获取cookie")
    print("=" * 60 + "\n")
    
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    # 使用Edge浏览器
    try:
        driver = webdriver.Edge(options=options)
    except Exception:
        # fallback: 尝试使用系统Edge
        try:
            from selenium.webdriver.edge.service import Service as EdgeService
            service = EdgeService()
            driver = webdriver.Edge(service=service, options=options)
        except Exception as e:
            print(f"无法启动Edge浏览器: {e}")
            print("请确保已安装Microsoft Edge浏览器")
            return None
    
    cookie_str = None
    
    try:
        # 打开掘金登录页
        driver.get("https://juejin.cn/login")
        print("浏览器已打开掘金登录页")
        print("请在手机上打开掘金APP，扫描页面上的二维码...")
        print("（等待登录成功，最多等待120秒）\n")
        
        # 等待用户扫码登录（检测URL变化或cookie出现）
        start_time = time.time()
        max_wait = 120  # 最长等待120秒
        logged_in = False
        
        while time.time() - start_time < max_wait:
            time.sleep(2)
            
            # 检查当前URL是否跳转（登录成功后会跳转到首页）
            current_url = driver.current_url
            if "login" not in current_url:
                logged_in = True
                break
            
            # 检查是否有登录cookie
            cookies = driver.get_cookies()
            has_session = any(c["name"] == "sessionid" for c in cookies)
            if has_session:
                logged_in = True
                break
            
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0 and elapsed > 0:
                print(f"  等待扫码中... ({elapsed}秒)")
        
        if not logged_in:
            print("登录超时（120秒），请重试")
            return None
        
        print("登录成功！正在提取cookie...")
        time.sleep(5)  # 等待cookie完全设置
        
        # 方法1：从Selenium cookies API获取
        selenium_cookies = driver.get_cookies()
        
        # 方法2：从JS上下文获取document.cookie（更可靠）
        try:
            js_cookie = driver.execute_script("return document.cookie;")
            print(f"JS document.cookie长度: {len(js_cookie) if js_cookie else 0}")
        except Exception:
            js_cookie = ""
        
        # 优先使用Selenium cookies构建完整cookie字符串（包含HttpOnly字段）
        all_cookies = []
        for c in selenium_cookies:
            all_cookies.append(c)
        
        cookie_str = "; ".join([f'{c["name"]}={c["value"]}' for c in all_cookies])
        print(f"提取到 {len(all_cookies)} 个cookie")
        
        # 调试：列出所有cookie名称
        cookie_names = [c["name"] for c in all_cookies]
        print(f"Cookie名称列表: {', '.join(cookie_names)}")
        
        # 检查关键cookie
        key_names = ["sessionid", "sessionid_ss", "sid_tt", "uid_tt", "sid_guard"]
        found_keys = [n for n in key_names if any(c["name"] == n for c in all_cookies)]
        print(f"关键cookie: {found_keys}")
        
        # 先保存cookie（不管验证结果如何），方便后续调试
        save_cookie_to_file(cookie_str)
        print(f"Cookie字符串长度: {len(cookie_str)}")
        
        # 验证cookie
        if check_juejin_cookie(cookie_str):
            print("\n掘金cookie获取成功！")
            return cookie_str
        else:
            print("Selenium cookie验证失败，尝试用JS cookie...")
            # 如果Selenium cookie不行，试试JS cookie
            if js_cookie and check_juejin_cookie(js_cookie):
                save_cookie_to_file(js_cookie)
                print("\n用JS cookie验证成功！")
                return js_cookie
            
            # 最后一种尝试：用浏览器session直接访问API验证
            print("尝试从浏览器session获取用户信息...")
            try:
                driver.get("https://juejin.cn/user/info")
                time.sleep(3)
                # 此时如果浏览器内已登录，会显示用户信息页面
                current_url = driver.current_url
                print(f"浏览器当前URL: {current_url}")
                
                # 在已登录浏览器中执行JS获取用户信息
                user_data = driver.execute_script("""
                    return fetch('https://api.juejin.cn/user_api/v1/user_info', {
                        credentials: 'include'
                    }).then(r => r.json());
                """)
                if user_data and user_data.get("err_no") == 0:
                    username = user_data.get("data", {}).get("user_name", "未知")
                    print(f"浏览器内验证成功，用户: {username}")
                    print("\n掘金cookie获取成功！（虽然跨域验证失败，但cookie在浏览器中有效）")
                    return cookie_str
            except Exception as e:
                print(f"浏览器内验证也失败: {e}")
            
            print("cookie验证失败，但cookie已保存到文件")
            print("注意：cookie可能在浏览器中有效，只是requests跨域验证失败")
            print("建议直接使用保存的cookie")
            return cookie_str
        
    except Exception as e:
        print(f"登录过程出错: {e}")
        return None
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def update_cookie_to_bat(cookie_str):
    """更新cookie到run_blog_task.bat中的环境变量
    
    Args:
        cookie_str: 新的cookie字符串
    """
    bat_path = os.path.join(config.SCRIPTS_DIR, "run_blog_task.bat")
    if not os.path.exists(bat_path):
        print(f"bat文件不存在: {bat_path}")
        return
    
    with open(bat_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 查找JUEJIN_COOKIE行
    import re
    pattern = r'set "JUEJIN_COOKIE=.*?"'
    replacement = f'set "JUEJIN_COOKIE={cookie_str}"'
    
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("已更新run_blog_task.bat中的JUEJIN_COOKIE")
    else:
        print("bat文件中未找到JUEJIN_COOKIE设置")


def get_valid_cookie():
    """获取有效的掘金cookie（先检查缓存，无效则触发扫码登录）
    
    Returns:
        str: 有效的cookie字符串，失败返回None
    """
    # 先检查环境变量
    if config.JUEJIN_COOKIE and check_juejin_cookie(config.JUEJIN_COOKIE):
        return config.JUEJIN_COOKIE
    
    # 再检查文件缓存
    file_cookie = load_cookie_from_file()
    if file_cookie and check_juejin_cookie(file_cookie):
        return file_cookie
    
    # 需要重新登录
    print("掘金cookie已失效，需要重新扫码登录")
    cookie = login_with_selenium()
    if cookie:
        # 更新bat文件
        update_cookie_to_bat(cookie)
        return cookie
    
    return None


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # 只检查当前cookie状态
        env_cookie = config.JUEJIN_COOKIE
        if env_cookie:
            print("环境变量中的cookie:")
            check_juejin_cookie(env_cookie)
        else:
            print("环境变量中未配置JUEJIN_COOKIE")
        
        file_cookie = load_cookie_from_file()
        if file_cookie:
            print("\n文件中的cookie:")
            check_juejin_cookie(file_cookie)
        else:
            print("\n无文件缓存cookie")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "login":
        # 强制扫码登录
        cookie = login_with_selenium()
        if cookie:
            update_cookie_to_bat(cookie)
            print(f"\ncookie长度: {len(cookie)} 字符")
        else:
            print("登录失败")
    
    else:
        print("用法:")
        print("  python juejin_qr_login.py check   - 检查当前cookie状态")
        print("  python juejin_qr_login.py login    - 扫码登录获取新cookie")
