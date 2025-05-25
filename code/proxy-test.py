import requests
import yaml
import time # 用于记录测试耗时、添加延时（如果需要）
import concurrent.futures # 用于并发测试

# 安装 SOCKS 扩展 (如果尚未安装): pip install requests[socks]
try:
    import socks # 检查 PySocks 是否可用
except ImportError:
    print("错误: PySocks 模块未找到。SOCKS5 代理测试将不可用。")
    print("请运行 'pip install requests[socks]' 或 'pip install PySocks' 来安装。")
    exit()

# 配置文件的 URL
CONFIG_URL = "https://sub.zhou12203.top/bkwzsyzy/download/collection/second?target=ClashMeta"
# 输出文件的名称
OUTPUT_FILE = "available_tested_proxies.txt"

# 测试用的 URL (选择一个高可用的、轻量级的网站)

# 推荐使用国内可访问的测试网站
#TEST_URL_HTTP = "http://detectportal.firefox.com/success.txt"
# TEST_URL_HTTPS = "https://www.baidu.com"
# 你也可以切换为 ip-api.com/json 但注意有频率限制
TEST_URL_HTTP = "http://ip-api.com/json"
TEST_URL_HTTPS = "https://ip-api.com/json"


# 代理测试超时时间 (秒)
PROXY_TEST_TIMEOUT = 8 # 稍微降低超时以加快测试，但太低可能误判
# 最大并发测试线程数
MAX_WORKERS = 5  # 根据你的网络和CPU调整，太高可能导致本地资源耗尽或被目标测试网站限制

def test_proxy(proxy_info, test_id):
    """
    测试单个代理节点的连通性。
    proxy_info: 包含代理详细信息的字典。
    test_id: 用于日志追踪的测试编号。
    返回: 如果代理可用则返回 proxy_info，否则返回 None。
    """
    proxy_type = proxy_info.get("type", "").lower()
    server = proxy_info.get("server")
    port = proxy_info.get("port")
    tls_enabled = proxy_info.get("tls", False) # 默认为 False

    # 基本信息检查
    if not server or not port:
        # print(f"  [{test_id:03d}][测试失败] 节点信息不完整: {proxy_info.get('name')}")
        return None

    proxies_dict = {}
    # 优先使用 HTTPS 测试URL，如果代理支持 (SOCKS5 或 HTTP/TLS)
    # 否则使用 HTTP 测试URL
    test_url = TEST_URL_HTTPS if proxy_type == "socks5" or (proxy_type == "http" and tls_enabled) else TEST_URL_HTTP

    # 构建 requests 需要的 proxies 字典
    if proxy_type == "http":
        # 对于 type: http, tls: true (HTTPS proxy), requests 使用 http://<host>:<port> 作为 https_proxy
        # 对于 type: http (普通 HTTP proxy), requests 使用 http://<host>:<port> 作为 http_proxy
        # 为了通用性，我们都设置，让 requests 自行选择
        proxy_address = f"http://{server}:{port}"
        proxies_dict = {"http": proxy_address, "https": proxy_address}
    elif proxy_type == "socks5":
        # `socks5h://` 会让代理服务器执行DNS解析
        proxy_address = f"socks5h://{server}:{port}"
        proxies_dict = {"http": proxy_address, "https": proxy_address}
    else:
        # print(f"  [{test_id:03d}][测试跳过] 不支持的代理类型: {proxy_type} for node {proxy_info.get('name')}")
        return None

    # print(f"  [{test_id:03d}] 正在测试: {proxy_info.get('name')} ({proxy_type}://{server}:{port}) -> {test_url} ...")
    log_prefix = f"  [{test_id:03d}][{proxy_info.get('name', 'Unknown')[:20]}]" # 限制名称长度
    start_time = time.time()
    try:
        # 增加 headers 模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # 对于可信的测试URL，verify=True 是默认且推荐的。
        # 如果测试URL是自签名等，可以考虑 verify=False，但会降低安全性。
        response = requests.get(test_url, proxies=proxies_dict, timeout=PROXY_TEST_TIMEOUT, headers=headers, verify=True)
        response.raise_for_status()  # 检查 HTTP 错误 (4xx or 5xx)
        elapsed_time = time.time() - start_time
        
        # 可选：检查响应内容判断是否真的通过代理
        ip_info = ""
        if "ip-api.com" in test_url:
            try:
                data = response.json()
                country = data.get("country", "N/A")
                query_ip = data.get("query", "N/A")
                ip_info = f" (出口: {query_ip} [{country}])"
            except requests.exceptions.JSONDecodeError:
                ip_info = " (响应非JSON)" # 可能代理返回了错误页面

        print(f"{log_prefix} [成功] 耗时: {elapsed_time:.2f}s{ip_info}")
        proxy_info['latency_ms'] = round(elapsed_time * 1000) # 添加延迟信息
        return proxy_info
    except requests.exceptions.ProxyError as e:
        print(f"{log_prefix} [失败] 代理错误: {type(e).__name__} - {e}")
    except requests.exceptions.ConnectTimeout as e:
        print(f"{log_prefix} [失败] 连接超时: {type(e).__name__} - {e}")
    except requests.exceptions.ReadTimeout as e:
        print(f"{log_prefix} [失败] 读取超时: {type(e).__name__} - {e}")
    except requests.exceptions.SSLError as e:
        print(f"{log_prefix} [失败] SSL错误: {type(e).__name__} - {e}")
    except requests.exceptions.RequestException as e:
        print(f"{log_prefix} [失败] 请求异常: {type(e).__name__} - {e}")
    except Exception as e: # 捕获其他潜在错误
        print(f"{log_prefix} [失败] 未知错误: {type(e).__name__} - {e}")
    
    # 如果测试失败，则打印失败信息
    return None


def fetch_filter_and_test_proxies(url, output_file):
    """
    下载、筛选 (无密码的 http/socks5) 并并发测试代理，保存可用节点。
    """
    print(f"1. 正在从 {url} 下载配置文件...")
    try:
        req_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=req_headers)
        response.raise_for_status()
        print("   下载成功。")
    except requests.exceptions.RequestException as e:
        print(f"   错误: 下载配置文件失败 - {e}")
        return

    try:
        config_data = yaml.safe_load(response.text)
        print("   YAML 解析成功。")
    except yaml.YAMLError as e:
        print(f"   错误: 解析 YAML 内容失败 - {e}")
        return

    if not isinstance(config_data, dict) or "proxies" not in config_data:
        print("   错误: 配置文件格式不正确，未找到 'proxies' 列表。")
        return

    all_proxies_raw = config_data.get("proxies", [])
    if not isinstance(all_proxies_raw, list):
        print("   错误: 'proxies' 字段不是一个列表。")
        return

    print(f"   共找到 {len(all_proxies_raw)} 个原始代理节点。")

    print("\n2. 筛选无需密码的 http/socks5 节点...")
    candidate_proxies = []
    for proxy_dict in all_proxies_raw:
        if not isinstance(proxy_dict, dict):
            continue

        proxy_type = proxy_dict.get("type", "").lower()
        if proxy_type not in ["http", "socks5"]:
            continue

        # 检查是否存在用户名或密码字段，并且它们不是空字符串或None
        # 有些配置可能 username: "" 或 password: ""
        has_auth = bool(proxy_dict.get("username")) or bool(proxy_dict.get("password"))
        if has_auth:
            continue
        
        # 确保核心字段存在
        if not proxy_dict.get("server") or not proxy_dict.get("port"):
            continue

        node_info = {
            "name": proxy_dict.get("name", "Unnamed Node"),
            "type": proxy_dict.get("type"), # 保留原始大小写
            "server": proxy_dict.get("server"),
            "port": proxy_dict.get("port"),
            "tls": proxy_dict.get("tls", False), # 默认为 False
        }
        if proxy_dict.get("sni"):
            node_info["sni"] = proxy_dict.get("sni")
        
        candidate_proxies.append(node_info)

    print(f"   筛选出 {len(candidate_proxies)} 个候选节点。")

    if not candidate_proxies:
        print("   没有符合初步筛选条件的候选节点。")
        return

    print(f"\n3. 开始并发测试 {len(candidate_proxies)} 个候选节点 (使用 {MAX_WORKERS} 个工作线程)...")
    available_proxies = []
    
    # 使用 ThreadPoolExecutor 进行并发测试
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 为每个任务分配一个唯一的ID，方便追踪
        future_to_proxy = {
            executor.submit(test_proxy, proxy_info, i+1): proxy_info 
            for i, proxy_info in enumerate(candidate_proxies)
        }
        
        completed_count = 0
        for future in concurrent.futures.as_completed(future_to_proxy):
            completed_count += 1
            result_proxy_info = future.result() # 获取 test_proxy 的返回结果
            if result_proxy_info:
                available_proxies.append(result_proxy_info)
            
            # 打印进度条式信息
            progress = completed_count / len(candidate_proxies) * 100
            print(f"\r   测试进度: {completed_count}/{len(candidate_proxies)} ({progress:.1f}%) - 当前可用: {len(available_proxies)}", end="")

    print("\n   测试完成。") # 清除进度条残留

    # 按延迟排序 (可选)
    if available_proxies:
        available_proxies.sort(key=lambda p: p.get('latency_ms', float('inf')))


    print(f"\n4. 共找到 {len(available_proxies)} 个可用的公共代理节点。")

    if not available_proxies:
        print("   没有测试通过的可用公共代理节点，不创建输出文件。")
        return

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 可用公共代理节点列表 (共 {len(available_proxies)} 个)\n")
            f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
            f.write(f"# 订阅源: {url}\n")
            f.write(f"# 测试目标: HTTP='{TEST_URL_HTTP}', HTTPS='{TEST_URL_HTTPS}'\n")
            f.write(f"# 测试超时: {PROXY_TEST_TIMEOUT} 秒\n")
            f.write(f"# 并发数: {MAX_WORKERS}\n")
            f.write("\n")

            for i, node in enumerate(available_proxies):
                f.write(f"--- [可用节点 {i+1:03d}] ---\n")
                f.write(f"  名称 (Name)    : {node.get('name', 'N/A')}\n")
                f.write(f"  类型 (Type)    : {node.get('type', 'N/A')}\n")
                f.write(f"  服务器 (Server) : {node.get('server', 'N/A')}\n")
                f.write(f"  端口 (Port)    : {node.get('port', 'N/A')}\n")
                
                latency = node.get('latency_ms')
                if latency is not None:
                     f.write(f"  延迟 (Latency) : {latency} ms\n")

                tls_status = node.get('tls')
                if tls_status is True:
                    f.write(f"  TLS          : 是 (True)\n")
                elif tls_status is False:
                    f.write(f"  TLS          : 否 (False)\n")
                else:
                    f.write(f"  TLS          : 未指定 (视为否)\n")

                if 'sni' in node and node['sni']:
                    f.write(f"  SNI          : {node['sni']}\n")
                f.write("\n")

        print(f"\n5. 可用的公共代理节点信息已保存到: {output_file}")
    except IOError as e:
        print(f"   错误: 写入文件 {output_file} 失败 - {e}")
    except Exception as e:
        print(f"   错误: 保存文件时发生未知错误 - {e}")

if __name__ == "__main__":
    start_total_time = time.time()
    fetch_filter_and_test_proxies(CONFIG_URL, OUTPUT_FILE)
    end_total_time = time.time()
    print(f"\n总耗时: {end_total_time - start_total_time:.2f} 秒")

