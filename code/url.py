import requests
import concurrent.futures

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
EXPECTED_RAW_CONTENT_TYPES_SUBSTRINGS = ['text/plain', 'application/yaml', 'application/x-yaml', 'octet-stream']


def check_url(url):
    """
    Checks if a URL is accessible and likely a raw subscription file.
    Returns the URL if successful, None otherwise.
    """
    try:
        # Using GET with stream=True to avoid downloading full content if not needed,
        # but allowing us to check headers.
        response = requests.get(url, timeout=15, headers=headers, stream=True, allow_redirects=True)
        status_code = response.status_code
        content_type = response.headers.get('Content-Type', '').lower()
        
        # It's important to close the response to free up resources, especially with stream=True
        response.close()

        if status_code == 200:
            # For raw.githubusercontent.com, if the Content-Type is HTML,
            # it's often a GitHub "file not found" or "repo not found" page that still returns 200,
            # or a rendered Markdown page instead of the raw Markdown.
            # We want the raw content.
            if "raw.githubusercontent.com" in url and 'text/html' in content_type:
                print(f"[INFO]    {url} (Status: 200, but Content-Type is HTML: {content_type} - Likely not a raw subscription file)")
                return None

            # A more general check for typical subscription file content types
            # This part can be adjusted based on how strict you want to be.
            # If the content_type is empty or one of the expected ones, consider it good.
            is_expected_type = False
            if not content_type: # If no content-type, we might still try (could be plain text)
                is_expected_type = True
            else:
                for expected_substring in EXPECTED_RAW_CONTENT_TYPES_SUBSTRINGS:
                    if expected_substring in content_type:
                        is_expected_type = True
                        break
            
            if is_expected_type:
                 # Check if it's a README.md on GitHub, these are often not direct subscription files.
                if "raw.githubusercontent.com" in url and url.lower().endswith("readme.md"):
                    print(f"[INFO]    {url} (Status: 200, Content-Type: {content_type} - Is a README.md, might not be a direct sub)")
                    # Depending on your needs, you might want to return None here or keep it.
                    # For now, we'll assume READMEs are not desired as *direct* subscription files.
                    return None # Or return url if you want to include them

                print(f"[SUCCESS] {url} (Status: {status_code}, Content-Type: {content_type})")
                return url
            else:
                print(f"[INFO]    {url} (Status: 200, but unexpected Content-Type: {content_type})")
                return None

        else:
            print(f"[FAILED]  {url} (Status: {status_code}, Content-Type: {content_type})")
            return None
            
    except requests.exceptions.Timeout:
        print(f"[FAILED]  {url} (Timeout)")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"[FAILED]  {url} (Connection Error: {e})")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[FAILED]  {url} (Error: {e})")
        return None

print("Testing links...\n")
accessible_links = []

# Use ThreadPoolExecutor for concurrent requests
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_to_url = {executor.submit(check_url, url): url for url in urls_to_test}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            result_url = future.result()
            if result_url:
                accessible_links.append(result_url)
        except Exception as exc:
            print(f"[ERROR]   {url} generated an exception: {exc}")

# Sort the list to maintain a somewhat consistent order if needed, though concurrent execution doesn't guarantee original order for processing
# accessible_links.sort() # Optional: if you want them sorted alphabetically

print("\nSuccessfully accessible and likely valid subscription links:")
if accessible_links:
    # Re-check original order for printing if desired, or print as collected
    # For exact original order of successful links:
    ordered_successful_links = [url for url in urls_to_test if url in accessible_links]
    for link in ordered_successful_links:
        print(f'  - "{link}"')
else:
    print("No links were deemed accessible and valid subscription files.")

