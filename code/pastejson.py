import json
from datetime import datetime, timezone

def convert_destination_to_sample_format(source_filepath="destination.json", target_filepath="sample-import-data.json"):
    """
    将 destination.json 文件的数据重写为 sample-import-data.json 格式。

    Args:
        source_filepath (str): 源 JSON 文件的路径。
        target_filepath (str): 目标 JSON 文件的路径。
    """
    try:
        with open(source_filepath, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
    except FileNotFoundError:
        print(f"错误：源文件 '{source_filepath}' 未找到。")
        return
    except json.JSONDecodeError:
        print(f"错误：源文件 '{source_filepath}' 不是有效的 JSON 格式。")
        return

    # 初始化目标数据结构
    output_data = {
        "exportTime": "",
        "totalEntries": 0,
        "exportedBy": "admin", # 根据示例
        "entries": []
    }

    # 转换 entries
    for item in source_data:
        # 转换时间格式
        # 源格式: "2025-03-04 13:32:44"
        # 目标格式: "2025-03-04T13:32:44.000Z"
        try:
            dt_object = datetime.strptime(item["time"], "%Y-%m-%d %H:%M:%S")
            # 格式化为 ISO 8601，并添加 .000Z 表示 UTC 和毫秒
            # 注意: 原始时间数据没有时区信息，这里我们直接将其视为 UTC 时间点进行格式化
            formatted_time = dt_object.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except ValueError:
            print(f"警告：条目 '{item.get('id', '未知ID')}' 的时间格式 '{item.get('time', '')}' 无效，将跳过时间转换。")
            formatted_time = item.get("time", "") # 或者设置为一个默认错误值

        new_entry = {
            "id": item.get("id", ""),
            "text": item.get("text", ""),
            "note": item.get("note", ""), # 如果 note 可能不存在，提供默认空字符串
            "time": formatted_time,
            "pinned": item.get("pinned", False),
            "hidden": item.get("hidden", False)
        }
        output_data["entries"].append(new_entry)

    # 更新元数据
    output_data["totalEntries"] = len(output_data["entries"])

    # 生成当前的 UTC exportTime
    now_utc = datetime.now(timezone.utc)
    # 格式化为 "YYYY-MM-DDTHH:MM:SS.sssZ"
    # .%f 会给出微秒 (6位)，我们需要毫秒 (3位)
    output_data["exportTime"] = now_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


    # 写入目标文件
    try:
        with open(target_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"数据已成功转换并保存到 '{target_filepath}'")
    except IOError:
        print(f"错误：无法写入目标文件 '{target_filepath}'。")

if __name__ == "__main__":
    # 确保你的 destination.json 文件和这个脚本在同一个目录下
    # 或者提供完整的文件路径
    convert_destination_to_sample_format()

    # 验证一下输出（可选）
    # try:
    #     with open("sample-import-data.json", 'r', encoding='utf-8') as f:
    #         print("\n生成的文件内容预览:")
    #         # 只打印一部分，避免控制台输出过多
    #         content = json.load(f)
    #         print(f"Export Time: {content.get('exportTime')}")
    #         print(f"Total Entries: {content.get('totalEntries')}")
    #         if content.get('entries'):
    #             print(f"First entry: {content['entries'][0]}")
    # except Exception as e:
    #     print(f"无法读取生成的文件进行预览: {e}")
