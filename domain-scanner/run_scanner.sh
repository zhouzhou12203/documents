#!/bin/bash

# 域名扫描器交互式启动脚本
# 作者: Domain Scanner Team
# 版本: 1.1

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 设置默认值
default_l=3
default_s=".de"
default_p="D"
default_workers=10
default_delay=1000
default_show_registered="n"
default_regex=""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示欢迎信息
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 域名扫描器交互式启动脚本                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 询问用户，如果用户输入为空则使用默认值
read -p "请输入域名长度 (默认为 $default_l): " l
l=${l:-$default_l}

read -p "请输入域名后缀 (默认为 $default_s): " s
s=${s:-$default_s}

# 验证域名模式输入
while true; do
    read -p "请输入域名模式 (d=纯数字, D=纯字母, a=字母数字混合) (默认为 $default_p): " p
    p=${p:-$default_p}
    if [[ "$p" == "d" || "$p" == "D" || "$p" == "a" ]]; then
        break
    else
        echo -e "${RED}无效的域名模式，请输入 d、D 或 a${NC}"
    fi
done

read -p "请输入并发工作线程数 (默认为 $default_workers): " workers
workers=${workers:-$default_workers}

read -p "请输入查询间隔毫秒数 (默认为 $default_delay): " delay
delay=${delay:-$default_delay}

read -p "是否显示已注册的域名? (y/n, 默认为 $default_show_registered): " show_registered
show_registered=${show_registered:-$default_show_registered}

read -p "请输入正则表达式 (默认为空，不使用正则表达式): " regex
regex=${regex:-"$default_regex"}

# 在当前目录执行（而不是硬编码的路径）
cd "$SCRIPT_DIR" || { echo -e "${RED}无法进入脚本目录${NC}"; exit 1; }

# 检查必要的文件是否存在
if [ ! -f "main.go" ] && [ ! -f "domain-scanner" ]; then
    echo -e "${RED}错误: 未找到 main.go 源文件或 domain-scanner 二进制文件${NC}"
    exit 1
fi

# 构建命令数组
if [ -f "domain-scanner" ]; then
    command=("./domain-scanner" -l "$l" -s "$s" -p "$p" -workers "$workers" -delay "$delay")
    echo -e "使用预编译二进制文件: ${GREEN}domain-scanner${NC}"
else
    command=("go" "run" "main.go" -l "$l" -s "$s" -p "$p" -workers "$workers" -delay "$delay")
    echo -e "使用源代码编译运行..."
fi

# 根据用户选择添加 -show-registered 选项
if [[ "$show_registered" == "y" || "$show_registered" == "Y" ]]; then
    command+=(-show-registered)
fi

# 如果用户输入了正则表达式，则添加 -r 选项
if [ -n "$regex" ]; then
    command+=(-r "$regex")
fi

# 创建结果目录
mkdir -p "$SCRIPT_DIR/results"

# 显示配置摘要
echo ""
echo -e "${BLUE}配置摘要:${NC}"
echo -e "  域名长度: ${GREEN}$l${NC}"
echo -e "  域名后缀: ${GREEN}$s${NC}"
echo -e "  域名模式: ${GREEN}$p${NC}"
echo -e "  工作线程: ${GREEN}$workers${NC}"
echo -e "  查询间隔: ${GREEN}$delay ms${NC}"
if [[ "$show_registered" == "y" || "$show_registered" == "Y" ]]; then
    echo -e "  显示已注册域名: ${GREEN}是${NC}"
else
    echo -e "  显示已注册域名: ${GREEN}否${NC}"
fi
if [ -n "$regex" ]; then
    echo -e "  正则表达式: ${GREEN}$regex${NC}"
fi
echo -e "  结果目录: ${GREEN}$SCRIPT_DIR/results${NC}"
echo ""

# 确认执行
echo -e "${YELLOW}按回车键开始扫描，或按 Ctrl+C 取消...${NC}"
read -r

# 打印要执行的命令
echo -e "要执行的命令是: ${GREEN}${command[*]}${NC}"
echo ""

# 执行命令
echo -e "${BLUE}启动域名扫描器...${NC}"
"${command[@]}"

# 检查执行结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}域名扫描完成!${NC}"
    
    # 显示结果文件
    if [ -d "$SCRIPT_DIR/results" ]; then
        echo ""
        echo -e "生成的文件:"
        ls -la "$SCRIPT_DIR/results/" | grep -E "\.(txt)$" | while read -r line; do
            echo -e "  ${GREEN}$(echo "$line" | awk '{print $NF}')${NC}"
        done
    fi
else
    echo ""
    echo -e "${RED}域名扫描过程中出现错误!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}感谢使用域名扫描器!${NC}"