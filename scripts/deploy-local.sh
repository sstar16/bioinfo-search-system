#!/bin/bash
#======================================================================
# BioInfo Search System - 本地部署脚本（无Docker）
# 适用于开发环境或不想使用Docker的情况
#======================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 显示横幅
show_banner() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║       BioInfo Search System - 本地部署脚本                  ║"
    echo "║       生物信息智能检索系统                                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
}

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# 检查Python版本
check_python() {
    log_info "检查 Python 环境..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python 未安装，请安装 Python 3.10+"
        exit 1
    fi
    
    # 检查版本
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_success "Python 版本: $PYTHON_VERSION"
    
    # 检查是否>=3.10
    if [[ $(echo "$PYTHON_VERSION < 3.10" | bc -l 2>/dev/null || echo "0") == "1" ]]; then
        log_warn "建议使用 Python 3.10 或更高版本"
    fi
}

# 创建虚拟环境
setup_venv() {
    log_info "设置 Python 虚拟环境..."
    
    VENV_DIR="$PROJECT_DIR/venv"
    
    if [ -d "$VENV_DIR" ]; then
        log_info "虚拟环境已存在"
    else
        $PYTHON_CMD -m venv "$VENV_DIR"
        log_success "虚拟环境创建成功"
    fi
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 升级pip
    pip install --upgrade pip -q
}

# 安装依赖
install_dependencies() {
    log_info "安装 Python 依赖..."
    
    pip install -r "$PROJECT_DIR/backend/requirements.txt" -q
    
    log_success "依赖安装完成"
}

# 检查并安装Ollama
setup_ollama() {
    log_info "检查 Ollama..."
    
    if command -v ollama &> /dev/null; then
        log_success "Ollama 已安装"
    else
        log_warn "Ollama 未安装"
        echo ""
        echo "请按照以下步骤安装 Ollama:"
        echo ""
        echo "Linux/macOS:"
        echo "  curl -fsSL https://ollama.ai/install.sh | sh"
        echo ""
        echo "Windows:"
        echo "  访问 https://ollama.ai/download 下载安装程序"
        echo ""
        
        read -p "是否继续（不使用LLM功能）？[y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        return 1
    fi
    
    return 0
}

# 下载LLM模型
download_model() {
    log_info "下载 LLaMA 3.2 模型..."
    
    if ollama list 2>/dev/null | grep -q "llama3.2"; then
        log_success "模型已存在"
    else
        log_info "正在下载模型（这可能需要几分钟）..."
        ollama pull llama3.2 || {
            log_warn "模型下载失败，可以稍后手动执行: ollama pull llama3.2"
        }
    fi
}

# 创建数据目录
setup_directories() {
    log_info "创建数据目录..."
    
    mkdir -p "$PROJECT_DIR/data"
    mkdir -p "$PROJECT_DIR/data/exports"
    mkdir -p "$PROJECT_DIR/data/logs"
    
    log_success "目录创建完成"
}

# 启动Ollama服务
start_ollama() {
    log_info "启动 Ollama 服务..."
    
    if pgrep -x "ollama" > /dev/null; then
        log_info "Ollama 服务已在运行"
    else
        ollama serve &
        sleep 3
        log_success "Ollama 服务已启动"
    fi
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    
    cd "$PROJECT_DIR/backend"
    
    export DATA_DIR="$PROJECT_DIR/data"
    export DB_PATH="$PROJECT_DIR/data/bioinfo.db"
    export OLLAMA_HOST="http://localhost:11434"
    
    # 在后台启动
    nohup $PYTHON_CMD -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload > "$PROJECT_DIR/data/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PROJECT_DIR/data/backend.pid"
    
    log_success "后端服务已启动 (PID: $BACKEND_PID)"
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    
    cd "$PROJECT_DIR/frontend"
    
    # 使用Python内置HTTP服务器
    nohup $PYTHON_CMD -m http.server 3000 > "$PROJECT_DIR/data/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$PROJECT_DIR/data/frontend.pid"
    
    log_success "前端服务已启动 (PID: $FRONTEND_PID)"
}

# 显示状态
show_status() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                     部署完成！                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    log_info "访问地址:"
    echo "  🌐 Web界面:     http://localhost:3000"
    echo "  🔧 API接口:     http://localhost:8000"
    echo "  📚 API文档:     http://localhost:8000/docs"
    echo "  🤖 Ollama:      http://localhost:11434"
    echo ""
    log_info "日志文件:"
    echo "  后端日志:       $PROJECT_DIR/data/logs/backend.log"
    echo "  前端日志:       $PROJECT_DIR/data/logs/frontend.log"
    echo ""
    log_info "停止服务:"
    echo "  ./scripts/stop-local.sh"
    echo ""
}

# 主函数
main() {
    show_banner
    
    check_python
    setup_venv
    install_dependencies
    setup_directories
    
    if setup_ollama; then
        start_ollama
        download_model
    fi
    
    start_backend
    start_frontend
    
    # 等待服务启动
    sleep 3
    
    show_status
}

# 运行
main "$@"
