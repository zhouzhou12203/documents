import requests
import concurrent.futures
import logging

# 前置代理，默认为空
proxy_url = ""

urls_to_test = [
    "https://raw.githubusercontent.com/firefoxmmx2/v2rayshare_subcription/main/subscription/clash_sub.yaml",
    "https://raw.githubusercontent.com/Roywaller/clash_subscription/refs/heads/main/clash_subscription.txt",
    "https://raw.githubusercontent.com/Q3dlaXpoaQ/V2rayN_Clash_Node_Getter/refs/heads/main/APIs/sc0.yaml",
    "https://raw.githubusercontent.com/Q3dlaXpoaQ/V2rayN_Clash_Node_Getter/refs/heads/main/APIs/sc1.yaml",
    "https://raw.githubusercontent.com/Q3dlaXpoaQ/V2rayN_Clash_Node_Getter/refs/heads/main/APIs/sc2.yaml",
    "https://raw.githubusercontent.com/Q3dlaXpoaQ/V2rayN_Clash_Node_Getter/refs/heads/main/APIs/sc3.yaml",
    "https://raw.githubusercontent.com/Q3dlaXpoaQ/V2rayN_Clash_Node_Getter/refs/heads/main/APIs/sc4.yaml",
    "https://raw.githubusercontent.com/xiaoji235/airport-free/refs/heads/main/clash/naidounode.txt",
    "https://raw.githubusercontent.com/mahdibland/SSAggregator/master/sub/sub_merge_yaml.yml",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.yml",
    "https://raw.githubusercontent.com/vxiaov/free_proxies/main/clash/clash.provider.yaml",
    "https://raw.githubusercontent.com/snakem982/proxypool/main/source/clash-meta.yaml",
    "https://raw.githubusercontent.com/leetomlee123/freenode/refs/heads/main/README.md", # This is a Markdown file
    "https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/master/list.yml",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml",
    "https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/speednodes.yaml",
    "https://raw.githubusercontent.com/mgit0001/test_clash/refs/heads/main/heima.txt",
    "https://raw.githubusercontent.com/mai19950/clashgithub_com/refs/heads/main/site", # This might be an HTML or placeholder
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/refs/heads/main/README.md", # Markdown
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/refs/heads/main/sub", # Might be a placeholder or a specific file if not 404
    "https://raw.githubusercontent.com/shahidbhutta/Clash/refs/heads/main/Router", # Likely a placeholder or directory listing if not a direct file
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.meta.yml",
    "https://raw.githubusercontent.com/anaer/Sub/refs/heads/main/clash.yaml",
    "https://raw.githubusercontent.com/free18/v2ray/refs/heads/main/c.yaml",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.yml",
    "https://raw.githubusercontent.com/mfbpn/tg_mfbpn_sub/main/trial.yaml",
    "https://raw.githubusercontent.com/Ruk1ng001/freeSub/main/clash.yaml",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/all_configs.txt",
    "https://raw.githubusercontent.com/ripaojiedian/freenode/main/clash", # Might be placeholder
    "https://raw.githubusercontent.com/go4sharing/sub/main/sub.yaml",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/clash.yaml"
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Expected content types for raw subscription files (can be extended)
# For raw.githubusercontent.com, 'text/plain' is very common. YAML files might also be served as 'application/x-yaml' or 'text/yaml'.
# 'application/octet-stream' can be a generic binary/text type.
# We will primarily filter out 'text/html' for raw.githubusercontent.com links if status is 200.
import yaml

EXPECTED_RAW_CONTENT_TYPES = ['text/plain; charset=utf-8', 'text/plain', 'application/yaml', 'application/x-yaml', 'application/octet-stream']

def is_valid_yaml_content(content):
    """
    Checks if the content is likely a valid YAML file by trying to parse the first few lines.
    """
    try:
        yaml.safe_load(content)
        return True
    except yaml.YAMLError:
        return False


def check_url(url):
    """
    Checks if a URL is accessible and likely a raw subscription file.
    Returns the URL if successful, None otherwise.
    """
    try:
        # 使用前置代理
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

        # Using GET with stream=True to avoid downloading full content if not needed,
        # but allowing us to check headers.
        response = requests.get(url, timeout=30, headers=headers, stream=True, allow_redirects=True, proxies=proxies)
        status_code = response.status_code
        content_type = response.headers.get('Content-Type', '').lower()
        # It's important to close the response to free up resources, especially with stream=True
        response.close()

        if status_code == 200:
            if "raw.githubusercontent.com" in url and 'text/html' in content_type:
                logging.info(f"[INFO]    {url} (Status: 200, but Content-Type is HTML: {content_type} - Likely not a raw subscription file)")
                return None

            if content_type not in EXPECTED_RAW_CONTENT_TYPES:
                logging.info(f"{url} (Status: 200, but unexpected Content-Type: {content_type})")
                return None

            #if "raw.githubusercontent.com" in url and url.lower().endswith("readme.md"):
            #    logging.info(f"{url} (Status: 200, Content-Type: {content_type} - Is a README.md, might not be a direct sub)")
            #    return None

            # Attempt to read the first 2048 bytes to validate content
            try:
                response = requests.get(url, timeout=30, headers=headers, stream=True, allow_redirects=True)
                chunk = next(response.iter_content(2048, decode_unicode=True), None)
                response.close()

                if chunk:
                    if 'yaml' in content_type:
                        if not is_valid_yaml_content(chunk):
                            logging.info(f"{url} (Status: 200, Content-Type: {content_type}, but invalid YAML content)")
                            return None
                    # Add more content validation checks here for other content types if needed

                logging.info(f"[SUCCESS] {url} (Status: {status_code}, Content-Type: {content_type})")
                return url
            except Exception as e:
                logging.error(f"[FAILED]  {url} (Content Validation Error: {e})")
                return None
        else:
            logging.warning(f"{url} (Status: {status_code}, Content-Type: {content_type})")
            return None
    except Exception as e:
        logging.error(f"{url} (Request Error: {e})")
        return None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_url(url, proxy_url=""):
    """
    Checks if a URL is accessible and likely a raw subscription file.
    Returns the URL if successful, None otherwise.
    """
    try:
        response = requests.get(url, timeout=15, headers=headers, stream=True, allow_redirects=True)
        status_code = response.status_code
        content_type = response.headers.get('Content-Type', '').lower()
        response.close()

        if status_code == 200:
            if "raw.githubusercontent.com" in url and 'text/html' in content_type:
                logging.info(f"{url} (Status: 200, but Content-Type is HTML: {content_type} - Likely not a raw subscription file)")
                return None

            if content_type not in EXPECTED_RAW_CONTENT_TYPES:
                logging.info(f"{url} (Status: 200, but unexpected Content-Type: {content_type})")
                return None

            if "raw.githubusercontent.com" in url and url.lower().endswith("readme.md"):
                logging.info(f"{url} (Status: 200, Content-Type: {content_type} - Is a README.md, might not be a direct sub)")
                return None

            # Attempt to read the first 2048 bytes to validate content
            try:
                response = requests.get(url, timeout=15, headers=headers, stream=True, allow_redirects=True)
                chunk = next(response.iter_content(2048, decode_unicode=True), None)
                response.close()

                if chunk:
                    if 'yaml' in content_type:
                        if not is_valid_yaml_content(chunk):
                            logging.info(f"{url} (Status: 200, Content-Type: {content_type}, but invalid YAML content)")
                            return None
                    # Add more content validation checks here for other content types if needed

                logging.info(f"[SUCCESS] {url} (Status: {status_code}, Content-Type: {content_type})")
                return url
            except requests.exceptions.RequestException as e:
                logging.error(f"{url} (Content Validation Error: {e})")
                return None
        else:
            logging.warning(f"{url} (Status: {status_code}, Content-Type: {content_type})")
            return None

    except requests.exceptions.Timeout:
        logging.warning(f"{url} (Timeout)")
        return None
    except requests.exceptions.ConnectionError as e:
        logging.error(f"{url} (Connection Error: {e})")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"{url} (Request Error: {e})")
        return None

logging.info("Testing links...\n")
accessible_links = []

# 使用 ThreadPoolExecutor 进行并发请求
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_to_url = {executor.submit(check_url, url): url for url in urls_to_test}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            result_url = future.result()
            if result_url:
                accessible_links.append(result_url)
        except Exception as exc:
            logging.error(f"{url} generated an exception: {exc}")

# Sort the list to maintain a somewhat consistent order if needed, though concurrent execution doesn't guarantee original order for processing
# accessible_links.sort() # Optional: if you want them sorted alphabetically

logging.info("\nSuccessfully accessible and likely valid subscription links:")
if accessible_links:
    # 按照指定格式输出成功链接
    print("成功测试的链接:")
    for link in accessible_links:
        print(f'- "{link}"')
else:
    logging.info("No links were deemed accessible and valid subscription files.")
