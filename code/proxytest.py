import yaml
import socket
import time
import subprocess
import os
import signal
import tempfile
import json
import requests
import shutil
import random
import threading
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from urllib.parse import urlparse
import base64
import ipaddress
import geoip2.database

# --- 配置 ---
V2RAY_CORE_EXECUTABLE = r"D:\v2rayN-windows-64\bin\xray\xray.exe" # 请确保这是你 v2ray.exe 的正确路径
# 确保此文件有执行权限

TEST_URL = "https://www.google.com/"  # 使用更稳定的URL
TCP_TIMEOUT = 2
URL_TEST_TIMEOUT = 30  # 增加超时时间
V2RAY_LOCAL_SOCKS_PORT =  10808
MAX_TCP_LATENCY = 1500
MAX_URL_LATENCY = 30000

# ... (clash_proxy_to_v2ray_outbound, url_test_with_v2ray, tcp_ping 函数保持不变) ...
# --- 辅助函数 (tcp_ping, clash_proxy_to_v2ray_outbound, url_test_with_v2ray) 保持不变 ---
def tcp_ping(host, port, timeout=TCP_TIMEOUT):
    """测试TCP连接并返回延迟(ms)或None"""
    try:
        ip_address = socket.gethostbyname(host)
    except socket.gaierror:
        return None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start_time = time.time()
        sock.connect((ip_address, port))
        end_time = time.time()
        sock.close()
        return (end_time - start_time) * 1000
    except (socket.timeout, ConnectionRefusedError, socket.gaierror, OSError):
        return None

def clash_proxy_to_v2ray_outbound(clash_proxy):
    v2ray_outbound = {"protocol": "", "settings": {}, "streamSettings": {}}
    proxy_type = clash_proxy.get("type")
    server = clash_proxy.get("server")
    port = int(clash_proxy.get("port", 0))
    uuid = clash_proxy.get("uuid")
    password = clash_proxy.get("password")

    if not server or not port: return None

    if proxy_type == "vless":
        v2ray_outbound["protocol"] = "vless"
        v2ray_outbound["settings"]["vnext"] = [{"address": server, "port": port, "users": [{"id": uuid, "flow": clash_proxy.get("flow", "")}]}]
        network = clash_proxy.get("network", "tcp")
        v2ray_outbound["streamSettings"]["network"] = network
        if clash_proxy.get("tls"):
            v2ray_outbound["streamSettings"]["security"] = "tls"
            tls_settings = {"allowInsecure": clash_proxy.get("skip-cert-verify", False)}
            if "servername" in clash_proxy: tls_settings["serverName"] = clash_proxy["servername"]
            if "alpn" in clash_proxy and isinstance(clash_proxy["alpn"], list): tls_settings["alpn"] = clash_proxy["alpn"]
            v2ray_outbound["streamSettings"]["tlsSettings"] = tls_settings
        elif clash_proxy.get("reality-opts"):
            v2ray_outbound["streamSettings"]["security"] = "reality"
            reality_settings = {
                "show": False,
                "publicKey": clash_proxy["reality-opts"].get("public-key"),
                "shortId": clash_proxy["reality-opts"].get("short-id", ""),
                "serverName": clash_proxy.get("servername")
            }
            if "fingerprint" in clash_proxy["reality-opts"]: reality_settings["fingerprint"] = clash_proxy["reality-opts"].get("fingerprint", "chrome")
            if "spiderX" in clash_proxy["reality-opts"]: reality_settings["spiderX"] = clash_proxy["reality-opts"].get("spiderX","")
            v2ray_outbound["streamSettings"]["realitySettings"] = reality_settings
        if network == "ws":
            ws_opts = clash_proxy.get("ws-opts", {})
            v2ray_outbound["streamSettings"]["wsSettings"] = {"path": ws_opts.get("path", "/"), "headers": ws_opts.get("headers", {})}
        return v2ray_outbound
    elif proxy_type == "vmess":
        v2ray_outbound["protocol"] = "vmess"
        v2ray_outbound["settings"]["vnext"] = [{"address": server, "port": port, "users": [{"id": uuid, "alterId": int(clash_proxy.get("alterId", 0)), "security": clash_proxy.get("cipher", "auto")}]}]
        network = clash_proxy.get("network", "tcp")
        v2ray_outbound["streamSettings"]["network"] = network
        if clash_proxy.get("tls"):
            v2ray_outbound["streamSettings"]["security"] = "tls"
            tls_settings = {"allowInsecure": clash_proxy.get("skip-cert-verify", False)}
            if "servername" in clash_proxy: tls_settings["serverName"] = clash_proxy["servername"]
            if "alpn" in clash_proxy and isinstance(clash_proxy["alpn"], list): tls_settings["alpn"] = clash_proxy["alpn"]
            v2ray_outbound["streamSettings"]["tlsSettings"] = tls_settings
        if network == "ws":
            ws_opts = clash_proxy.get("ws-opts", {})
            v2ray_outbound["streamSettings"]["wsSettings"] = {"path": ws_opts.get("path", "/"), "headers": ws_opts.get("headers", {})}
        elif network == "http" and "h2-opts" in clash_proxy and clash_proxy.get("tls"):
            v2ray_outbound["streamSettings"]["network"] = "h2"
            v2ray_outbound["streamSettings"]["security"] = "tls"
            h2_opts = clash_proxy.get("h2-opts", {})
            v2ray_outbound["streamSettings"]["h2Settings"] = {"path": h2_opts.get("path", "/"), "host": [h2_opts.get("host", clash_proxy.get("servername"))]}
            if "tlsSettings" not in v2ray_outbound["streamSettings"]:
                v2ray_outbound["streamSettings"]["tlsSettings"] = {"allowInsecure": clash_proxy.get("skip-cert-verify", False), "serverName": clash_proxy["servername", h2_opts.get("host")]}
        return v2ray_outbound
    elif proxy_type == "trojan":
        v2ray_outbound["protocol"] = "trojan"
        v2ray_outbound["settings"]["servers"] = [{"address": server, "port": port, "password": password}]
        v2ray_outbound["streamSettings"]["network"] = clash_proxy.get("network", "tcp")
        v2ray_outbound["streamSettings"]["security"] = "tls"
        tls_settings = {"allowInsecure": clash_proxy.get("skip-cert-verify", False), "serverName": clash_proxy.get("sni", server)}
        if "alpn" in clash_proxy and isinstance(clash_proxy["alpn"], list): tls_settings["alpn"] = clash_proxy["alpn"]
        v2ray_outbound["streamSettings"]["tlsSettings"] = tls_settings
        if v2ray_outbound["streamSettings"]["network"] == "ws":
            ws_opts = clash_proxy.get("ws-opts", {})
            v2ray_outbound["streamSettings"]["wsSettings"] = {"path": ws_opts.get("path", "/"), "headers": ws_opts.get("headers", {})}
        return v2ray_outbound
    elif proxy_type == "ss":
        v2ray_outbound["protocol"] = "shadowsocks"
        v2ray_outbound["settings"]["servers"] = [{"address": server, "port": port, "method": clash_proxy.get("cipher"), "password": password}]
        v2ray_outbound["streamSettings"]["network"] = "tcp"
        return v2ray_outbound
    elif proxy_type == "socks5":
        v2ray_outbound["protocol"] = "socks"
        v2ray_outbound["settings"]["servers"] = [{"address": server, "port": port}]
        if "username" in clash_proxy and "password" in clash_proxy:
            v2ray_outbound["settings"]["servers"][0]["users"] = [{"user": clash_proxy["username"], "pass": clash_proxy["password"]}]
        return v2ray_outbound
    elif proxy_type == "http":
        v2ray_outbound["protocol"] = "http"
        v2ray_outbound["settings"]["servers"] = [{"address": server, "port": port}]
        if "username" in clash_proxy and "password" in clash_proxy:
             v2ray_outbound["settings"]["servers"][0]["users"] = [{"user": clash_proxy["username"], "pass": clash_proxy["password"]}]
        if clash_proxy.get("tls"):
            v2ray_outbound["streamSettings"]["security"] = "tls"
            v2ray_outbound["streamSettings"]["tlsSettings"] = {"allowInsecure": clash_proxy.get("skip-cert-verify", False), "serverName": clash_proxy.get("servername", server)}
        return v2ray_outbound
    elif proxy_type in ["hysteria", "hysteria2", "tuic"]:
        # print(f"    Skipping V2Ray conversion for unsupported type: {proxy_type}")
        return None
    else:
        # print(f"    Unsupported proxy type for V2Ray conversion: {proxy_type}")
        return None

def url_test_with_v2ray(clash_proxy_config, v2ray_executable, test_url, v2ray_socks_port, timeout=URL_TEST_TIMEOUT):
    v2ray_outbound_config = clash_proxy_to_v2ray_outbound(clash_proxy_config)
    if not v2ray_outbound_config: return None

    proxy_name = clash_proxy_config.get("name", "UnnamedProxy")
    temp_dir = tempfile.mkdtemp()
    v2ray_config_path = os.path.join(temp_dir, "v2ray_config.json")

    v2ray_client_config = {
        "log": {"loglevel": "warning"},
        "inbounds": [{"listen": "127.0.0.1", "port": v2ray_socks_port, "protocol": "socks", "settings": {"auth": "noauth", "udp": True, "ip": "127.0.0.1"}}],
        "outbounds": [v2ray_outbound_config, {"protocol": "freedom", "tag": "direct"}]
    }
    with open(v2ray_config_path, "w", encoding="utf-8") as f: json.dump(v2ray_client_config, f, indent=2)

    process = None
    try:
        cmd = [v2ray_executable, "run", "-c", v2ray_config_path]
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 增加端口等待时间
        for _ in range(50):  # 增加到5秒
            try:
                with socket.create_connection(("127.0.0.1", v2ray_socks_port), timeout=0.1):
                    break
            except Exception:
                time.sleep(0.1)
        else:
            return None

        proxies = {"http": f"socks5h://127.0.0.1:{v2ray_socks_port}", "https": f"socks5h://127.0.0.1:{v2ray_socks_port}"}
        start_time = time.time()
        try:
            # 添加重试机制
            for _ in range(2):  # 最多重试2次
                try:
                    response = requests.get(test_url, proxies=proxies, timeout=timeout)
                    end_time = time.time()
                    if 200 <= response.status_code < 300:
                        return (end_time - start_time) * 1000
                    time.sleep(1)  # 失败后等待1秒再重试
                except requests.exceptions.RequestException:
                    time.sleep(1)  # 失败后等待1秒再重试
            return None
        except requests.exceptions.RequestException:
            return None
    except Exception:
        return None
    finally:
        if process:
            process.terminate()
            try: 
                process.wait(timeout=5)
            except subprocess.TimeoutExpired: 
                process.kill()
                process.wait()
        shutil.rmtree(temp_dir, ignore_errors=True)

def url_test_worker(proxy, v2ray_executable, test_url, local_port, timeout=15, progress=None):
    """URL测试工作线程函数"""
    name = proxy["name"]
    if progress:
        print(f"URL测试中 ({progress}): {name}")
    else:
        print(f"URL测试中: {name}")
    
    url_latency = url_test_with_v2ray(proxy, v2ray_executable, test_url, local_port, timeout)
    if url_latency is not None:
        print(f"  URL Test (V2Ray): {url_latency:.2f} ms")
        if url_latency <= MAX_URL_LATENCY:
            proxy["url_latency"] = f"{url_latency:.0f}ms"
            print(f"  URL测试通过")
            return proxy
        else:
            print(f"  URL测试失败: 延迟 > {MAX_URL_LATENCY} ms")
    else:
        print(f"  URL测试失败: 无法连接或超时")
    print("-" * 30)
    return None

def download_subscription(url):
    """从远程URL下载订阅内容"""
    try:
        # 添加请求头，模拟浏览器行为
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # 检查响应状态
        
        # 检查内容类型
        content_type = response.headers.get('content-type', '').lower()
        
        # 处理base64编码的内容
        if 'base64' in content_type or url.endswith('.txt'):
            try:
                content = base64.b64decode(response.text).decode('utf-8')
            except:
                content = response.text
        else:
            content = response.text
            
        return content
    except Exception as e:
        print(f"下载订阅失败 ({url}): {str(e)}")
        return None

def is_url(string):
    """检查字符串是否是URL"""
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except:
        return False

def load_rename_rules(rename_file):
    """加载重命名规则"""
    try:
        # 默认路径
        default_path = r"C:\Users\30752\Desktop\guest\edit\sub\config\rename.yaml"
        
        # 如果未指定rename文件，使用默认路径
        if not rename_file:
            rename_file = default_path
            
        # 检查是否是URL
        if is_url(rename_file):
            try:
                # 添加请求头，模拟浏览器行为
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(rename_file, headers=headers, timeout=30)
                response.raise_for_status()
                return yaml.safe_load(response.text)
            except Exception as e:
                print(f"从远程加载重命名规则失败: {e}")
                return []
        
        # 处理本地文件
        # 尝试直接使用提供的路径
        if os.path.exists(rename_file):
            try:
                with open(rename_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"读取重命名规则文件失败: {e}")
        
        # 如果直接路径失败，尝试在脚本目录下查找
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_path = os.path.join(script_dir, 'rename.yaml')
        if os.path.exists(local_path):
            try:
                with open(local_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"读取本地重命名规则文件失败: {e}")
        
        # 如果都失败了，尝试使用默认路径
        if os.path.exists(default_path):
            try:
                with open(default_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"读取默认重命名规则文件失败: {e}")
        
        print("警告: 未找到重命名规则文件")
        return []
        
    except Exception as e:
        print(f"加载重命名规则失败: {e}")
        return []

def get_ip_location_api(ip):
    """使用在线API获取IP地理位置信息"""
    try:
        # 使用免费的ip-api.com服务
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return data.get('countryCode')
    except:
        pass
    return None

def get_ip_location(ip):
    """获取IP地址的地理位置信息"""
    try:
        # 首先尝试使用本地数据库
        if os.path.exists('GeoLite2-Country.mmdb'):
            reader = geoip2.database.Reader('GeoLite2-Country.mmdb')
            response = reader.country(ip)
            country_code = response.country.iso_code
            reader.close()
            return country_code
    except Exception as e:
        print(f"本地数据库查询失败: {e}")
    
    # 如果本地数据库不可用，使用在线API
    return get_ip_location_api(ip)

def get_country_name_from_ip(server):
    """从服务器地址获取国家代码"""
    try:
        # 尝试解析域名
        ip = socket.gethostbyname(server)
        return get_ip_location(ip)
    except:
        return None

def rename_proxy(proxy_name, rename_rules, server=None):
    """根据规则重命名代理节点"""
    # 提取速度信息
    speed_match = re.search(r'⬇️\s*([\d.]+)\s*MB/s', proxy_name)
    speed_info = speed_match.group(1) if speed_match else ""
    
    # 用于跟踪每个地区的节点数量
    if not hasattr(rename_proxy, 'country_counters'):
        rename_proxy.country_counters = {}
    
    # 首先尝试使用正则表达式匹配
    for rule in rename_rules:
        if re.search(rule['recognition'], proxy_name):
            # 如果是中国节点，返回None表示需要排除
            if 'CN' in rule['name']:
                return None
            # 获取地区名称
            country_name = rule['name']
            # 更新计数器
            if country_name not in rename_proxy.country_counters:
                rename_proxy.country_counters[country_name] = 1
            else:
                rename_proxy.country_counters[country_name] += 1
            # 构建新名称
            new_name = f"{country_name}{rename_proxy.country_counters[country_name]} | {speed_info}MB/s"
            return new_name
    
    # 如果正则匹配失败，尝试通过IP获取地理位置
    if server:
        country_code = get_country_name_from_ip(server)
        if country_code:
            # 如果是中国节点，返回None表示需要排除
            if country_code == 'CN':
                return None
            # 更新计数器
            if country_code not in rename_proxy.country_counters:
                rename_proxy.country_counters[country_code] = 1
            else:
                rename_proxy.country_counters[country_code] += 1
            # 构建新名称
            new_name = f"{country_code}{rename_proxy.country_counters[country_code]} | {speed_info}MB/s"
            return new_name
    
    # 如果都失败了，返回原始名称
    return proxy_name

def remove_duplicate_proxies(proxies):
    """去除重复的代理节点"""
    unique_proxies = {}
    for proxy in proxies:
        if not isinstance(proxy, dict) or 'server' not in proxy or 'port' not in proxy:
            continue
            
        # 创建唯一标识
        key = f"{proxy['server']}:{proxy['port']}"
        
        # 如果节点已存在，保留延迟较低的节点
        if key in unique_proxies:
            existing_proxy = unique_proxies[key]
            # 如果新节点有延迟信息，且比现有节点延迟低，则替换
            if 'tcp_latency' in proxy and 'tcp_latency' in existing_proxy:
                try:
                    new_latency = float(proxy['tcp_latency'].replace('ms', ''))
                    existing_latency = float(existing_proxy['tcp_latency'].replace('ms', ''))
                    if new_latency < existing_latency:
                        unique_proxies[key] = proxy
                except ValueError:
                    pass
        else:
            unique_proxies[key] = proxy
    
    return list(unique_proxies.values())

# --- 主逻辑 ---
def main():
    # 定义默认文件名
    default_output_file = r"C:\Users\30752\Desktop\guest\edit\sub\output\output.yaml"
    
    # 获取用户输入的rename文件路径
    print("请输入重命名规则文件路径（支持本地文件路径或远程URL）：")
    print("示例：")
    print("  https://raw.githubusercontent.com/username/repo/main/rename.yaml")
    print("  C:\\path\\to\\your\\rename.yaml")
    print("  /path/to/your/rename.yaml")
    print("  （直接回车使用默认路径）")
    
    rename_file = input().strip()
    
    # 加载重命名规则
    rename_rules = load_rename_rules(rename_file)
    if not rename_rules:
        print("警告: 未找到重命名规则，将使用原始节点名称")
    
    # 获取用户输入的订阅源
    print("\n请输入订阅源（支持本地文件路径或远程URL，每行一个，输入空行结束）：")
    print("示例：")
    print("  https://example.com/sub")
    print("  C:\\path\\to\\your\\config.yaml")
    print("  （输入空行结束）")
    
    input_sources = []
    while True:
        source = input().strip()
        if not source:
            break
        input_sources.append(source)
    
    if not input_sources:
        print("错误：未提供任何订阅源")
        return
    
    # 获取用户输入的输出文件名
    user_output_file = input(f"请输入筛选后输出的文件名 (默认为: {default_output_file}): ").strip()
    output_yaml_file = user_output_file if user_output_file else default_output_file
    
    # 合并所有代理节点
    all_proxies = []
    for source in input_sources:
        print(f"\n处理订阅源: {source}")
        
        if is_url(source):
            # 处理远程URL
            content = download_subscription(source)
            if content is None:
                print(f"跳过无效的订阅源: {source}")
                continue
            try:
                config_data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                print(f"解析YAML内容失败: {e}")
                continue
        else:
            # 处理本地文件
            if not os.path.exists(source):
                print(f"错误: 文件 '{source}' 未找到")
                continue
            try:
                with open(source, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)
            except Exception as e:
                print(f"读取文件失败: {e}")
                continue
        
        if not isinstance(config_data, dict) or "proxies" not in config_data:
            print(f"错误: 订阅源 '{source}' 格式不正确")
            continue
            
        proxies = config_data.get("proxies", [])
        if not isinstance(proxies, list):
            print(f"错误: 订阅源 '{source}' 中的 'proxies' 必须是一个列表")
            continue
            
        # 为每个代理添加来源标记
        for proxy in proxies:
            if isinstance(proxy, dict):
                proxy["source"] = source
        all_proxies.extend(proxies)
    
    if not all_proxies:
        print("错误：没有找到任何有效的代理节点")
        return
    
    print(f"\n总共找到 {len(all_proxies)} 个代理节点")
    
    # 去除重复节点
    all_proxies = remove_duplicate_proxies(all_proxies)
    print(f"去重后剩余 {len(all_proxies)} 个代理节点")
    
    # 先进行TCP测试
    tcp_passed_proxies = []
    print(f"开始TCP测试 {len(all_proxies)} 个代理节点...\n")

    for i, proxy in enumerate(all_proxies):
        if not isinstance(proxy, dict) or "name" not in proxy or "server" not in proxy or "port" not in proxy:
            print(f"  跳过无效的代理配置: {proxy}")
            continue

        name = proxy["name"]
        server = proxy["server"]
        try:
            port = int(proxy["port"])
        except ValueError:
            print(f"  跳过代理 '{name}' (端口无效: {proxy['port']})")
            continue

        print(f"TCP测试中 ({i+1}/{len(all_proxies)}): {name}")

        # TCPing Test
        tcp_latency = tcp_ping(server, port)
        if tcp_latency is not None:
            print(f"  TCP Ping: {tcp_latency:.2f} ms")
            if tcp_latency <= MAX_TCP_LATENCY:
                proxy["tcp_latency"] = f"{tcp_latency:.0f}ms"
                tcp_passed_proxies.append(proxy)
                print(f"  TCP测试通过")
            else:
                print(f"  TCP测试失败: 延迟 > {MAX_TCP_LATENCY} ms")
        else:
            print(f"  TCP测试失败: 无法连接或超时")
        print("-" * 30)

    print(f"\nTCP测试完成。{len(tcp_passed_proxies)} / {len(all_proxies)} 个代理节点通过TCP测试。")

    # 对通过TCP测试的节点进行URL测试（使用多线程）
    available_proxies = []
    print(f"\n开始URL测试 {len(tcp_passed_proxies)} 个通过TCP测试的节点...\n")
    
    # 创建线程池，设置最大线程数
    max_workers = min(10, len(tcp_passed_proxies))  # 最多10个线程，或节点数量（取较小值）
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 创建任务列表
        future_to_proxy = {}
        for i, proxy in enumerate(tcp_passed_proxies, 1):
            local_port = random.randint(10000, 60000)
            future = executor.submit(
                url_test_worker,
                proxy,
                V2RAY_CORE_EXECUTABLE,
                TEST_URL,
                local_port,
                15,
                f"{i}/{len(tcp_passed_proxies)}"  # 添加进度信息
            )
            future_to_proxy[future] = proxy

        # 处理完成的任务
        completed = 0
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            completed += 1
            try:
                result = future.result()
                if result:
                    available_proxies.append(result)
            except Exception as e:
                print(f"测试节点 '{proxy['name']}' 时发生错误: {e}")
            # 显示总体进度
            print(f"\rURL测试进度: {completed}/{len(tcp_passed_proxies)} 个节点已测试", end="")
        print()  # 换行

    print(f"\n测试完成。{len(available_proxies)} / {len(all_proxies)} 个代理节点完全可用。")

    # 在保存配置之前重命名节点
    renamed_proxies = []
    for proxy in available_proxies:
        if 'name' in proxy and 'server' in proxy:
            new_name = rename_proxy(proxy['name'], rename_rules, proxy['server'])
            if new_name is not None:  # 排除中国节点
                proxy['name'] = new_name
                renamed_proxies.append(proxy)
    
    # 更新配置文件
    config_data["proxies"] = renamed_proxies
    try:
        with open(output_yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True, sort_keys=False, indent=2)
        print(f"筛选后的配置已保存到 '{output_yaml_file}'")
    except IOError as e:
        print(f"写入输出文件错误: {e}")
    except Exception as e:
        print(f"保存文件时发生未知错误: {e}")

if __name__ == "__main__":
    # 确保 V2Ray 可执行文件存在且可执行
    # shutil.which 检查命令是否在 PATH 中或者是否是可执行文件的绝对/相对路径
    v2ray_exe_to_check = V2RAY_CORE_EXECUTABLE.split()[0] # 如果路径包含参数，只检查命令本身
    if not os.path.isfile(v2ray_exe_to_check) and not shutil.which(v2ray_exe_to_check):
        print(f"错误: V2Ray 可执行文件 '{V2RAY_CORE_EXECUTABLE}' 未找到或不在 PATH 中。")
        print("请检查 V2RAY_CORE_EXECUTABLE 的路径设置是否正确，或将 v2ray.exe 所在目录添加到系统 PATH。")
    else:
        # 进一步检查可执行权限 (主要对Linux/macOS有意义, Windows上一般存在即可执行)
        if os.name != 'nt' and not os.access(shutil.which(v2ray_exe_to_check) or v2ray_exe_to_check, os.X_OK):
             print(f"错误: V2Ray 可执行文件 '{V2RAY_CORE_EXECUTABLE}' 没有执行权限。")
        else:
            main()
