@echo off
chcp 65001 >nul
REM ======================================================================
REM BioInfo Search System - Windows 本地部署脚本
REM 适用于 Conda 环境
REM ======================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║       BioInfo Search System - Windows 部署脚本               ║
echo ║       生物信息智能检索系统                                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

echo [INFO] 项目目录: %PROJECT_DIR%

REM 检查是否在conda环境中
echo [INFO] 检查 Conda 环境...
where conda >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 未检测到 Conda，请先安装 Anaconda 或 Miniconda
    pause
    exit /b 1
)
echo [SUCCESS] Conda 已安装

REM 创建conda环境（如果不存在）
echo [INFO] 检查/创建 Conda 环境 'bioinfo'...
call conda activate bioinfo 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] 创建新的 Conda 环境...
    call conda create -n bioinfo python=3.11 -y
    call conda activate bioinfo
)
echo [SUCCESS] Conda 环境已激活

REM 安装依赖
echo [INFO] 安装 Python 依赖...
pip install -r "%PROJECT_DIR%\backend\requirements.txt" -q
echo [SUCCESS] 依赖安装完成

REM 创建数据目录
echo [INFO] 创建数据目录...
if not exist "%PROJECT_DIR%\data" mkdir "%PROJECT_DIR%\data"
if not exist "%PROJECT_DIR%\data\exports" mkdir "%PROJECT_DIR%\data\exports"
if not exist "%PROJECT_DIR%\data\logs" mkdir "%PROJECT_DIR%\data\logs"
echo [SUCCESS] 目录创建完成

REM 检查Ollama
echo [INFO] 检查 Ollama...
where ollama >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Ollama 未安装
    echo.
    echo 请从 https://ollama.ai/download 下载并安装 Ollama
    echo 安装后运行: ollama pull llama3.2
    echo.
    echo 系统将在没有LLM的情况下继续运行（使用规则解析）
    echo.
) else (
    echo [SUCCESS] Ollama 已安装
    echo [INFO] 检查 LLaMA 3.2 模型...
    ollama list | findstr "llama3.2" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [INFO] 下载 LLaMA 3.2 模型...
        ollama pull llama3.2
    )
)

REM 设置环境变量
set DATA_DIR=%PROJECT_DIR%\data
set DB_PATH=%PROJECT_DIR%\data\bioinfo.db
set OLLAMA_HOST=http://localhost:11434

echo.
echo [INFO] 启动后端服务...
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  后端服务启动中...                                           ║
echo ║  API地址: http://localhost:8000                              ║
echo ║  API文档: http://localhost:8000/docs                         ║
echo ║  按 Ctrl+C 停止服务                                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd "%PROJECT_DIR%\backend"
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
