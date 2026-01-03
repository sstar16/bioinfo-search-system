#!/bin/bash
#======================================================================
# BioInfo Search System - Docker 一键部署脚本
# 使用方法: ./deploy-docker.sh [gpu|cpu]
#======================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 显示横幅
show_banner() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║       BioInfo Search System - Docker 部署脚本               ║"
    echo "║       生物信息智能检索系统                                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
}

# 检查Docker是否安装
check_docker() {
    log_info "检查 Docker 安装状态..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        echo "  安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
    
    log_success "Docker 已安装"
}

# 检查GPU支持
check_gpu() {
    log_info "检查 GPU 支持..."
    
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi &> /dev/null
        if [ $? -eq 0 ]; then
            log_success "检测到 NVIDIA GPU"
            return 0
        fi
    fi
    
    log_warn "未检测到 NVIDIA GPU，将使用 CPU 模式"
    return 1
}

# 选择部署模式
select_mode() {
    local mode=${1:-"auto"}
    
    if [ "$mode" == "gpu" ]; then
        COMPOSE_FILE="docker-compose.yml"
        log_info "使用 GPU 模式部署"
    elif [ "$mode" == "cpu" ]; then
        COMPOSE_FILE="docker-compose.cpu.yml"
        log_info "使用 CPU 模式部署"
    else
        # 自动检测
        if check_gpu; then
            COMPOSE_FILE="docker-compose.yml"
            log_info "自动选择: GPU 模式"
        else
            COMPOSE_FILE="docker-compose.cpu.yml"
            log_info "自动选择: CPU 模式"
        fi
    fi
}

# 构建和启动服务
deploy_services() {
    log_info "构建和启动服务..."
    
    # 停止旧服务（如果存在）
    docker compose -f $COMPOSE_FILE down 2>/dev/null || true
    
    # 构建镜像
    log_info "构建 Docker 镜像..."
    docker compose -f $COMPOSE_FILE build --no-cache
    
    # 启动服务
    log_info "启动服务..."
    docker compose -f $COMPOSE_FILE up -d
    
    log_success "服务启动成功"
}

# 下载并设置LLM模型
setup_llm_model() {
    log_info "等待 Ollama 服务启动..."
    sleep 10
    
    log_info "下载 LLaMA 3.2 模型（这可能需要几分钟）..."
    docker exec bioinfo-ollama ollama pull llama3.2 || {
        log_warn "模型下载失败，可以稍后手动执行:"
        echo "  docker exec bioinfo-ollama ollama pull llama3.2"
    }
    
    log_success "LLM 模型设置完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "后端服务已就绪"
            break
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_warn "服务启动超时，请检查日志"
    fi
}

# 显示服务状态
show_status() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                     部署完成！                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    log_info "服务状态:"
    docker compose -f $COMPOSE_FILE ps
    echo ""
    log_info "访问地址:"
    echo "  🌐 Web界面:     http://localhost"
    echo "  🔧 API文档:     http://localhost:8000/docs"
    echo "  🤖 Ollama:      http://localhost:11434"
    echo ""
    log_info "常用命令:"
    echo "  查看日志:       docker compose -f $COMPOSE_FILE logs -f"
    echo "  停止服务:       docker compose -f $COMPOSE_FILE down"
    echo "  重启服务:       docker compose -f $COMPOSE_FILE restart"
    echo ""
}

# 主函数
main() {
    show_banner
    
    # 检查是否在项目目录
    if [ ! -f "docker-compose.yml" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    check_docker
    select_mode "$1"
    deploy_services
    setup_llm_model
    wait_for_services
    show_status
}

# 运行
main "$@"
