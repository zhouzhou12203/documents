import subprocess
import json
import os
import requests # 需要安装: pip install requests
import sys
import codecs

# --- 配置 ---
# 你的 OpenAI 兼容 API 的 Base URL
# 例如: "http://localhost:8000/v1" 或 "https://api.openai.com/v1"
BASE_URL = os.environ.get("OPENAI_API_BASE", "https://zhou12203-uni.hf.space/v1")
# 你的 API Key (如果你的服务需要)
# 建议通过环境变量 OPENAI_API_KEY 设置，或者直接在这里填写
API_KEY = os.environ.get("OPENAI_API_KEY", "sk-pkhf60Yfz2GyJxgRmXqFQzouWUd9GZnmi3KlvowmRWpWqrhy")
# 使用的模型名称
MODEL_NAME = "gemini-2.0-flash-exp" # 或者你部署的模型名
# 生成commit message的最大token数
MAX_TOKENS = 60
# 控制输出的随机性
TEMPERATURE = 0.3
# --- END 配置 ---

SYSTEM_PROMPT = """你是一个专业的Git提交信息生成器。
请根据提供的 'git diff --staged' 输出，生成一个简短、清晰且符合 Conventional Commits 规范的提交信息。
规范格式为: <type>(<scope>): <subject>
例如: feat: add new login button
     fix(parser): handle malformed input
     docs: update README with API instructions

- type: feat, fix, docs, style, refactor, perf, test, chore
- scope: 可选，指明影响范围
- subject: 动词开头，现在时态，简洁描述。

只输出最终的commit信息本身，不要包含任何解释、前缀如 "Commit message:" 或 markdown 代码块标记。请使用中文回答
"""

def get_staged_diff():
    """获取 git staged 的 diff 内容"""
    try:
        result = subprocess.run(
            ["git", "diff", "--staged", "--patch", "--unified=0"],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8' # 确保正确处理中文等字符
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"获取 git diff 失败: {e}")
        if e.stderr:
            print(f"Git Stderr: {e.stderr}")
        return None
    except FileNotFoundError:
        print("错误: git 命令未找到。请确保 git 已安装并在 PATH 中。")
        return None

def generate_commit_message(diff_content):
    """调用 AI API 生成 commit message"""
    if not diff_content:
        return "chore: no changes to commit" # 或者返回空，让调用者处理

    if BASE_URL == "YOUR_OPENAI_COMPATIBLE_BASE_URL/v1":
        print("错误：请在脚本中或通过环境变量 OPENAI_API_BASE 设置 BASE_URL。")
        return None

    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }
    if API_KEY and API_KEY != "YOUR_API_KEY":
        headers["Authorization"] = f"Bearer {API_KEY}"
    elif "openai.com" in BASE_URL and (not API_KEY or API_KEY == "YOUR_API_KEY"):
        print("错误：使用 OpenAI 官方 API 时必须提供 API_KEY。")
        return None


    user_prompt = f"请为以下 git diff 内容生成一个 commit message:\n\n```diff\n{diff_content}\n```"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "stream": False
    }

    api_endpoint = f"{BASE_URL.rstrip('/')}/chat/completions"

    try:
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # 如果 HTTP 错误 (4xx or 5xx) 则抛出异常
        
        response_data = response.json()
        
        if "choices" in response_data and len(response_data["choices"]) > 0:
            message_content = response_data["choices"][0].get("message", {}).get("content", "")
            # 清理AI可能添加的多余字符
            message_content = message_content.strip()
            message_content = message_content.removeprefix("```").removesuffix("```")
            message_content = message_content.removeprefix("`").removesuffix("`")
            message_content = message_content.strip('"').strip("'")
            return message_content.strip()
        else:
            print("错误：API 响应中没有找到有效的 'choices'。")
            print("API 原始响应:", response.text)
            return None

    except requests.exceptions.RequestException as e:
        print(f"API 请求失败: {e}")
        return None
    except json.JSONDecodeError:
        print("错误：解析API响应失败，不是有效的JSON。")
        print("API 原始响应:", response.text)
        return None


if __name__ == "__main__":
    if sys.platform.startswith('win'):
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # 设置控制台输出为 UTF-8
        kernel32.SetConsoleCP(65001)        # 设置控制台输入为 UTF-8

    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"
    my_env["LANG"] = "zh_CN.UTF-8"
    my_env["LC_ALL"] = "zh_CN.UTF-8"

    diff = get_staged_diff()
    if diff is None: # 错误已在 get_staged_diff 中打印
        exit(1)
    
    if not diff:
        print("没有暂存的更改可以提交。")
        exit(0) # 正常退出，没有错误

    # 限制diff长度，避免请求体过大或token超限
    max_diff_length = 8000 # 根据模型上下文调整
    if len(diff) > max_diff_length:
        print(f"警告: Diff内容过长 ({len(diff)} characters)，将截断为 {max_diff_length} characters。")
        diff = diff[:max_diff_length] + "\n... (diff truncated)"

    commit_msg = generate_commit_message(diff)

    if commit_msg:
        print(commit_msg)
    else:
        print("未能生成 commit message。请检查错误信息。")
        exit(1)
