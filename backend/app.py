#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BioInfo Search System - 后端主应用
基于FastAPI的生物信息智能检索系统
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# 导入自定义模块
from services.llm_parser import LLMQueryParser
from services.enhanced_data_fetcher import EnhancedBioDataFetcher, EnhancedDataSourceRegistry
from services.data_cleaner import DataCleaningService
from services.database import DatabaseManager
from services.task_manager import TaskManager

# 配置
DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DB_PATH = os.environ.get("DB_PATH", "/app/data/bioinfo.db")

# 全局任务管理器
task_manager = TaskManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(f"{DATA_DIR}/exports", exist_ok=True)
    os.makedirs(f"{DATA_DIR}/logs", exist_ok=True)
    
    # 初始化数据库
    db = DatabaseManager(DB_PATH)
    await db.init_db()
    app.state.db = db
    
    # 初始化LLM解析器
    app.state.llm_parser = LLMQueryParser(OLLAMA_HOST)
    
    # 初始化数据获取器（增强版）
    app.state.data_fetcher = EnhancedBioDataFetcher()
    
    # 初始化数据清洗服务
    app.state.data_cleaner = DataCleaningService()
    
    print("🚀 BioInfo Search System 启动成功!")
    print(f"📁 数据目录: {DATA_DIR}")
    print(f"🤖 Ollama 地址: {OLLAMA_HOST}")
    
    yield
    
    # 关闭时清理
    await db.close()
    print("👋 BioInfo Search System 已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="BioInfo Search System",
    description="基于LLM的生物信息智能检索系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 数据模型 ====================

class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="自然语言查询", min_length=2, max_length=1000)
    max_results: int = Field(default=100, ge=1, le=1000, description="最大结果数")
    sources: List[str] = Field(default=["clinicaltrials", "pubmed"], description="数据源")
    use_llm: bool = Field(default=True, description="是否使用LLM解析")

class SearchResponse(BaseModel):
    """搜索响应模型"""
    task_id: str
    status: str
    message: str
    parsed_query: Optional[Dict] = None

class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: float
    message: str
    result: Optional[Dict] = None
    error: Optional[str] = None

class DataExportRequest(BaseModel):
    """数据导出请求"""
    task_id: str
    format: str = Field(default="csv", pattern="^(csv|xlsx|json)$")

class HistoryQuery(BaseModel):
    """历史查询"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    keyword: Optional[str] = None

# ==================== API路由 ====================

@app.get("/")
async def root():
    """根路由 - 系统信息"""
    return {
        "name": "BioInfo Search System",
        "version": "1.0.0",
        "description": "基于LLM的生物信息智能检索系统",
        "endpoints": {
            "search": "/api/search",
            "status": "/api/task/{task_id}",
            "history": "/api/history",
            "export": "/api/export"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ollama_status": await app.state.llm_parser.check_connection()
    }

@app.get("/api/sources")
async def get_available_sources():
    """获取可用数据源列表"""
    return {
        "sources": EnhancedDataSourceRegistry.get_available_sources(),
        "categories": {
            "clinical_trials": EnhancedDataSourceRegistry.get_sources_by_category("clinical_trials"),
            "literature": EnhancedDataSourceRegistry.get_sources_by_category("literature")
        }
    }

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    执行生物信息搜索
    
    1. 使用LLM解析自然语言查询
    2. 调用相应API获取数据
    3. 清洗和整合数据
    4. 保存到数据库
    """
    try:
        # 创建任务
        task_id = task_manager.create_task(request.query)
        
        # 如果使用LLM，先解析查询
        parsed_query = None
        if request.use_llm:
            try:
                parsed_query = await app.state.llm_parser.parse_query(request.query)
                task_manager.update_task(task_id, progress=0.1, message="查询解析完成")
            except Exception as e:
                # LLM解析失败，使用简单解析
                parsed_query = {"keywords": request.query.split(), "original": request.query}
                task_manager.update_task(task_id, progress=0.1, message=f"使用简单解析: {str(e)}")
        else:
            parsed_query = {"keywords": request.query.split(), "original": request.query}
        
        # 在后台执行数据获取任务
        background_tasks.add_task(
            execute_search_task,
            task_id=task_id,
            parsed_query=parsed_query,
            sources=request.sources,
            max_results=request.max_results,
            db=app.state.db,
            fetcher=app.state.data_fetcher,
            cleaner=app.state.data_cleaner
        )
        
        return SearchResponse(
            task_id=task_id,
            status="processing",
            message="搜索任务已创建，正在后台处理",
            parsed_query=parsed_query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def execute_search_task(
    task_id: str,
    parsed_query: Dict,
    sources: List[str],
    max_results: int,
    db: DatabaseManager,
    fetcher: EnhancedBioDataFetcher,
    cleaner: DataCleaningService
):
    """后台执行搜索任务"""
    try:
        # 获取关键词
        keywords = parsed_query.get("keywords", [])
        condition = parsed_query.get("condition", "")
        search_term = condition if condition else " ".join(keywords)
        
        if not search_term:
            search_term = parsed_query.get("original", "")
        
        # 使用聚合搜索方法获取所有数据源的数据
        task_manager.update_task(
            task_id, 
            progress=0.2,
            message=f"正在从 {len(sources)} 个数据源获取数据..."
        )
        
        # 调用增强版数据获取器的聚合搜索方法
        raw_results = await fetcher.fetch_all(
            search_term=search_term,
            sources=sources,
            max_results=max_results,
            enrich_oa=True  # 自动添加开放获取信息
        )
        
        # 转换结果格式
        all_results = []
        for source, data in raw_results.items():
            task_manager.update_task(
                task_id, 
                progress=0.4,
                message=f"已获取 {source} 数据: {len(data)} 条"
            )
            all_results.append({
                "source": source,
                "data": data,
                "count": len(data) if data else 0
            })
        
        # 数据清洗
        task_manager.update_task(task_id, progress=0.7, message="正在清洗数据...")
        cleaned_results = []
        for result in all_results:
            if result["data"]:
                cleaned_data = cleaner.clean_data(result["data"], result["source"])
                cleaned_results.append({
                    "source": result["source"],
                    "data": cleaned_data,
                    "count": len(cleaned_data),
                    "original_count": result["count"]
                })
            else:
                cleaned_results.append(result)
        
        # 保存到数据库
        task_manager.update_task(task_id, progress=0.9, message="正在保存数据...")
        search_record_id = await db.save_search_record(
            query=parsed_query.get("original", search_term),
            parsed_query=parsed_query,
            results=cleaned_results
        )
        
        # 完成任务
        summary = {
            "search_id": search_record_id,
            "total_results": sum(r["count"] for r in cleaned_results),
            "sources": {r["source"]: r["count"] for r in cleaned_results},
            "query": parsed_query
        }
        
        task_manager.complete_task(task_id, summary)
        
    except Exception as e:
        task_manager.fail_task(task_id, str(e))

@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        message=task["message"],
        result=task.get("result"),
        error=task.get("error")
    )

@app.get("/api/history")
async def get_search_history(page: int = 1, page_size: int = 20, keyword: Optional[str] = None):
    """获取搜索历史"""
    try:
        history = await app.state.db.get_search_history(page, page_size, keyword)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/{search_id}")
async def get_search_detail(search_id: int):
    """获取搜索详情"""
    try:
        detail = await app.state.db.get_search_detail(search_id)
        if not detail:
            raise HTTPException(status_code=404, detail="搜索记录不存在")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export")
async def export_data(request: DataExportRequest):
    """导出数据"""
    try:
        # 获取任务结果
        task = task_manager.get_task(request.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task["status"] != "completed":
            raise HTTPException(status_code=400, detail="任务尚未完成")
        
        # 获取搜索结果
        search_id = task["result"]["search_id"]
        detail = await app.state.db.get_search_detail(search_id)
        
        # 导出文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bioinfo_export_{timestamp}.{request.format}"
        filepath = f"{DATA_DIR}/exports/{filename}"
        
        if request.format == "csv":
            await export_to_csv(detail["results"], filepath)
        elif request.format == "xlsx":
            await export_to_xlsx(detail["results"], filepath)
        elif request.format == "json":
            await export_to_json(detail["results"], filepath)
        
        return {
            "status": "success",
            "filename": filename,
            "download_url": f"/api/download/{filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/{search_id}")
async def export_by_search_id(search_id: int, format: str = "csv"):
    """根据搜索ID导出数据"""
    try:
        # 验证格式
        if format not in ["csv", "xlsx", "json"]:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
        # 获取搜索结果
        detail = await app.state.db.get_search_detail(search_id)
        if not detail:
            raise HTTPException(status_code=404, detail="搜索记录不存在")
        
        # 导出文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bioinfo_export_{timestamp}.{format}"
        filepath = f"{DATA_DIR}/exports/{filename}"
        
        if format == "csv":
            await export_to_csv(detail["results"], filepath)
        elif format == "xlsx":
            await export_to_xlsx(detail["results"], filepath)
        elif format == "json":
            await export_to_json(detail["results"], filepath)
        
        return {
            "status": "success",
            "filename": filename,
            "download_url": f"/api/download/{filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """下载导出的文件"""
    filepath = f"{DATA_DIR}/exports/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath, filename=filename)

@app.delete("/api/search/{search_id}")
async def delete_search_record(search_id: int):
    """删除搜索记录"""
    try:
        await app.state.db.delete_search_record(search_id)
        return {"status": "success", "message": "删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_statistics():
    """获取系统统计信息"""
    try:
        stats = await app.state.db.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== WebSocket实时更新 ====================

@app.websocket("/ws/task/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    """WebSocket实时任务状态更新"""
    await websocket.accept()
    try:
        while True:
            task = task_manager.get_task(task_id)
            if task:
                await websocket.send_json(task)
                if task["status"] in ["completed", "failed"]:
                    break
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

# ==================== 辅助函数 ====================

async def export_to_csv(results: List[Dict], filepath: str):
    """导出为CSV"""
    import pandas as pd
    all_data = []
    for source_result in results:
        for item in source_result.get("data", []):
            item["_source"] = source_result["source"]
            all_data.append(item)
    
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')

async def export_to_xlsx(results: List[Dict], filepath: str):
    """导出为Excel"""
    import pandas as pd
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for source_result in results:
            source = source_result["source"]
            data = source_result.get("data", [])
            if data:
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=source[:31], index=False)

async def export_to_json(results: List[Dict], filepath: str):
    """导出为JSON"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )