import requests
import json
import time
from typing import List, Dict, Optional

class APITester:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json"
        }
        
    def test_openai_api(self, api_key: str) -> bool:
        """测试OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "gpt-4.1-mini",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.status_code == 200
        except:
            return False

    def test_gemini_api(self, api_key: str) -> bool:
        """测试Gemini API"""
        url = f"https://gemini12203.deno.dev/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
        data = {
            "contents": [{"parts": [{"text": "Hello"}]}]
        }
        try:
            response = requests.post(url, json=data)
            return response.status_code == 200
        except:
            return False

    def test_openrouter_api(self, api_key: str) -> bool:
        """测试OpenRouter API"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "deepseek/deepseek-r1:free",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.status_code == 200
        except:
            return False

    def test_custom_api(self, api_url: str, api_key: str, model: str) -> bool:
        """测试自定义API"""
        headers = {
            **self.headers,
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}]
        }
        try:
            response = requests.post(api_url, headers=headers, json=data)
            return response.status_code == 200
        except:
            return False

def clean_api_string(api: str) -> str:
    """清理API字符串，去除引号和逗号"""
    return api.strip().strip('"').strip("'").rstrip(',')

def get_api_type_from_user() -> str:
    """让用户选择API类型"""
    print("请选择API类型：")
    print("1. openai (gpt-4.1-mini)")
    print("2. gemini (gemini-2.0-flash-exp)")
    print("3. openrouter (deepseek/deepseek-r1:free)")
    print("4. 自定义 (格式：url|key|model)")
    while True:
        choice = input("请输入类型编号(1-4)：").strip()
        if choice in ['1', '2', '3', '4']:
            return choice
        print("输入有误，请重新输入！")

def get_apis_from_terminal() -> List[str]:
    """从终端获取API列表"""
    print("请输入API列表（每行一个，输入空行结束）：")
    apis = []
    while True:
        line = input().strip()
        if not line:
            break
        apis.append(line)
    return apis

def process_api_list(api_list: List[str], api_type: str) -> List[str]:
    """处理API列表，去除逗号并返回可用的API"""
    tester = APITester()
    available_apis = []
    for api in api_list:
        api = clean_api_string(api)
        if api_type == '1':  # openai
            if tester.test_openai_api(api):
                available_apis.append(api)
        elif api_type == '2':  # gemini
            api_key = api
            if tester.test_gemini_api(api_key):
                available_apis.append(api)
        elif api_type == '3':  # openrouter
            api_key = api
            if tester.test_openrouter_api(api_key):
                available_apis.append(api)
        elif api_type == '4':  # 自定义
            try:
                url, key, model = api.split("|")
                if tester.test_custom_api(url, key, model):
                    available_apis.append(api)
            except:
                continue
    return available_apis

def main():
    api_type = get_api_type_from_user()
    api_list = get_apis_from_terminal()
    print("\n开始测试API可用性...")
    available_apis = process_api_list(api_list, api_type)
    print("\n可用的API列表：")
    for api in available_apis:
        print(api)

if __name__ == "__main__":
    main()
