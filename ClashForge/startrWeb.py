# run_streamlit.py
import subprocess
import sys

def run_streamlit_app(script_path):
    """使用 subprocess 运行 Streamlit 应用程序"""
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Streamlit 运行出错：{e}")

if __name__ == "__main__":
    script_to_run = "WebUI.py"  # 你的 Streamlit 脚本的路径
    run_streamlit_app(script_to_run)
