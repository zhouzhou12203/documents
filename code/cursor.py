import os
import sqlite3
import requests
import base64
import json
from datetime import datetime

def pad_base64(b64_str):
    padding = '=' * (-len(b64_str) % 4)
    return (b64_str + padding).encode('utf-8')

def decode_jwt(token):
    try:
        header_b64, payload_b64, _ = token.split('.')
    except ValueError:
        raise ValueError("无效的 JWT 格式，应包含两处'.'分隔符")
    header = json.loads(base64.urlsafe_b64decode(pad_base64(header_b64)))
    payload = json.loads(base64.urlsafe_b64decode(pad_base64(payload_b64)))
    return header, payload

class CursorClient:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.user_info = None
        self.cookies = None
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'Settings | Cursor - The AI Code Editor',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

    def get_token(self):
        extractor = TokenExtractor()
        self.token = extractor.get_access_token()
        return self.token

    def extract_user_id(self):
        if not self.token:
            return False
        try:
            header, payload = decode_jwt(self.token)
            sub = payload.get('sub')
            if not sub:
                print("警告：无法从token中获取用户ID")
                return False

            exp_ts = payload.get('exp')
            if exp_ts:
                exp_time = datetime.fromtimestamp(int(exp_ts))
                print(f"\nToken过期时间: {exp_time.strftime('%Y-%m-%d %H:%M:%S')}")

            if '|' in sub:
                self.user_id = sub.split('|')[1]
            else:
                self.user_id = sub

            self.cookies = {
                'NEXT_LOCALE': 'cn',
                'WorkosCursorSessionToken': f'{self.user_id}%3A%3A{self.token}',
            }
            return True
        except Exception as e:
            print(f"解析token失败: {e}")
            return False

    def get_user_info(self):
        try:
            response = requests.get(
                'https://www.cursor.com/api/auth/me',
                cookies=self.cookies,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            self.user_info = response.json()

            email = self.user_info.get('email')
            if email:
                print(f"\n用户邮箱: {email}\n")
            else:
                print("\n未找到用户邮箱\n")

            return self.user_info
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}")
            return None
        except json.JSONDecodeError:
            print("返回数据不是有效的JSON格式")
            return None
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            return None

    def get_usage(self, print_details=True):
        try:
            response = requests.get(
                'https://www.cursor.com/api/usage',
                cookies=self.cookies,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if print_details:
                print("\n===== 使用量API返回结果 =====")
                print(json.dumps(data, indent=4, ensure_ascii=False))
                print("==============================\n")

            if 'gpt-4' not in data or 'numRequests' not in data['gpt-4']:
                print("API返回数据结构不符合预期")
                return None

            return data['gpt-4']['numRequests']
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}")
            return None
        except json.JSONDecodeError:
            print("返回数据不是有效的JSON格式")
            return None
        except Exception as e:
            print(f'获取数据失败: {e}')
            return None

class TokenExtractor:
    def __init__(self):
        if os.name == 'nt':
            self.db_path = os.path.join(os.getenv('APPDATA'), 'Cursor', 'User', 'globalStorage', 'state.vscdb')
        else:
            self.db_path = os.path.expanduser('~/Library/Application Support/Cursor/User/globalStorage/state.vscdb')

    def get_access_token(self):
        if not os.path.exists(self.db_path):
            print(f"数据库文件不存在: {self.db_path}")
            return None
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM itemTable WHERE key = 'cursorAuth/accessToken'")
            row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            print(f"数据库错误: {str(e)}")
            return None
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()

def main():
    client = CursorClient()
    # 获取令牌
    if not client.get_token():
        print("无法获取access token")
        return

    # 提取用户ID并设置cookies
    if not client.extract_user_id():
        return

    # 获取用户信息
    if not client.get_user_info():
        print("获取用户信息失败，但将继续尝试获取使用量")

    # 获取使用量
    usage = client.get_usage()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if usage is not None:
        print(f'[{current_time}] Cursor 使用量: {usage}')
    else:
        print(f'[{current_time}] 获取使用量失败')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序发生未预期的错误: {e}")