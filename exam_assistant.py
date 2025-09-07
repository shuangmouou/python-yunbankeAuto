import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from browser_manager import start_async_browser_check, launch_browser_manually
from api_manager import set_api_key, test_api_connection
from auto_process import start_auto_process
import os
import requests
import zipfile
import shutil


class ExamAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("智能考试助手 v4.2")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)

        # 设置默认字体
        self.default_font = ('Microsoft YaHei UI', 10)
        self.title_font = ('Microsoft YaHei UI', 11, 'bold')

        # 初始化变量
        self.parsed_result = ""
        self.driver = None
        self.doubao_api_key = ""
        self.is_exam_page_loaded = False
        self.browser_check_in_progress = False

        # 创建界面
        self.create_menu()
        self.create_ui()

        # 异步执行浏览器检测
        self.root.after(100, lambda: start_async_browser_check(self))

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="设置API密钥", command=lambda: set_api_key(self))
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menubar)

    def create_ui(self):
        """创建主界面"""
        # 创建标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # 创建答题标签页
        self.create_answer_tab()

    def create_answer_tab(self):
        """创建答题标签页"""
        answer_frame = tk.Frame(self.notebook)
        self.notebook.add(answer_frame, text="自动答题")

        # 使用说明区域
        instructions_frame = tk.LabelFrame(answer_frame, text="使用说明", font=self.title_font, height=200)
        instructions_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        instructions_frame.pack_propagate(0)

        instructions = [
            "1. 程序启动时会自动检测可复用的浏览器",
            "2. 未检测到时请点击'启动浏览器'按钮",
            "3. 在浏览器中登录您的云班课账号",
            "4. 进入具体的考试答题页面",
            "5. 输入豆包API密钥并点击'开始答题'"
        ]

        for text in instructions:
            label = tk.Label(instructions_frame, text=text, anchor='w', justify='left',
                             font=self.default_font, padx=10)
            label.pack(fill='x', pady=2)

        # API密钥区域
        api_frame = tk.Frame(answer_frame)
        api_frame.pack(fill=tk.X, padx=10, pady=5)

        api_label = tk.Label(api_frame, text="豆包API密钥:", font=self.default_font)
        api_label.pack(side=tk.LEFT, padx=(0, 5))

        self.api_key_var = tk.StringVar()
        self.api_key_entry = tk.Entry(api_frame, textvariable=self.api_key_var,
                                      width=40, font=self.default_font, show="*")
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 控制按钮区域
        control_frame = tk.Frame(answer_frame, height=60)
        control_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        control_frame.pack_propagate(0)

        self.auto_button = tk.Button(control_frame, text="开始答题",
                                     command=lambda: start_auto_process(self),
                                     font=("Microsoft YaHei UI", 12, "bold"),
                                     bg="#FF9800", fg="white", padx=30, pady=10)
        self.auto_button.pack(side=tk.LEFT, padx=5)

        self.test_button = tk.Button(control_frame, text="测试API连接",
                                     command=lambda: test_api_connection(self),
                                     font=self.title_font, bg="#2196F3", fg="white", padx=20)
        self.test_button.pack(side=tk.LEFT, padx=5)

        self.launch_button = tk.Button(control_frame, text="启动浏览器",
                                       command=lambda: launch_browser_manually(self),
                                       font=self.title_font, bg="#4CAF50", fg="white", padx=20)
        self.launch_button.pack(side=tk.LEFT, padx=5)

        self.load_edge_button = tk.Button(control_frame, text="加载edge",
                                       command=self.load_edge,
                                       font=self.title_font, bg="#FF5722", fg="white", padx=20)
        self.load_edge_button.pack(side=tk.LEFT, padx=5)

        self.redetect_button = tk.Button(control_frame, text="重新检测复用浏览器",
                                       command=lambda: start_async_browser_check(self),
                                       font=self.title_font, bg="#2196F3", fg="white", padx=20)
        self.redetect_button.pack(side=tk.LEFT, padx=5)



        # 状态日志区域
        status_frame = tk.LabelFrame(answer_frame, text="执行日志", font=self.title_font)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD,
                                                     font=self.default_font)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.status_text.config(state=tk.DISABLED)

    def write_log(self, message):
        """在状态日志区域写入消息"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()

    def show_help(self):
        """显示使用说明"""
        help_text = """
使用说明

【自动答题工具】
1. 程序启动时会自动尝试连接已打开的浏览器
2. 如果没有连接成功，请点击"启动浏览器"按钮手动启动
3. 在浏览器中登录您的云班课账号
4. 进入具体的考试答题页面
5. 返回本程序，在"自动答题"标签页中输入豆包API密钥
6. 点击"开始答题"按钮启动自动化流程：
   • 自动获取考试题目
   • 自动调用豆包API获取答案
   • 自动填写答案到考试页面


【API设置】
1. 在"设置"菜单中选择"设置API密钥"
2. 输入您从豆包平台获取的API密钥
3. 点击"测试连接"按钮验证API是否可用

注意事项:
• 请确保浏览器窗口保持打开状态
• 答题过程中不要操作浏览器
• 答题完成后请检查答案是否正确
• 如果遇到问题，请查看日志信息

"""
        messagebox.showinfo("使用说明", help_text)

    def show_about(self):
        """显示关于信息"""
        about_text = """
智能考试助手 v4.2

功能特点:
• 快速浏览器检测（3秒内完成）
• 手动启动浏览器功能
• 全自动化答题流程
• 集成豆包AI智能解答系统
• 支持单选题、多选题、填空题、判断题
• API连接测试功能
• 用户友好的图形界面和详细日志


技术栈:
• Python 3.x
• Tkinter GUI框架
• Selenium浏览器自动化
• 豆包大模型API

"""
        messagebox.showinfo("关于", about_text)

    def load_edge(self):
        # 创建lanzouyun文件夹
        download_dir = "lanzouyun"
        os.makedirs(download_dir, exist_ok=True)

        # 通用请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
            'Accept': 'application/json, text/javascript, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://wwrl.lanzouu.com',
            'Connection': 'keep-alive',
        }

        # URL列表和对应的文件名
        url_list = [
            'https://wwrl.lanzouu.com/iGG2a2z6ijlc',
            'https://wwrl.lanzouu.com/izSYa2z6im2b',
            'https://wwrl.lanzouu.com/iZPpP2z6iq0d',
            'https://wwrl.lanzouu.com/ipO9n2z6iste',
            'https://wwrl.lanzouu.com/i3Uo12z6ivtc',
            'https://wwrl.lanzouu.com/i7M3l2z6iwkj'
        ]

        filenames = ["edge_split.zip", "edge_split.z01", "edge_split.z02", "edge_split.z03", "edge_split.z04", "edge_split.z05"]

        # 使用Session保持会话状态
        session = requests.Session()
        session.headers.update(headers)

        for i, url in enumerate(url_list):
            try:
                self.write_log(f"\n正在处理URL {i + 1}/{len(url_list)}: {url}")

                # 获取初始页面
                response = session.get(url)
                response.raise_for_status()

                # 提取iframe URL
                from lxml import etree
                soup = etree.HTML(response.text)
                iframe = soup.xpath('//iframe/@src')[0]
                if not iframe.startswith('http'):
                    iframe = f'https://wwrl.lanzouu.com/{iframe}'

                self.write_log(f"iframe URL: {iframe}")

                # 更新Referer并获取iframe内容
                session.headers.update({'Referer': url})
                iframe_response = session.get(iframe)
                iframe_response.raise_for_status()

                # 提取关键参数
                import re
                wp_sign = re.search(r"var wp_sign = '([^']+)'", iframe_response.text).group(1)
                ajaxdata = re.search(r"var ajaxdata = '([^']+)'", iframe_response.text).group(1)
                ajaxm_url = re.search(r"url\s*:\s*'(.*?)',//data//", iframe_response.text).group(1)

                self.write_log(f"wp_sign: {wp_sign}")
                self.write_log(f"ajaxdata: {ajaxdata}")
                self.write_log(f"ajaxm_url: {ajaxm_url}")

                # 构建并发送AJAX请求
                ajax_url = f"https://wwrl.lanzouu.com{ajaxm_url}"
                session.headers.update({'Referer': iframe})

                data = {
                    'action': 'downprocess',
                    'websignkey': ajaxdata,
                    'signs': ajaxdata,
                    'sign': wp_sign,
                    'websign': '',
                    'kd': '1',
                    'ves': '1'
                }

                # 获取下载信息
                ajax_response = session.post(ajax_url, data=data)
                ajax_response.raise_for_status()

                # 解析JSON响应（让json库处理转义字符）
                download_info = ajax_response.json()

                # 构建下载URL
                download_domain = download_info['dom']
                download_path = download_info['url']

                # 处理可能的转义字符
                download_domain = download_domain.replace('\\', '')
                download_url = f"{download_domain}/file/{download_path}"

                self.write_log(f"下载URL: {download_url}")

                # 更新Referer为AJAX请求URL
                session.headers.update({'Referer': ajax_url})

                # 下载文件
                filename = filenames[i]
                file_path = os.path.join(download_dir, filename)

                self.write_log(f"开始下载文件: {filename}")

                # 使用stream=True处理大文件
                with session.get(download_url, stream=True) as r:
                    r.raise_for_status()

                    # 检查响应头，确认是否为文件下载
                    content_type = r.headers.get('content-type', '')
                    content_length = r.headers.get('content-length', '')

                    self.write_log(f"响应类型: {content_type}")
                    self.write_log(f"文件大小: {int(content_length) / 1024 / 1024:.2f} MB" if content_length else "未知大小")

                    # 保存文件
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:  # 过滤空块
                                f.write(chunk)

                    self.write_log(f"✅ 文件 {filename} 下载完成")

            except Exception as e:
                self.write_log(f"❌ 处理URL {url} 时出错: {str(e)}")
                continue

        self.write_log("\n所有文件下载完成！")

        # 定义固定路径和文件名
        base_dir = download_dir
        base_name = "edge_split"
        output_folder = "edge_extracted"

        # 构建分卷文件列表（按正确顺序）
        volume_files = [
            os.path.join(base_dir, f"{base_name}.zip"),  # 第一个分卷
            os.path.join(base_dir, f"{base_name}.z01"),  # 第二个分卷
            os.path.join(base_dir, f"{base_name}.z02"),  # 第三个分卷
            os.path.join(base_dir, f"{base_name}.z03"),  # 第四个分卷
            os.path.join(base_dir, f"{base_name}.z04"),
            os.path.join(base_dir, f"{base_name}.z05"),
        ]

        # 检查所有分卷文件是否存在
        existing_files = [f for f in volume_files if os.path.exists(f)]

        if not existing_files:
            self.write_log(f"错误: 未找到任何分卷文件")
            return

        if len(existing_files) < len(volume_files):
            self.write_log(f"警告: 部分分卷文件缺失，找到 {len(existing_files)}/{len(volume_files)} 个")
            self.write_log("已找到的分卷:")
            for f in existing_files:
                self.write_log(f"  - {os.path.basename(f)}")

        self.write_log(f"开始处理现有分卷文件...")

        # 创建临时合并文件路径
        temp_zip = os.path.join(base_dir, f"{base_name}_merged.zip")

        # 合并分卷文件
        self.write_log("开始合并分卷文件...")
        with open(temp_zip, 'wb') as output:
            for volume in existing_files:
                self.write_log(f"合并: {os.path.basename(volume)}")
                with open(volume, 'rb') as f:
                    shutil.copyfileobj(f, output)

        self.write_log(f"分卷合并完成: {temp_zip}")

        # 创建解压目录
        extract_dir = os.path.join(base_dir, output_folder)
        os.makedirs(extract_dir, exist_ok=True)

        # 解压文件
        try:
            self.write_log(f"开始解压到: {extract_dir}")
            with zipfile.ZipFile(temp_zip, 'r') as zipf:
                zipf.extractall(extract_dir)
            self.write_log(f"解压完成! 文件保存在: {extract_dir}")
        except Exception as e:
            self.write_log(f"解压失败: {e}")
            self.write_log("可能是由于分卷文件不完整导致的")
            return
        finally:
            # 删除临时文件
            if os.path.exists(temp_zip):
                os.remove(temp_zip)
                self.write_log("临时合并文件已删除")

        # 寻找msedge.exe的文件路径
        msedge_path = None
        for root, dirs, files in os.walk(extract_dir):
            if 'msedge.exe' in files:
                msedge_path = os.path.join(root, 'msedge.exe')
                break

        if msedge_path:
            self.write_log(f"找到msedge.exe路径: {msedge_path}")
            # 生成bat文件
            bat_content = ".\edge_extracted\edge\msedge.exe --remote-debugging-port=9222 --user-data-dir=\"D:\\selenium_edge\""
            bat_path = os.path.join(download_dir, 'launch_edge.bat')
            with open(bat_path, 'w') as bat_file:
                bat_file.write(bat_content)
            self.write_log(f"已生成bat文件: {bat_path}")
        else:
            self.write_log("未找到msedge.exe文件")