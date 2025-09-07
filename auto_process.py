import threading
import time
import re
from lxml import html
import requests
import json
from api_manager import call_doubao_api
from api_manager import parse_doubao_response
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def start_auto_process(assistant):
    """启动全自动化流程"""
    # 检查API密钥
    assistant.doubao_api_key = assistant.api_key_var.get().strip()
    if not assistant.doubao_api_key:
        from tkinter import messagebox
        messagebox.showwarning("API密钥缺失", "请先设置豆包API密钥")
        return

    # 检查浏览器是否运行
    if not assistant.driver or not hasattr(assistant.driver, 'session_id'):
        from tkinter import messagebox
        messagebox.showwarning("浏览器未运行", "浏览器未正确启动，请点击'启动浏览器'按钮")
        return

    # 在新线程中运行自动化流程
    assistant.auto_button.config(state='disabled')
    assistant.test_button.config(state='disabled')
    assistant.launch_button.config(state='disabled')
    threading.Thread(target=full_auto_process, args=(assistant,), daemon=True).start()


def get_page_html(assistant):
    """获取当前浏览器页面的HTML源码"""
    try:
        if assistant.driver:
            assistant.write_log("正在获取页面源码...")
            html_content = assistant.driver.page_source
            assistant.write_log("页面源码获取成功")
            return html_content
        else:
            assistant.write_log("浏览器未连接，无法获取源码")
            return None
    except Exception as e:
        assistant.write_log(f"获取页面源码失败: {str(e)}")
        return None


def full_auto_process(assistant):
    """全自动化流程：获取题目->生成答案->填写答案"""
    try:
        # 1. 获取页面HTML源码
        assistant.write_log("正在获取考试页面内容...")
        html_content = get_page_html(assistant)
        if not html_content:
            assistant.write_log("❌ 无法获取页面源码，流程终止")
            return

        # 2. 解析页面题目
        assistant.write_log("解析页面题目...")

        # 使用lxml解析HTML
        tree = html.fromstring(html_content)

        # 构建题目文本
        question_text = ""
        current_question = 0

        # 查找题目和选项
        question_elements = tree.xpath('//div[@class="t-subject t-item moso-text moso-editor"]')
        option_elements = tree.xpath('//div[@class="t-option t-item"]')

        if not question_elements:
            assistant.write_log("❌ 未找到题目元素，请确认是否在答题页面")
            return

        # 构建题目文本
        for element in tree.xpath(
                '//div[@class="t-subject t-item moso-text moso-editor"] | //div[@class="t-option t-item"]'):
            if element.get('class') == 't-subject t-item moso-text moso-editor':
                current_question += 1
                question_text += f"\n题目 {current_question}:\n"
                question_text += element.text_content().strip() + "\n"
                question_text += "选项:\n"
            elif element.get('class') == 't-option t-item':
                option_text = element.text_content().strip()
                option_text = re.sub(r'^[A-Za-z0-9]+\.\s*', '', option_text)
                question_text += f"   {option_text}\n"

        assistant.write_log(f"✅ 成功提取 {current_question} 道题目")

        # 3. 调用豆包API获取答案
        assistant.write_log("正在请求豆包AI解答题目...")
        doubao_response = call_doubao_api(assistant, question_text)

        if doubao_response:
            # 4. 解析豆包API的响应
            formatted_answers, answer_dict = parse_doubao_response(assistant, doubao_response)
            assistant.write_log("\n豆包AI提供的答案:\n" + formatted_answers)

            # 5. 自动填写答案到考试页面
            assistant.write_log("\n开始自动填写答案...")
            auto_answer_process(assistant, answer_dict)
        else:
            assistant.write_log("❌ 无法获取豆包AI的答案，流程终止")

    except Exception as e:
        assistant.write_log(f"❌ 全自动化流程出错: {str(e)}")
    finally:
        assistant.auto_button.config(state='normal')
        assistant.test_button.config(state='normal')
        assistant.launch_button.config(state='normal')


def auto_answer_process(assistant, answers):
    """执行自动答题的实际过程"""
    try:
        # 配置优化
        select_config = {letter: idx for idx, letter in enumerate('ABCDEFGHabcdefgh')}
        wait = WebDriverWait(assistant.driver, 10)  # 全局显式等待

        # 高效获取所有题目
        question_elements = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@class="t-con"]'))
        )
        assistant.write_log(f"🔍 找到 {len(question_elements)} 道题目")

        # 批量滚动到可视区域
        assistant.driver.execute_script("""
            const questions = document.querySelectorAll('div.t-con');
            questions.forEach(q => q.scrollIntoView({behavior: 'auto', block: 'center'}));
        """)
        time.sleep(1)  # 等待滚动完成

        # 核心答题逻辑
        start_time = time.time()
        processed = 0

        for q_index, question in enumerate(question_elements, 1):
            if q_index in answers:
                try:
                    # 滚动到题目位置
                    assistant.driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});",
                                                   question)
                    time.sleep(0.1)

                    # 获取题型
                    type_element = question.find_element(By.XPATH, './/div[contains(@class, "t-type")]')
                    question_type = type_element.text
                    answer_str = answers[q_index]

                    # 处理选择题
                    if "单选题" in question_type or "多选题" in question_type:
                        # 解析答案
                        answer_list = re.split(r'[,\s;，；]+', answer_str)
                        answer_list = [a.upper() for a in answer_list if a]

                        # 获取选项
                        options = question.find_elements(By.XPATH, './/div[@class="t-option t-item"]//label')

                        # 选择答案
                        for answer in answer_list:
                            opt_index = select_config.get(answer)
                            if opt_index is not None and opt_index < len(options):
                                option = options[opt_index]
                                input_element = option.find_element(By.TAG_NAME, 'input')
                                assistant.driver.execute_script("arguments[0].click();", input_element)
                                assistant.write_log(f"  已选择 {answer}")

                        processed += 1
                        assistant.write_log(f"✅ 已处理第 {q_index} 题 {'(多选)' if '多选' in question_type else ''}")

                    # 处理填空题
                    elif "填空题" in question_type:
                        # 分割多个填空的答案
                        blank_answers = re.split(r'[;；]', answer_str)
                        blank_answers = [ans.strip() for ans in blank_answers if ans.strip()]

                        # 获取填空输入框
                        blank_inputs = question.find_elements(By.XPATH, './/div[@class="blank-item"]//input')

                        # 填写答案
                        for idx, blank_input in enumerate(blank_inputs):
                            if idx < len(blank_answers):
                                assistant.driver.execute_script("arguments[0].value = '';", blank_input)
                                blank_input.send_keys(blank_answers[idx])
                                assistant.write_log(f"  已填写: {blank_answers[idx]}")

                        processed += 1
                        assistant.write_log(f"✅ 已处理第 {q_index} 题 填空题")

                    # 处理判断题
                    elif "判断题" in question_type:
                        # 获取选项
                        options = question.find_elements(By.XPATH, './/div[@class="t-judge t-item"]//label')

                        # 根据答案选择
                        if "正确" in answer_str and len(options) > 0:
                            input_element = options[0].find_element(By.TAG_NAME, 'input')
                            assistant.driver.execute_script("arguments[0].click();", input_element)
                            assistant.write_log(f"  已选择: 正确")
                        elif "错误" in answer_str and len(options) > 1:
                            input_element = options[1].find_element(By.TAG_NAME, 'input')
                            assistant.driver.execute_script("arguments[0].click();", input_element)
                            assistant.write_log(f"  已选择: 错误")
                        else:
                            assistant.write_log(f"⚠️ 第 {q_index} 题判断题答案无法识别: {answer_str}")
                            continue

                        processed += 1
                        assistant.write_log(f"✅ 已处理第 {q_index} 题 判断题")

                except Exception as e:
                    assistant.write_log(f"❌ 第 {q_index} 题处理失败: {str(e)[:50]}")

        # 性能报告
        total_time = time.time() - start_time
        assistant.write_log(f"\n🎉 处理完成! 共处理 {processed} 道题")
        assistant.write_log(f"⏱️ 总耗时: {total_time:.1f}秒, 平均每题: {total_time / max(1, processed):.2f}秒")

        # 提示用户检查答案
        assistant.write_log("\n⚠️ 请检查答案是否正确，确认无误后提交试卷")

    except Exception as e:
        assistant.write_log(f"❌ 自动答题过程中出错: {str(e)}")
    finally:
        assistant.auto_button.config(state='normal')
        assistant.test_button.config(state='normal')
        assistant.launch_button.config(state='normal')