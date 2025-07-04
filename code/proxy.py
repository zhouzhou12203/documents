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
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

# --- 配置 ---
V2RAY_CORE_EXECUTABLE = r"D:\v2rayN-windows-64\bin\xray\xray.exe" # 请确保这是你 v2ray.exe 的正确路径
# 确保此文件有执行权限

TEST_URL = "https://www.google.com"  # 使用更稳定的URL
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

def url_test_worker(proxy, v2ray_executable, test_url, local_port, timeout=15):
    """URL测试工作线程函数"""
    name = proxy["name"]
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

# --- 主逻辑 ---
def main():
    # 定义默认文件名
    default_input_file = r"C:\Users\30752\Desktop\guest\edit\sub\output\all.yaml"  # 修改为指定的默认输入文件路径
    default_output_file = r"C:\Users\30752\Desktop\guest\edit\sub\output\output.yaml"  # 修改为指定的默认输出文件路径

    # 获取用户输入的输入文件名，如果用户直接回车，则使用默认值
    user_input_file = input(f"请输入Clash订阅文件名 (默认为: {default_input_file}): ").strip()
    input_yaml_file = user_input_file if user_input_file else default_input_file

    # 获取用户输入的输出文件名，如果用户直接回车，则使用默认值
    user_output_file = input(f"请输入筛选后输出的文件名 (默认为: {default_output_file}): ").strip()
    output_yaml_file = user_output_file if user_output_file else default_output_file

    print(f"\n将从 '{input_yaml_file}' 读取节点，筛选结果将保存到 '{output_yaml_file}'.\n")

    if not os.path.exists(input_yaml_file):
        print(f"错误: 输入文件 '{input_yaml_file}' 未找到。请确保文件存在于脚本所在目录或提供完整路径。")
        return

    try:
        with open(input_yaml_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
    except FileNotFoundError: # 这一层检查其实可以省略，因为上面已经用 os.path.exists 检查过了
        print(f"错误: 输入文件 '{input_yaml_file}' 未找到。")
        return
    except yaml.YAMLError as e:
        print(f"解析YAML文件错误: {e}")
        return
    except Exception as e:
        print(f"读取文件时发生未知错误: {e}")
        return

    if not isinstance(config_data, dict) or "proxies" not in config_data:
        print("错误: YAML文件格式不正确，必须是包含 'proxies' 列表的字典。")
        return

    all_proxies = config_data.get("proxies", [])
    if not isinstance(all_proxies, list):
        print("错误: 'proxies' 必须是一个列表。")
        return

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
        for proxy in tcp_passed_proxies:
            local_port = random.randint(10000, 60000)
            future = executor.submit(
                url_test_worker,
                proxy,
                V2RAY_CORE_EXECUTABLE,
                TEST_URL,
                local_port,
                15
            )
            future_to_proxy[future] = proxy

        # 处理完成的任务
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            try:
                result = future.result()
                if result:
                    available_proxies.append(result)
            except Exception as e:
                print(f"测试节点 '{proxy['name']}' 时发生错误: {e}")

    print(f"\n测试完成。{len(available_proxies)} / {len(all_proxies)} 个代理节点完全可用。")

    # 更新配置文件
    config_data["proxies"] = available_proxies
    try:
        with open(output_yaml_file, "w", encoding="utf-8") as f:
            # 使用 allow_unicode=True 保留中文等非ASCII字符, sort_keys=False 保持原有顺序
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
