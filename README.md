# BioInfo Search System

## 生物信息智能检索系统

基于自然语言处理和大语言模型（LLM）的生物信息智能检索系统，支持从多个专业数据库（ClinicalTrials.gov、PubMed等）获取、清洗和集成生物医学数据。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## ✨ 功能特性

### 🤖 智能查询解析
- 支持自然语言输入（中英文）
- 使用本地LLM（LLaMA 3.2）解析查询意图
- 自动提取疾病名称、干预类型、试验阶段等信息
- 智能关键词映射和翻译

### 🔍 多数据源检索
- **ClinicalTrials.gov**: 美国国立卫生研究院临床试验数据库
- **PubMed**: 美国国家医学图书馆生物医学文献数据库
- 可扩展更多数据源

### 🧹 数据清洗与集成
- 自动文本清洗和标准化
- 日期格式统一（ISO 8601）
- 年龄数值提取和转换
- 临床试验状态和阶段标准化
- 数据质量评分

### 📊 数据展示与导出
- 美观的Web界面
- 实时任务进度显示
- 支持CSV、Excel、JSON格式导出
- 搜索历史记录
- 数据统计分析

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户界面 (Web)                           │
│                    Vue 3 + Tailwind CSS                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Nginx 反向代理                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     后端 API (FastAPI)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │LLM解析器│  │数据获取器│  │数据清洗器│  │任务管理器│       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
         │                │                    │
         ▼                ▼                    ▼
┌──────────────┐  ┌──────────────┐   ┌──────────────────┐
│   Ollama     │  │ 外部API      │   │  SQLite数据库    │
│   (LLaMA)    │  │ ClinicalTrials│   │                  │
└──────────────┘  │ PubMed       │   └──────────────────┘
                  └──────────────┘
```

## 📁 项目结构

```
bioinfo-search-system/
├── backend/                    # 后端代码
│   ├── app.py                  # FastAPI主应用
│   ├── services/               # 服务模块
│   │   ├── llm_parser.py       # LLM查询解析
│   │   ├── data_fetcher.py     # 数据获取
│   │   ├── data_cleaner.py     # 数据清洗
│   │   ├── database.py         # 数据库管理
│   │   └── task_manager.py     # 任务管理
│   ├── requirements.txt        # Python依赖
│   └── Dockerfile              # 后端Docker配置
├── frontend/                   # 前端代码
│   └── index.html              # 单页应用
├── docker/                     # Docker配置
│   └── nginx.conf              # Nginx配置
├── scripts/                    # 部署脚本
│   ├── deploy-docker.sh        # Docker部署
│   ├── deploy-local.sh         # 本地部署
│   └── stop-local.sh           # 停止服务
├── docs/                       # 文档
│   └── PROJECT_SPECIFICATION.md # 项目说明书
├── docker-compose.yml          # Docker Compose (GPU)
├── docker-compose.cpu.yml      # Docker Compose (CPU)
└── README.md                   # 项目说明
```

## 🚀 快速开始

### 方式一：Docker一键部署（推荐）

#### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- 至少8GB内存
- （可选）NVIDIA GPU + NVIDIA Container Toolkit

#### 部署步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/bioinfo-search-system.git
cd bioinfo-search-system

# 2. 运行部署脚本
chmod +x scripts/deploy-docker.sh
./scripts/deploy-docker.sh

# 或指定模式
./scripts/deploy-docker.sh gpu    # GPU模式
./scripts/deploy-docker.sh cpu    # CPU模式
```

#### 访问服务
- Web界面: http://localhost
- API文档: http://localhost:8000/docs
- Ollama: http://localhost:11434

### 方式二：本地部署（无Docker）

#### 前置要求
- Python 3.10+
- pip
- （可选）Ollama

#### 部署步骤

```bash
# 1. 安装 Ollama（可选，用于LLM功能）
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2

# 2. 运行部署脚本
chmod +x scripts/deploy-local.sh
./scripts/deploy-local.sh
```

#### 访问服务
- Web界面: http://localhost:3000
- API接口: http://localhost:8000

## 📖 使用指南

### 基本搜索

在搜索框中输入自然语言查询，例如：

```
查找B群脑膜炎球菌疫苗的三期临床试验
```

系统会自动：
1. 使用LLM解析查询，提取关键信息
2. 从选定数据源获取数据
3. 清洗和标准化数据
4. 展示结果并提供导出功能

### 高级选项

- **使用LLM解析**: 启用/禁用LLM智能解析
- **数据源选择**: 选择要搜索的数据库
- **最大结果数**: 限制返回结果数量

### 数据导出

搜索完成后，可以将结果导出为：
- CSV格式
- Excel格式（.xlsx）
- JSON格式

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATA_DIR` | 数据存储目录 | `/app/data` |
| `DB_PATH` | 数据库文件路径 | `/app/data/bioinfo.db` |
| `OLLAMA_HOST` | Ollama服务地址 | `http://localhost:11434` |

### LLM模型

默认使用 `llama3.2` 模型。如需更换模型：

```bash
# 下载其他模型
ollama pull llama3.2:70b  # 更大的模型，更准确
ollama pull qwen2.5       # 中文支持更好

# 修改代码中的模型名称
# backend/services/llm_parser.py
self.model = "llama3.2:70b"  # 或其他模型名
```

## 📚 API文档

### 主要接口

#### POST /api/search
发起搜索请求

```json
{
  "query": "B群脑膜炎球菌疫苗临床试验",
  "max_results": 100,
  "sources": ["clinicaltrials", "pubmed"],
  "use_llm": true
}
```

#### GET /api/task/{task_id}
获取任务状态

#### GET /api/history
获取搜索历史

#### POST /api/export
导出数据

完整API文档访问: http://localhost:8000/docs

## 🛠️ 开发指南

### 添加新数据源

1. 在 `data_fetcher.py` 中添加新的获取方法
2. 在 `data_cleaner.py` 中添加对应的清洗逻辑
3. 更新 `DataSourceRegistry` 注册新数据源

### 优化LLM提示词

编辑 `llm_parser.py` 中的 `_build_prompt` 方法来调整提示词。

### 自定义清洗规则

在 `data_cleaner.py` 中添加新的清洗方法和规则。

## ❓ 常见问题

### Q: LLM解析失败怎么办？
A: 系统会自动回退到规则解析。检查Ollama服务是否正常运行：
```bash
curl http://localhost:11434/api/tags
```

### Q: 搜索速度很慢？
A: 
1. 减少最大结果数
2. 只选择需要的数据源
3. 使用GPU加速LLM推理

### Q: 内存不足？
A: 
1. 使用更小的LLM模型
2. 减少并发搜索数量
3. 定期清理历史数据

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [ClinicalTrials.gov](https://clinicaltrials.gov) - 临床试验数据
- [PubMed](https://pubmed.ncbi.nlm.nih.gov) - 生物医学文献
- [Ollama](https://ollama.ai) - 本地LLM运行时
- [FastAPI](https://fastapi.tiangolo.com) - 后端框架
- [Vue.js](https://vuejs.org) - 前端框架

## 📞 联系方式

如有问题或建议，请提交 Issue 或联系：
- 邮箱: your-email@example.com

---

**最后更新**: 2025年1月
