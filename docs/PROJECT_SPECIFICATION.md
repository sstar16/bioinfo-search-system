# BioInfo Search System 项目说明书

## 生物信息智能检索系统 - 技术规格文档

**文档版本**: 1.0.0  
**创建日期**: 2025年1月  
**文档状态**: 正式版

---

## 目录

1. [项目概述](#1-项目概述)
2. [需求分析](#2-需求分析)
3. [系统设计](#3-系统设计)
4. [技术实现](#4-技术实现)
5. [数据库设计](#5-数据库设计)
6. [API设计](#6-api设计)
7. [部署方案](#7-部署方案)
8. [测试方案](#8-测试方案)
9. [性能优化](#9-性能优化)
10. [安全考虑](#10-安全考虑)
11. [扩展计划](#11-扩展计划)

---

## 1. 项目概述

### 1.1 背景介绍

随着生物医学研究的快速发展，各类专业数据库（如ClinicalTrials.gov、PubMed等）积累了海量的临床试验和文献数据。研究人员需要高效地从这些分散的数据源中检索、整合和分析相关信息。

传统的检索方式存在以下问题：
- 需要掌握各数据库的特定查询语法
- 手动在多个数据库间切换检索
- 数据格式不统一，难以整合分析
- 无法智能理解用户的检索意图

### 1.2 项目目标

开发一个基于自然语言处理和大语言模型（LLM）的智能检索系统，实现：

1. **自然语言查询**: 用户可以使用日常语言描述检索需求
2. **智能意图理解**: 利用LLM解析查询，提取关键信息
3. **多源数据获取**: 自动从多个专业数据库检索数据
4. **数据清洗整合**: 标准化和整合不同来源的数据
5. **可视化展示**: 提供友好的Web界面展示结果

### 1.3 项目范围

**包含功能**:
- 自然语言查询解析（中英文）
- ClinicalTrials.gov数据检索
- PubMed文献数据检索
- 数据清洗和标准化
- 数据质量评估
- Web界面展示
- 数据导出（CSV/Excel/JSON）
- 搜索历史记录

**不包含功能**:
- 用户认证和权限管理
- 付费数据库接入
- 全文文献下载
- 深度学习模型训练

---

## 2. 需求分析

### 2.1 功能需求

#### 2.1.1 查询解析模块

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| FR-001 | 支持中文自然语言输入 | P0 |
| FR-002 | 支持英文自然语言输入 | P0 |
| FR-003 | 自动提取疾病/病原体名称 | P0 |
| FR-004 | 自动提取干预类型（如疫苗、药物） | P0 |
| FR-005 | 识别临床试验阶段 | P1 |
| FR-006 | 识别时间范围 | P1 |
| FR-007 | 识别目标人群 | P2 |

#### 2.1.2 数据获取模块

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| FR-010 | 从ClinicalTrials.gov获取试验数据 | P0 |
| FR-011 | 从PubMed获取文献数据 | P0 |
| FR-012 | 支持分页获取大量数据 | P0 |
| FR-013 | 数据获取进度实时反馈 | P1 |
| FR-014 | 支持并行获取多数据源 | P1 |

#### 2.1.3 数据清洗模块

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| FR-020 | 文本字段去空白和特殊字符 | P0 |
| FR-021 | 日期格式标准化（ISO 8601） | P0 |
| FR-022 | 年龄数值提取和单位转换 | P0 |
| FR-023 | 试验状态标准化 | P0 |
| FR-024 | 试验阶段标准化 | P0 |
| FR-025 | 数据质量评分 | P1 |
| FR-026 | 缺失值处理 | P1 |

#### 2.1.4 用户界面模块

| 需求ID | 需求描述 | 优先级 |
|--------|----------|--------|
| FR-030 | 搜索输入框和选项 | P0 |
| FR-031 | 任务进度实时显示 | P0 |
| FR-032 | 结果列表展示 | P0 |
| FR-033 | 数据导出功能 | P0 |
| FR-034 | 搜索历史查看 | P1 |
| FR-035 | 统计信息展示 | P2 |

### 2.2 非功能需求

| 需求ID | 需求描述 | 指标 |
|--------|----------|------|
| NFR-001 | 响应时间 | 单次API调用 < 3秒 |
| NFR-002 | 并发处理 | 支持10个并发用户 |
| NFR-003 | 数据准确性 | LLM解析准确率 > 85% |
| NFR-004 | 可用性 | 系统可用性 > 99% |
| NFR-005 | 可扩展性 | 支持新增数据源 |

---

## 3. 系统设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          表示层 (Presentation Layer)                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Web前端 (Vue 3 SPA)                       │   │
│  │    搜索界面 │ 结果展示 │ 历史记录 │ 统计分析 │ 数据导出    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          网关层 (Gateway Layer)                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Nginx 反向代理                             │   │
│  │              路由分发 │ 静态文件服务 │ 负载均衡              │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          业务层 (Business Layer)                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   FastAPI 应用服务器                         │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │   │
│  │  │ LLM     │ │ 数据    │ │ 数据    │ │ 任务    │           │   │
│  │  │ 解析器  │ │ 获取器  │ │ 清洗器  │ │ 管理器  │           │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                    │           │           │
                    ▼           ▼           ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────────────────────┐
│   Ollama      │ │ 外部数据源    │ │        数据层                 │
│   LLM服务     │ │ ClinicalTrials│ │  ┌─────────────────────────┐ │
│               │ │ PubMed        │ │  │    SQLite 数据库       │ │
│  LLaMA 3.2    │ │               │ │  │  搜索记录 │ 结果数据   │ │
└───────────────┘ └───────────────┘ │  └─────────────────────────┘ │
                                    └───────────────────────────────┘
```

### 3.2 模块设计

#### 3.2.1 LLM查询解析器 (LLMQueryParser)

**职责**: 将自然语言查询转换为结构化查询参数

**核心流程**:
```
用户输入 → 预处理 → LLM调用 → 结果解析 → 后处理 → 结构化输出
                         ↓
                    (失败时)
                         ↓
                    规则解析
```

**输入输出**:
```python
# 输入
query = "查找关于B群脑膜炎球菌疫苗的三期临床试验"

# 输出
{
    "condition": "meningococcal B",
    "intervention": "vaccine",
    "phase": "Phase 3",
    "keywords": ["meningococcal", "vaccine", "B"],
    "data_sources": ["clinicaltrials", "pubmed"]
}
```

#### 3.2.2 数据获取器 (BioDataFetcher)

**职责**: 从外部数据库获取原始数据

**支持的数据源**:
| 数据源 | API | 数据类型 |
|--------|-----|----------|
| ClinicalTrials.gov | REST API v2 | 临床试验 |
| PubMed | E-utilities | 生物医学文献 |

**异常处理**:
- 网络超时自动重试（最多3次）
- API限流处理（自动延迟）
- 错误数据跳过并记录

#### 3.2.3 数据清洗器 (DataCleaningService)

**职责**: 清洗、标准化和质量评估

**清洗规则**:
| 字段类型 | 清洗操作 |
|----------|----------|
| 文本 | 去空白、去特殊字符、截断过长内容 |
| 日期 | 转换为ISO 8601格式 |
| 年龄 | 提取数值、统一为年单位 |
| 状态 | 映射到标准枚举值 |
| 阶段 | 映射到标准格式（PHASE_1等） |

**质量评分算法**:
```
总分 = Σ(字段完整性权重 × 字段是否有效)
     + Σ(数值有效性权重 × 数值是否合理)
     + Σ(日期有效性权重 × 日期是否存在)
```

#### 3.2.4 任务管理器 (TaskManager)

**职责**: 管理异步搜索任务的生命周期

**任务状态机**:
```
        ┌───────────────────────────────────────┐
        │                                       │
        ▼                                       │
    ┌────────┐     ┌────────────┐     ┌────────┴───┐
    │pending │────▶│ processing │────▶│ completed  │
    └────────┘     └────────────┘     └────────────┘
                         │
                         │
                         ▼
                   ┌──────────┐
                   │  failed  │
                   └──────────┘
```

### 3.3 数据流设计

```
1. 搜索请求流程
   
   用户 ──[查询]──▶ API网关 ──▶ 创建任务 ──▶ 返回task_id
                                    │
                                    ▼
                              LLM解析查询
                                    │
                                    ▼
                              数据源检索 (并行)
                              ┌─────┴─────┐
                              ▼           ▼
                         ClinicalTrials  PubMed
                              │           │
                              └─────┬─────┘
                                    ▼
                                数据清洗
                                    │
                                    ▼
                                保存数据库
                                    │
                                    ▼
                                任务完成

2. 结果查询流程
   
   用户 ──[task_id]──▶ 查询任务状态 ──▶ 返回状态/结果
```

---

## 4. 技术实现

### 4.1 技术栈选型

| 层次 | 技术 | 版本 | 选型理由 |
|------|------|------|----------|
| 前端框架 | Vue 3 | 3.x | 响应式、轻量、生态丰富 |
| UI框架 | Tailwind CSS | 3.x | 原子化CSS、高度可定制 |
| 后端框架 | FastAPI | 0.109+ | 异步、高性能、自动文档 |
| 数据库 | SQLite | 3.x | 轻量、无需额外服务 |
| LLM运行时 | Ollama | latest | 本地部署、易于使用 |
| LLM模型 | LLaMA 3.2 | 8B | 开源、性能均衡 |
| 容器化 | Docker | 20.10+ | 标准化部署 |
| 反向代理 | Nginx | alpine | 轻量、高性能 |

### 4.2 核心代码结构

```python
# 后端核心模块关系图

app.py (FastAPI应用)
    │
    ├── services/
    │   ├── llm_parser.py      # LLM查询解析
    │   │   ├── LLMQueryParser     # 主解析器类
    │   │   └── QueryOptimizer     # 查询优化器
    │   │
    │   ├── data_fetcher.py    # 数据获取
    │   │   ├── BioDataFetcher     # 数据获取器
    │   │   └── DataSourceRegistry # 数据源注册
    │   │
    │   ├── data_cleaner.py    # 数据清洗
    │   │   ├── DataCleaningService  # 清洗服务
    │   │   ├── DataIntegrationService # 集成服务
    │   │   └── DataQualityAnalyzer  # 质量分析
    │   │
    │   ├── database.py        # 数据库管理
    │   │   └── DatabaseManager    # 数据库管理器
    │   │
    │   └── task_manager.py    # 任务管理
    │       └── TaskManager        # 任务管理器
    │
    └── models/                # 数据模型 (Pydantic)
        ├── SearchRequest
        ├── SearchResponse
        └── TaskStatusResponse
```

### 4.3 异步处理机制

```python
# 搜索任务异步执行示例

@app.post("/api/search")
async def search(request: SearchRequest, background_tasks: BackgroundTasks):
    # 1. 创建任务
    task_id = task_manager.create_task(request.query)
    
    # 2. LLM解析（同步，快速）
    parsed_query = await llm_parser.parse_query(request.query)
    
    # 3. 后台执行数据获取（异步，耗时）
    background_tasks.add_task(
        execute_search_task,
        task_id=task_id,
        parsed_query=parsed_query,
        ...
    )
    
    # 4. 立即返回任务ID
    return SearchResponse(task_id=task_id, status="processing")
```

---

## 5. 数据库设计

### 5.1 ER图

```
┌─────────────────────┐     ┌─────────────────────┐
│   search_records    │     │   search_results    │
├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │◄───┐│ id (PK)             │
│ query               │    ││ search_id (FK)      │
│ parsed_query (JSON) │    │└─────────────────────┤
│ total_results       │    │  source              │
│ sources (JSON)      │    │  data (JSON)         │
│ created_at          │    │  count               │
│ updated_at          │    │  created_at          │
└─────────────────────┘    └──────────────────────┘
          │
          │ 1:N
          ▼
┌─────────────────────┐     ┌─────────────────────┐
│   clinical_trials   │     │   pubmed_articles   │
├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │     │ id (PK)             │
│ search_id (FK)      │     │ search_id (FK)      │
│ nct_id (UNIQUE)     │     │ pmid (UNIQUE)       │
│ title               │     │ title               │
│ status              │     │ authors             │
│ phase               │     │ journal             │
│ start_date          │     │ publication_date    │
│ completion_date     │     │ doi                 │
│ enrollment          │     │ quality_score       │
│ sponsor             │     │ ...                 │
│ quality_score       │     └─────────────────────┘
│ ...                 │
└─────────────────────┘
```

### 5.2 表结构详细定义

#### search_records 表
| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 主键 |
| query | TEXT | NOT NULL | 原始查询文本 |
| parsed_query | TEXT | | 解析后的JSON |
| total_results | INTEGER | DEFAULT 0 | 总结果数 |
| sources | TEXT | | 数据源JSON数组 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### clinical_trials 表
| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 主键 |
| search_id | INTEGER | FOREIGN KEY | 关联搜索记录 |
| nct_id | TEXT | UNIQUE | ClinicalTrials ID |
| title | TEXT | | 试验标题 |
| status | TEXT | | 试验状态 |
| phase | TEXT | | 试验阶段 |
| start_date | TEXT | | 开始日期 |
| completion_date | TEXT | | 完成日期 |
| enrollment | INTEGER | | 入组人数 |
| sponsor | TEXT | | 赞助商 |
| countries | TEXT | | 国家列表 |
| summary | TEXT | | 摘要 |
| quality_score | REAL | | 质量评分 |
| fetched_at | TIMESTAMP | | 获取时间 |
| cleaned_at | TIMESTAMP | | 清洗时间 |

### 5.3 索引设计

```sql
-- 搜索记录索引
CREATE INDEX idx_search_query ON search_records(query);
CREATE INDEX idx_search_date ON search_records(created_at);

-- 临床试验索引
CREATE INDEX idx_trials_nct ON clinical_trials(nct_id);
CREATE INDEX idx_trials_search ON clinical_trials(search_id);
CREATE INDEX idx_trials_status ON clinical_trials(status);

-- PubMed文献索引
CREATE INDEX idx_pubmed_pmid ON pubmed_articles(pmid);
CREATE INDEX idx_pubmed_search ON pubmed_articles(search_id);
```

---

## 6. API设计

### 6.1 RESTful API规范

**基础URL**: `http://localhost:8000/api`

**通用响应格式**:
```json
{
    "status": "success|error",
    "data": {...},
    "message": "描述信息"
}
```

### 6.2 接口列表

#### 6.2.1 POST /api/search - 创建搜索任务

**请求**:
```json
{
    "query": "B群脑膜炎球菌疫苗临床试验",
    "max_results": 100,
    "sources": ["clinicaltrials", "pubmed"],
    "use_llm": true
}
```

**响应**:
```json
{
    "task_id": "uuid-string",
    "status": "processing",
    "message": "搜索任务已创建，正在后台处理",
    "parsed_query": {
        "condition": "meningococcal B",
        "intervention": "vaccine",
        "keywords": ["meningococcal", "vaccine"]
    }
}
```

#### 6.2.2 GET /api/task/{task_id} - 查询任务状态

**响应**:
```json
{
    "task_id": "uuid-string",
    "status": "completed",
    "progress": 1.0,
    "message": "任务完成",
    "result": {
        "search_id": 1,
        "total_results": 150,
        "sources": {
            "clinicaltrials": 50,
            "pubmed": 100
        }
    }
}
```

#### 6.2.3 GET /api/search/{search_id} - 获取搜索结果详情

#### 6.2.4 GET /api/history - 获取搜索历史

#### 6.2.5 POST /api/export - 导出数据

#### 6.2.6 GET /api/stats - 获取统计信息

#### 6.2.7 DELETE /api/search/{search_id} - 删除搜索记录

---

## 7. 部署方案

### 7.1 Docker部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Host                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                  Docker Network                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │  frontend   │  │   backend   │  │   ollama    │   │ │
│  │  │   :80       │  │   :8000     │  │   :11434    │   │ │
│  │  │   nginx     │  │   uvicorn   │  │   llama3.2  │   │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │ │
│  │         │                │                │           │ │
│  │         └────────────────┼────────────────┘           │ │
│  │                          │                            │ │
│  └──────────────────────────┼────────────────────────────┘ │
│                             │                              │
│  ┌──────────────────────────┼────────────────────────────┐ │
│  │                    Volumes                            │ │
│  │   bioinfo-data/          │         ollama-data/       │ │
│  │   └── bioinfo.db         │         └── models/        │ │
│  └──────────────────────────┴────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 资源需求

| 组件 | CPU | 内存 | 存储 |
|------|-----|------|------|
| Frontend (Nginx) | 0.1 核 | 128MB | 50MB |
| Backend (FastAPI) | 1 核 | 512MB | 500MB |
| Ollama (LLaMA 3.2) | 2 核 | 8GB | 5GB |
| **总计（最小）** | **3 核** | **9GB** | **6GB** |

### 7.3 部署命令

```bash
# GPU模式
docker compose -f docker-compose.yml up -d

# CPU模式
docker compose -f docker-compose.cpu.yml up -d

# 查看日志
docker compose logs -f backend

# 停止服务
docker compose down
```

---

## 8. 测试方案

### 8.1 测试类型

| 测试类型 | 工具 | 覆盖范围 |
|----------|------|----------|
| 单元测试 | pytest | 核心业务逻辑 |
| 集成测试 | pytest + httpx | API接口 |
| E2E测试 | Playwright | 用户流程 |
| 性能测试 | locust | 并发负载 |

### 8.2 测试用例示例

```python
# 单元测试 - LLM解析器
class TestLLMParser:
    def test_parse_chinese_query(self):
        parser = LLMQueryParser()
        result = parser._rule_based_parse("B群脑膜炎疫苗临床试验")
        assert "meningococcal" in result["condition"].lower()
        assert "vaccine" in result["intervention"].lower()

# 集成测试 - 搜索API
class TestSearchAPI:
    async def test_search_endpoint(self):
        async with AsyncClient() as client:
            response = await client.post(
                "/api/search",
                json={"query": "COVID-19 vaccine", "max_results": 10}
            )
            assert response.status_code == 200
            assert "task_id" in response.json()
```

---

## 9. 性能优化

### 9.1 优化策略

| 优化点 | 策略 | 预期效果 |
|--------|------|----------|
| LLM推理 | GPU加速 | 响应时间减少80% |
| 数据获取 | 并行请求 | 获取时间减少50% |
| 数据库 | 索引优化 | 查询时间减少70% |
| 前端 | CDN缓存 | 加载时间减少60% |

### 9.2 缓存策略

```python
# LLM解析结果缓存
QUERY_CACHE = {}  # 简单内存缓存

async def parse_query_cached(query: str):
    cache_key = hash(query)
    if cache_key in QUERY_CACHE:
        return QUERY_CACHE[cache_key]
    
    result = await llm_parser.parse_query(query)
    QUERY_CACHE[cache_key] = result
    return result
```

---

## 10. 安全考虑

### 10.1 安全措施

| 风险 | 措施 |
|------|------|
| SQL注入 | 使用参数化查询 |
| XSS攻击 | 前端输入过滤 |
| API滥用 | 请求频率限制 |
| 数据泄露 | 敏感信息脱敏 |

### 10.2 数据隐私

- 不存储用户个人信息
- 搜索历史仅存储在本地
- 可配置数据保留期限

---

## 11. 扩展计划

### 11.1 短期计划（1-3个月）

- [ ] 添加WHO临床试验数据源
- [ ] 支持更多LLM模型（Qwen、DeepSeek）
- [ ] 实现用户认证功能
- [ ] 添加数据可视化图表

### 11.2 中期计划（3-6个月）

- [ ] 支持全文文献分析
- [ ] 实现智能推荐功能
- [ ] 添加多语言界面
- [ ] 开发移动端应用

### 11.3 长期计划（6-12个月）

- [ ] 构建知识图谱
- [ ] 实现自动化报告生成
- [ ] 支持团队协作功能
- [ ] 开放API供第三方使用

---

## 附录

### A. 术语表

| 术语 | 说明 |
|------|------|
| LLM | Large Language Model，大语言模型 |
| NCT ID | ClinicalTrials.gov的唯一标识符 |
| PMID | PubMed的唯一标识符 |
| ISO 8601 | 国际日期时间标准格式 |

### B. 参考文献

1. ClinicalTrials.gov API Documentation
2. PubMed E-utilities Documentation
3. FastAPI Documentation
4. Ollama Documentation

### C. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0.0 | 2025-01 | 初始版本 |

---

**文档结束**
