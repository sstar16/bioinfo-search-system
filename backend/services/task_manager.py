#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理服务
管理异步搜索任务的状态和生命周期
"""

import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any


class TaskManager:
    """任务管理器"""
    
    def __init__(self, max_tasks: int = 1000, task_ttl_hours: int = 24):
        self.tasks: Dict[str, Dict] = {}
        self.max_tasks = max_tasks
        self.task_ttl = timedelta(hours=task_ttl_hours)
        self._lock = threading.Lock()
    
    def create_task(self, query: str) -> str:
        """
        创建新任务
        
        Args:
            query: 搜索查询
            
        Returns:
            任务ID
        """
        with self._lock:
            # 清理过期任务
            self._cleanup_expired_tasks()
            
            # 如果任务数超限，清理最旧的已完成任务
            if len(self.tasks) >= self.max_tasks:
                self._cleanup_old_tasks()
            
            task_id = str(uuid.uuid4())
            self.tasks[task_id] = {
                "id": task_id,
                "query": query,
                "status": "pending",
                "progress": 0.0,
                "message": "任务已创建",
                "result": None,
                "error": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            return task_id
    
    def update_task(
        self, 
        task_id: str, 
        status: Optional[str] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None
    ):
        """更新任务状态"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                
                if status:
                    task["status"] = status
                if progress is not None:
                    task["progress"] = min(max(progress, 0.0), 1.0)
                if message:
                    task["message"] = message
                
                task["updated_at"] = datetime.now().isoformat()
    
    def complete_task(self, task_id: str, result: Any):
        """完成任务"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].update({
                    "status": "completed",
                    "progress": 1.0,
                    "message": "任务完成",
                    "result": result,
                    "completed_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })
    
    def fail_task(self, task_id: str, error: str):
        """标记任务失败"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].update({
                    "status": "failed",
                    "message": "任务失败",
                    "error": error,
                    "updated_at": datetime.now().isoformat()
                })
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        with self._lock:
            return self.tasks.get(task_id)
    
    def list_tasks(
        self, 
        status: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """列出任务"""
        with self._lock:
            tasks = list(self.tasks.values())
            
            if status:
                tasks = [t for t in tasks if t["status"] == status]
            
            # 按创建时间倒序
            tasks.sort(key=lambda x: x["created_at"], reverse=True)
            
            return tasks[:limit]
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                return True
            return False
    
    def _cleanup_expired_tasks(self):
        """清理过期任务"""
        now = datetime.now()
        expired = []
        
        for task_id, task in self.tasks.items():
            created_at = datetime.fromisoformat(task["created_at"])
            if now - created_at > self.task_ttl:
                expired.append(task_id)
        
        for task_id in expired:
            del self.tasks[task_id]
    
    def _cleanup_old_tasks(self):
        """清理最旧的已完成任务"""
        # 找出已完成或失败的任务
        completed = [
            (tid, task["created_at"]) 
            for tid, task in self.tasks.items()
            if task["status"] in ["completed", "failed"]
        ]
        
        # 按时间排序，删除最旧的一半
        completed.sort(key=lambda x: x[1])
        to_delete = completed[:len(completed) // 2]
        
        for task_id, _ in to_delete:
            del self.tasks[task_id]


class TaskStatus:
    """任务状态常量"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
