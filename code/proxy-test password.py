import requests
import yaml # 用于解析 YAML
# import json # json不再直接用于输出整个列表，但可用于单个节点内部处理（如果需要）

# 配置文件的 URL
CONFIG_URL = "https://sub.zhou12203.top/bkwzsyzy/download/collection/total?target=ClashMeta"
# 输出文件的名称
OUTPUT_FILE = "filtered_proxies_formatted.txt" # 新的输出文件名

def fetch_and_filter_proxies(url, output_file):
    """
    从 URL 下载代理配置，筛选出 http 和 socks5 类型的节点，
    并以更美观的格式保存到新文件。
    """
    print(f"正在从 {url} 下载配置文件...")
    try:
        # 添加 headers 模拟浏览器，有些服务器可能需要
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        print("下载成功。")
    except requests.exceptions.Timeout:
        print(f"错误: 请求超时 {url}")
        return
    except requests.exceptions.HTTPError as e:
        print(f"错误: HTTP 请求失败 {url} - {e.response.status_code} {e.response.reason}")
        return
    except requests.exceptions.RequestException as e:
        print(f"错误: 下载配置文件失败 - {e}")
        return

    try:
        config_data = yaml.safe_load(response.text)
        print("YAML 解析成功。")
    except yaml.YAMLError as e:
        print(f"错误: 解析 YAML 内容失败 - {e}")
        return

    if not isinstance(config_data, dict) or "proxies" not in config_data:
        print("错误: 配置文件格式不正确，未找到 'proxies' 列表。")
        if isinstance(config_data, dict):
            print(f"顶层键: {list(config_data.keys())}")
        else:
            print(f"获取到的数据类型: {type(config_data)}")
        return

    all_proxies = config_data.get("proxies", [])
    if not isinstance(all_proxies, list):
        print(f"错误: 'proxies' 字段不是一个列表，而是 {type(all_proxies)}。")
        return

    print(f"共找到 {len(all_proxies)} 个代理节点。")

    filtered_proxies_data = []
    for proxy in all_proxies:
        if not isinstance(proxy, dict):
            print(f"警告: 发现非字典格式的代理项，已跳过: {proxy}")
            continue

        proxy_type = proxy.get("type", "").lower()

        if proxy_type == "http" or proxy_type == "socks5":
            # 提取我们关心的字段，可以按需调整
            node_info = {
                "name": proxy.get("name", "N/A"),
                "type": proxy.get("type", "N/A"), # 保留原始大小写或统一处理
                "server": proxy.get("server", "N/A"),
                "port": proxy.get("port", "N/A"),
                "tls": proxy.get("tls"), # 可能为 None, True, False
            }
            # 可选字段
            if "username" in proxy:
                node_info["username"] = proxy["username"]
            if "password" in proxy:
                node_info["password"] = proxy["password"]
            if "sni" in proxy:
                node_info["sni"] = proxy["sni"]
            # 你可以根据需要添加或移除其他字段，例如 'udp', 'skip-cert-verify' 等
            # if 'udp' in proxy:
            # node_info['udp'] = proxy['udp']

            filtered_proxies_data.append(node_info)

    print(f"筛选出 {len(filtered_proxies_data)} 个 http/socks5 类型的节点。")

    if not filtered_proxies_data:
        print("没有找到符合条件的代理节点，不创建输出文件。")
        return

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, node in enumerate(filtered_proxies_data):
                f.write(f"--- [节点 {i+1:03d}] ---\n") # 给节点编号，用0补齐方便排序
                f.write(f"  名称 (Name)    : {node.get('name', 'N/A')}\n")
                f.write(f"  类型 (Type)    : {node.get('type', 'N/A')}\n")
                f.write(f"  服务器 (Server) : {node.get('server', 'N/A')}\n")
                f.write(f"  端口 (Port)    : {node.get('port', 'N/A')}\n")

                # 处理 tls 字段，使其输出更友好
                tls_status = node.get('tls')
                if tls_status is True:
                    f.write(f"  TLS 加密     : 是 (True)\n")
                elif tls_status is False:
                    f.write(f"  TLS 加密     : 否 (False)\n")
                # else: # tls 字段不存在或为 None
                    # f.write(f"  TLS 加密     : 未指定\n") # 如果需要明确指出未指定

                if 'sni' in node and node['sni']: # 确保 sni 存在且不为空
                    f.write(f"  SNI          : {node['sni']}\n")

                if 'username' in node and node['username']: # 确保 username 存在且不为空
                    f.write(f"  用户名 (User)  : {node['username']}\n")
                if 'password' in node and node['password']: # 确保 password 存在且不为空
                    # 出于安全考虑，你可能不想直接打印密码，或者用星号替代
                    # f.write(f"  密码 (Pass)    : {node['password']}\n")
                    f.write(f"  密码 (Pass)    : [已隐藏]\n") # 或者用占位符

                # 可以添加其他你想显示的字段
                # if 'udp' in node:
                #     f.write(f"  UDP 支持     : {node['udp']}\n")

                f.write("\n") # 每个节点后空一行，增加间距

        print(f"筛选并格式化后的节点信息已保存到: {output_file}")
        print(f"提示: 密码已在输出文件中标记为 [已隐藏]。如果需要显示，请修改脚本。")

    except IOError as e:
        print(f"错误: 写入文件 {output_file} 失败 - {e}")
    except Exception as e:
        print(f"错误: 保存文件时发生未知错误 - {e}")

if __name__ == "__main__":
    fetch_and_filter_proxies(CONFIG_URL, OUTPUT_FILE)
