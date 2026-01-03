#!/bin/bash
#======================================================================
# BioInfo Search System - 停止本地服务
#======================================================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "停止 BioInfo Search System 服务..."

# 停止后端
if [ -f "$PROJECT_DIR/data/backend.pid" ]; then
    PID=$(cat "$PROJECT_DIR/data/backend.pid")
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✓ 后端服务已停止 (PID: $PID)"
    fi
    rm -f "$PROJECT_DIR/data/backend.pid"
fi

# 停止前端
if [ -f "$PROJECT_DIR/data/frontend.pid" ]; then
    PID=$(cat "$PROJECT_DIR/data/frontend.pid")
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✓ 前端服务已停止 (PID: $PID)"
    fi
    rm -f "$PROJECT_DIR/data/frontend.pid"
fi

# 停止Ollama（可选）
read -p "是否停止 Ollama 服务？[y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pkill -x ollama 2>/dev/null && echo "✓ Ollama 服务已停止" || echo "Ollama 服务未运行"
fi

echo ""
echo "所有服务已停止"
