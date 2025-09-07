import tkinter as tk
import requests
import json
import re
from tkinter import messagebox


def set_api_key(assistant):
    """设置豆包API密钥"""
    dialog = tk.Toplevel(assistant.root)
    dialog.title("设置豆包API密钥")
    dialog.geometry("500x200")
    dialog.resizable(False, False)

    tk.Label(dialog, text="豆包API密钥:", font=assistant.title_font).pack(pady=(20, 5))

    api_var = tk.StringVar(value=assistant.api_key_var.get())
    api_entry = tk.Entry(dialog, textvariable=api_var, width=50, font=assistant.default_font)
    api_entry.pack(pady=5)

    def save_api_key():
        assistant.api_key_var.set(api_var.get())
        assistant.doubao_api_key = api_var.get()
        dialog.destroy()
        messagebox.showinfo("成功", "API密钥已保存")

    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="保存", command=save_api_key,
              font=assistant.default_font, bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=10)

    tk.Button(button_frame, text="测试连接", command=lambda: test_api_connection(assistant, api_var.get()),
              font=assistant.default_font, bg="#2196F3", fg="white", width=15).pack(side=tk.LEFT, padx=10)

    tk.Label(dialog, text="温馨提示: 请在豆包官网申请API密钥", font=("Microsoft YaHei UI", 9), fg="#666").pack(
        pady=5)


def test_api_connection(assistant, api_key=None):
    """测试豆包API连接性"""
    if not api_key:
        api_key = assistant.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("API密钥缺失", "请先输入豆包API密钥")
            return

    try:
        assistant.write_log("正在测试豆包API连接...")

        # 豆包API请求URL和头部
        url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 构建测试请求
        payload = {
            "model": "doubao-1-5-pro-32k-250115",
            "messages": [
                {"role": "system", "content": "你是一个专业的考试助手"},
                {"role": "user", "content": "你好，请回复'连接成功'"}
            ],
        }

        # 发送API请求（超时45秒）
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=45)

        if response.status_code == 200:
            # 解析响应
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                if "连接成功" in content:
                    assistant.write_log("✅ API连接测试成功！")
                    messagebox.showinfo("测试成功", "API连接正常！")
                else:
                    assistant.write_log(f"⚠️ API返回意外内容: {content}")
                    messagebox.showinfo("测试结果", f"API连接正常，但返回内容: {content}")
            else:
                assistant.write_log("❌ API响应中未找到有效答案")
                messagebox.showerror("测试失败", "API响应中未找到有效答案")
        else:
            assistant.write_log(f"❌ API调用失败，状态码: {response.status_code}, 响应: {response.text}")
            messagebox.showerror("测试失败", f"API调用失败，状态码: {response.status_code}\n响应: {response.text}")

    except requests.Timeout:
        assistant.write_log("❌ API连接超时（超过45秒）")
        messagebox.showerror("测试失败", "API连接超时（超过45秒）")
    except Exception as e:
        assistant.write_log(f"❌ API连接测试失败: {str(e)}")
        messagebox.showerror("测试失败", f"连接测试失败: {str(e)}")


def chinese_to_arabic(chinese_num):
    """将中文数字转换为阿拉伯数字"""
    mapping = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
        '十': 10, '百': 100, '千': 1000, '万': 10000
    }

    if chinese_num.isdigit():
        return int(chinese_num)

    total = 0
    current = 0
    for char in chinese_num:
        value = mapping.get(char)
        if value is None:
            continue
        if value >= 10:
            total += max(current, 1) * value
            current = 0
        else:
            current = value
    return total + current


def call_doubao_api(assistant, question_text):
    """调用豆包API获取题目答案"""
    if not assistant.doubao_api_key:
        assistant.write_log("错误：未设置豆包API密钥")
        return None

    try:
        assistant.write_log("正在调用豆包API获取答案...")

        # 豆包API请求URL和头部
        url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        headers = {
            "Authorization": f"Bearer {assistant.doubao_api_key}",
            "Content-Type": "application/json"
        }

        # 构建智能提示词
        prompt = f"""
请根据以下题目和选项，给出每道题的正确答案。请按照以下格式回答：
第X题答案：A······（如果是多选，答案内容用逗号分隔；如果是填空，多个填空用分号分隔；判断题使用"正确"或"错误"）

题目如下：
{question_text}

注意：
1. 不要包含任何多余的文字
2. 每道题一行
3. 严格按照格式回答
            """

        # 构建请求数据
        payload = {
            "model": "doubao-1-5-pro-32k-250115",
            "messages": [
                {"role": "system", "content": "你是一个专业的考试助手，负责解答选择题、填空题和判断题"},
                {"role": "user", "content": prompt}
            ],
        }

        # 发送API请求（超时45秒）
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=45)

        if response.status_code == 200:
            # 解析响应
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                answer_content = response_data["choices"][0]["message"]["content"]
                assistant.write_log("豆包API调用成功")
                return answer_content
            else:
                assistant.write_log("API响应中未找到有效答案")
        else:
            assistant.write_log(f"豆包API调用失败，状态码: {response.status_code}, 响应: {response.text}")

        return None
    except Exception as e:
        assistant.write_log(f"调用豆包API时出错: {str(e)}")
        return None


def parse_doubao_response(assistant, response_text):
    """解析豆包API返回的答案"""
    try:
        assistant.write_log("正在解析豆包API的答案...")

        # 提取答案的正则表达式
        pattern = r'第([零一二三四五六七八九十百千万\d]+)题答案[:：]\s*([^\n]+)'
        answers = {}

        for match in re.finditer(pattern, response_text):
            chinese_num = match.group(1)
            question_num = chinese_to_arabic(chinese_num)
            answer_str = match.group(2).strip()
            answers[question_num] = answer_str

        # 将答案格式化为字符串
        formatted_answers = "\n".join([f"第{q_num}题答案：{ans}" for q_num, ans in answers.items()])

        assistant.write_log(f"成功解析 {len(answers)} 道题的答案")
        return formatted_answers, answers
    except Exception as e:
        assistant.write_log(f"解析豆包API答案时出错: {str(e)}")
        return "", {}