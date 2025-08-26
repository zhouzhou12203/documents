#!/bin/bash

# 域名扫描器启动脚本 for macOS
# 作者: Domain Scanner Team
# 版本: 1.0

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "域名扫描器启动脚本"
    echo "=================="
    echo "用法: ./start.sh [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示此帮助信息"
    echo "  -c, --config FILE   指定配置文件路径"
    echo "  -l LENGTH           设置域名长度 (默认: 4)"
    echo "  -s SUFFIX           设置域名后缀 (默认: .de)"
    echo "  -p PATTERN          设置域名模式 (D=字母, d=数字, a=字母数字) (默认: D)"
    echo "  -w WORKERS          设置并发工作线程数 (默认: 10)"
    echo "  -d DELAY            设置查询间隔毫秒数 (默认: 1000)"
    echo "  --show-registered   显示已注册的域名"
    echo "  -r REGEX            设置正则表达式过滤器"
    echo ""
    echo "示例:"
    echo "  ./start.sh                          # 使用默认配置启动"
    echo "  ./start.sh -l 3 -s .com -p D        # 扫描3位字母.com域名"
    echo "  ./start.sh -c myconfig.toml         # 使用自定义配置文件"
    echo "  ./start.sh --show-registered        # 显示已注册域名"
}

# 默认参数
CONFIG_FILE=""
DOMAIN_LENGTH="4"
DOMAIN_SUFFIX=".de"
DOMAIN_PATTERN="D"
WORKERS="10"
DELAY="1000"
SHOW_REGISTERED=""
REGEX_FILTER=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -l)
            DOMAIN_LENGTH="$2"
            shift 2
            ;;
        -s)
            DOMAIN_SUFFIX="$2"
            shift 2
            ;;
        -p)
            DOMAIN_PATTERN="$2"
            shift 2
            ;;
        -w)
            WORKERS="$2"
            shift 2
            ;;
        -d)
            DELAY="$2"
            shift 2
            ;;
        --show-registered)
            SHOW_REGISTERED="-show-registered"
            shift
            ;;
        -r)
            REGEX_FILTER="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 检查是否在项目目录中
if [ ! -f "$PROJECT_DIR/domain-scanner" ] && [ ! -f "$PROJECT_DIR/main.go" ]; then
    echo -e "${RED}错误: 未找到域名扫描器程序或源代码${NC}"
    echo "请确保在项目根目录中运行此脚本"
    exit 1
fi

# 显示启动信息
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   域名扫描器启动脚本                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查Go环境
if ! command -v go &> /dev/null; then
    echo -e "${YELLOW}警告: 未找到Go环境，将尝试使用预编译的二进制文件${NC}"
    USE_BINARY=true
else
    GO_VERSION=$(go version | cut -d' ' -f3)
    echo -e "Go版本: ${GREEN}$GO_VERSION${NC}"
    USE_BINARY=false
fi

# 创建结果目录
mkdir -p "$PROJECT_DIR/results"

# 构建命令参数
CMD_ARGS=""

if [ -n "$CONFIG_FILE" ]; then
    if [ -f "$CONFIG_FILE" ]; then
        CMD_ARGS="$CMD_ARGS -config $CONFIG_FILE"
        echo -e "使用配置文件: ${GREEN}$CONFIG_FILE${NC}"
    else
        echo -e "${YELLOW}警告: 配置文件 $CONFIG_FILE 不存在${NC}"
    fi
else
    # 使用命令行参数
    CMD_ARGS="$CMD_ARGS -l $DOMAIN_LENGTH"
    CMD_ARGS="$CMD_ARGS -s $DOMAIN_SUFFIX"
    CMD_ARGS="$CMD_ARGS -p $DOMAIN_PATTERN"
    CMD_ARGS="$CMD_ARGS -workers $WORKERS"
    CMD_ARGS="$CMD_ARGS -delay $DELAY"
    
    if [ -n "$SHOW_REGISTERED" ]; then
        CMD_ARGS="$CMD_ARGS $SHOW_REGISTERED"
    fi
    
    if [ -n "$REGEX_FILTER" ]; then
        CMD_ARGS="$CMD_ARGS -r $REGEX_FILTER"
    fi
    
    echo -e "域名长度: ${GREEN}$DOMAIN_LENGTH${NC}"
    echo -e "域名后缀: ${GREEN}$DOMAIN_SUFFIX${NC}"
    echo -e "域名模式: ${GREEN}$DOMAIN_PATTERN${NC}"
    echo -e "工作线程: ${GREEN}$WORKERS${NC}"
    echo -e "查询间隔: ${GREEN}$DELAY ms${NC}"
    
    if [ -n "$SHOW_REGISTERED" ]; then
        echo -e "显示已注册域名: ${GREEN}是${NC}"
    fi
    
    if [ -n "$REGEX_FILTER" ]; then
        echo -e "正则过滤器: ${GREEN}$REGEX_FILTER${NC}"
    fi
fi

echo ""
echo -e "结果将保存到: ${GREEN}$PROJECT_DIR/results/${NC}"
echo ""

# 确认启动
echo -e "${YELLOW}按回车键开始扫描，或按 Ctrl+C 取消...${NC}"
read -r

# 启动域名扫描器
echo -e "${BLUE}启动域名扫描器...${NC}"

if [ "$USE_BINARY" = true ] && [ -f "$PROJECT_DIR/domain-scanner" ]; then
    echo -e "使用预编译二进制文件: ${GREEN}domain-scanner${NC}"
    "$PROJECT_DIR/domain-scanner" $CMD_ARGS
elif [ -f "$PROJECT_DIR/main.go" ]; then
    echo -e "使用源代码编译运行..."
    go run "$PROJECT_DIR/main.go" $CMD_ARGS
else
    echo -e "${RED}错误: 未找到可执行文件${NC}"
    exit 1
fi

# 检查执行结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}域名扫描完成!${NC}"
    
    # 显示结果文件
    if [ -d "$PROJECT_DIR/results" ]; then
        echo ""
        echo -e "生成的文件:"
        ls -la "$PROJECT_DIR/results/" | grep -E "\.(txt)$" | while read -r line; do
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