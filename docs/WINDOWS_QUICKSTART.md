# Windows + Conda 快速启动指南

## 方式一：手动启动（推荐）

### 1. 打开 Anaconda Prompt 或 PowerShell

### 2. 创建并激活 Conda 环境
```bash
# 创建环境（首次）
conda create -n bioinfo python=3.11 -y

# 激活环境
conda activate bioinfo
```

### 3. 进入项目目录
```bash
cd D:\AI\BAI\bioinfo-search-system
```

### 4. 安装依赖
```bash
pip install -r backend/requirements.txt
```

### 5. 创建数据目录
```bash
mkdir data
mkdir data\exports
mkdir data\logs
```

### 6. 启动后端服务
```bash
cd backend
set DATA_DIR=..\data
set DB_PATH=..\data\bioinfo.db
set OLLAMA_HOST=http://localhost:11434
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 7. 启动前端（新开一个终端）
```bash
cd D:\AI\BAI\bioinfo-search-system\frontend
python -m http.server 3000
```

### 8. 访问系统
- 前端界面: http://localhost:3000
- API文档: http://localhost:8000/docs

---

## 方式二：使用批处理脚本

双击运行 `scripts/deploy-windows.bat`

---

## 安装 Ollama（可选，用于LLM功能）

1. 从 https://ollama.ai/download 下载 Windows 版本
2. 安装后打开 PowerShell 运行：
   ```bash
   ollama pull llama3.2
   ```
3. Ollama 会自动在后台运行

**注意**：即使不安装 Ollama，系统也可以运行，只是会使用规则解析而不是 LLM 解析。

---

## 常见问题

### Q: pip install 报错？
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Q: uvicorn 找不到？
```bash
pip install uvicorn[standard]
```

### Q: 端口被占用？
修改端口号：
```bash
python -m uvicorn app:app --port 8001
```
