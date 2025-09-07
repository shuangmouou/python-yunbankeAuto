import threading
import socket
import os
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service


def start_async_browser_check(assistant):
    """开始异步浏览器检测（优化版）"""
    assistant.write_log("正在快速检测可复用的浏览器...")
    assistant.browser_check_in_progress = True

    # 禁用控制按钮防止用户干扰
    assistant.auto_button.config(state='disabled')
    assistant.test_button.config(state='disabled')
    assistant.launch_button.config(state='disabled')

    # 在后台线程执行检测
    threading.Thread(target=try_connect_existing_browser_fast, args=(assistant,), daemon=True).start()


def try_connect_existing_browser_fast(assistant):
    """快速尝试连接已存在的浏览器实例"""
    try:
        # 首先快速检查端口是否开放
        if not is_port_open("127.0.0.1", 9222):
            assistant.root.after(0, lambda: on_browser_connection_failed(assistant, "调试端口未开放"))
            return

        # 配置复用浏览器选项（优化连接参数）
        edge_options = Options()
        edge_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        edge_options.add_argument("--disable-extensions")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")

        # 尝试使用当前目录下的驱动程序
        current_dir = os.path.dirname(os.path.abspath(__file__))
        driver_path = os.path.join(current_dir, "msedgedriver.exe")

        # 创建服务时设置更短的启动超时（3秒）
        service = Service(
            executable_path=driver_path,
            timeout=3000
        )

        # 尝试创建浏览器实例
        assistant.driver = webdriver.Edge(
            service=service,
            options=edge_options,
            keep_alive=False
        )

        # 设置页面加载超时为5秒
        assistant.driver.set_page_load_timeout(5)

        # 检查是否成功连接（使用JS快速获取信息）
        try:
            current_url = assistant.driver.execute_script('return window.location.href')
            title = assistant.driver.execute_script('return document.title')
            assistant.root.after(0, lambda: on_browser_connected(assistant, current_url, title))
        except WebDriverException as e:
            assistant.root.after(0, lambda: on_browser_connection_failed(assistant, f"浏览器窗口异常: {str(e)}"))
            if assistant.driver:
                assistant.driver.quit()
                assistant.driver = None

    except Exception as e:
        error_msg = str(e)
        if "cannot connect to chrome" in error_msg.lower() or "connection refused" in error_msg.lower():
            error_msg = "未检测到可复用的浏览器（调试端口未启用）"
        elif "timeout" in error_msg.lower():
            error_msg = "检测超时（3秒内未响应）"

        # 在主线程显示错误
        assistant.root.after(0, lambda: on_browser_connection_failed(assistant, error_msg))
    finally:
        # 在主线程恢复UI状态
        assistant.root.after(0, lambda: on_browser_check_complete(assistant))


def is_port_open(host, port):
    """检查指定端口是否开放"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    except:
        return False
    finally:
        sock.close()


def on_browser_connected(assistant, url, title):
    """当浏览器连接成功时调用"""
    assistant.write_log("✅ 成功连接到浏览器实例")
    assistant.write_log(f"当前页面: {title}")
    assistant.write_log(f"URL: {url}")


def on_browser_connection_failed(assistant, error_msg):
    """当浏览器连接失败时调用"""
    assistant.write_log(f"❌ 浏览器连接检测失败: {error_msg}")
    if assistant.driver:
        try:
            assistant.driver.quit()
        except:
            pass
        assistant.driver = None


def on_browser_check_complete(assistant):
    """浏览器检查完成后恢复UI状态"""
    assistant.browser_check_in_progress = False

    # 恢复控制按钮
    assistant.auto_button.config(state='normal')
    assistant.test_button.config(state='normal')
    assistant.launch_button.config(state='normal')

    # 如果没有连接成功，提示用户
    if not assistant.driver:
        show_browser_prompt(assistant)


def show_browser_prompt(assistant):
    """显示浏览器连接提示弹窗"""
    from tkinter import messagebox
    messagebox.showinfo("浏览器连接提示",
                        "未检测到可复用的浏览器实例\n请点击'启动浏览器'按钮手动启动\n\n提示: 启动浏览器时请添加参数:\n--remote-debugging-port=9222")


def launch_browser_manually(assistant):
    """手动启动浏览器"""
    try:
        # 如果已有浏览器实例，先关闭
        if assistant.driver:
            try:
                assistant.driver.quit()
            except:
                pass
            assistant.driver = None

        assistant.write_log("正在手动启动浏览器...")

        # 配置浏览器选项
        edge_options = Options()
        edge_options.add_argument("--remote-debugging-port=9222")
        edge_options.add_argument("--user-data-dir=D:\selenium_edge")
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option("useAutomationExtension", False)

        # 设置浏览器窗口大小和位置
        edge_options.add_argument("--window-size=1200,800")
        edge_options.add_argument("--window-position=100,100")

        # 尝试使用当前目录下的驱动程序
        current_dir = os.path.dirname(os.path.abspath(__file__))
        driver_path = os.path.join(current_dir, "msedgedriver.exe")
        service = Service(driver_path)

        # 启动浏览器
        assistant.driver = webdriver.Edge(service=service, options=edge_options)

        # 导航到云班课登录页面
        assistant.driver.get("https://www.mosoteach.cn/")

        assistant.write_log("✅ 浏览器已启动，请登录并进入考试页面")
        assistant.write_log("提示: 保持浏览器窗口打开，不要关闭")

    except Exception as e:
        assistant.write_log(f"❌ 启动浏览器失败: {str(e)}")
        if assistant.driver:
            try:
                assistant.driver.quit()
            except:
                pass
            assistant.driver = None
        from tkinter import messagebox
        messagebox.showerror("错误", f"启动浏览器失败: {str(e)}")


def check_browser_alive(assistant):
    """检查浏览器窗口是否仍然存活"""
    if not assistant.driver:
        return False

    try:
        # 尝试获取当前窗口句柄，如果失败则说明浏览器已关闭
        assistant.driver.current_window_handle
        return True
    except:
        assistant.driver = None
        return False