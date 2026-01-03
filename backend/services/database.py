#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理服务
使用SQLite存储搜索历史和结果数据
"""

import os
import json
import aiosqlite
from datetime import datetime
from typing import Dict, List, Optional, Any


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
    
    async def init_db(self):
        """初始化数据库"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            # 创建搜索记录表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS search_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    parsed_query TEXT,
                    total_results INTEGER DEFAULT 0,
                    sources TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建临床试验数据表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS clinical_trials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_id INTEGER,
                    nct_id TEXT UNIQUE,
                    title TEXT,
                    official_title TEXT,
                    status TEXT,
                    phase TEXT,
                    start_date TEXT,
                    completion_date TEXT,
                    enrollment INTEGER,
                    study_type TEXT,
                    allocation TEXT,
                    vaccine_names TEXT,
                    sponsor TEXT,
                    collaborators TEXT,
                    countries TEXT,
                    num_locations INTEGER,
                    primary_outcome TEXT,
                    min_age_years REAL,
                    max_age_years REAL,
                    sex TEXT,
                    summary TEXT,
                    url TEXT,
                    quality_score REAL,
                    fetched_at TIMESTAMP,
                    cleaned_at TIMESTAMP,
                    FOREIGN KEY (search_id) REFERENCES search_records(id)
                )
            """)
            
            # 创建PubMed文献表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS pubmed_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_id INTEGER,
                    pmid TEXT UNIQUE,
                    title TEXT,
                    authors TEXT,
                    journal TEXT,
                    publication_date TEXT,
                    volume TEXT,
                    issue TEXT,
                    pages TEXT,
                    doi TEXT,
                    pub_type TEXT,
                    url TEXT,
                    quality_score REAL,
                    fetched_at TIMESTAMP,
                    cleaned_at TIMESTAMP,
                    FOREIGN KEY (search_id) REFERENCES search_records(id)
                )
            """)
            
            # 创建搜索结果关联表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS search_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_id INTEGER,
                    source TEXT,
                    data TEXT,
                    count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (search_id) REFERENCES search_records(id)
                )
            """)
            
            # 创建索引
            await db.execute("CREATE INDEX IF NOT EXISTS idx_search_query ON search_records(query)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_search_date ON search_records(created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_trials_nct ON clinical_trials(nct_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_trials_search ON clinical_trials(search_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_pubmed_pmid ON pubmed_articles(pmid)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_pubmed_search ON pubmed_articles(search_id)")
            
            await db.commit()
            print(f"✓ 数据库初始化完成: {self.db_path}")
    
    async def close(self):
        """关闭数据库连接"""
        pass  # aiosqlite 使用上下文管理器，不需要显式关闭
    
    async def save_search_record(
        self, 
        query: str, 
        parsed_query: Dict,
        results: List[Dict]
    ) -> int:
        """
        保存搜索记录和结果
        
        Returns:
            搜索记录ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            # 计算总结果数
            total_results = sum(r.get("count", 0) for r in results)
            # 修复：存储为 {source: count} 格式
            sources = {r.get("source"): r.get("count", 0) for r in results}
            
            # 插入搜索记录
            cursor = await db.execute(
                """
                INSERT INTO search_records (query, parsed_query, total_results, sources)
                VALUES (?, ?, ?, ?)
                """,
                (query, json.dumps(parsed_query, ensure_ascii=False), total_results, json.dumps(sources))
            )
            search_id = cursor.lastrowid
            
            # 保存各数据源结果
            for result in results:
                source = result.get("source")
                data = result.get("data", [])
                count = result.get("count", len(data))
                
                # 保存结果摘要
                await db.execute(
                    """
                    INSERT INTO search_results (search_id, source, data, count)
                    VALUES (?, ?, ?, ?)
                    """,
                    (search_id, source, json.dumps(data, ensure_ascii=False, default=str), count)
                )
                
                # 保存详细数据到对应表
                if source == "clinicaltrials":
                    await self._save_clinical_trials(db, search_id, data)
                elif source == "pubmed":
                    await self._save_pubmed_articles(db, search_id, data)
            
            await db.commit()
            return search_id
    
    async def _save_clinical_trials(self, db, search_id: int, data: List[Dict]):
        """保存临床试验数据"""
        for item in data:
            try:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO clinical_trials (
                        search_id, nct_id, title, official_title, status, phase,
                        start_date, completion_date, enrollment, study_type, allocation,
                        vaccine_names, sponsor, collaborators, countries, num_locations,
                        primary_outcome, min_age_years, max_age_years, sex, summary,
                        url, quality_score, fetched_at, cleaned_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        search_id,
                        item.get("nct_id"),
                        item.get("title"),
                        item.get("official_title"),
                        item.get("status"),
                        item.get("phase"),
                        item.get("start_date"),
                        item.get("completion_date"),
                        item.get("enrollment"),
                        item.get("study_type"),
                        item.get("allocation"),
                        item.get("vaccine_names"),
                        item.get("sponsor"),
                        item.get("collaborators"),
                        item.get("countries"),
                        item.get("num_locations"),
                        item.get("primary_outcome"),
                        item.get("min_age_years"),
                        item.get("max_age_years"),
                        item.get("sex"),
                        item.get("summary"),
                        item.get("url"),
                        item.get("quality_score"),
                        item.get("fetched_at"),
                        item.get("cleaned_at")
                    )
                )
            except Exception as e:
                print(f"保存临床试验数据错误: {e}")
    
    async def _save_pubmed_articles(self, db, search_id: int, data: List[Dict]):
        """保存PubMed文献数据"""
        for item in data:
            try:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO pubmed_articles (
                        search_id, pmid, title, authors, journal, publication_date,
                        volume, issue, pages, doi, pub_type, url,
                        quality_score, fetched_at, cleaned_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        search_id,
                        item.get("pmid"),
                        item.get("title"),
                        item.get("authors"),
                        item.get("journal"),
                        item.get("publication_date"),
                        item.get("volume"),
                        item.get("issue"),
                        item.get("pages"),
                        item.get("doi"),
                        item.get("pub_type"),
                        item.get("url"),
                        item.get("quality_score"),
                        item.get("fetched_at"),
                        item.get("cleaned_at")
                    )
                )
            except Exception as e:
                print(f"保存PubMed数据错误: {e}")
    
    async def get_search_history(
        self, 
        page: int = 1, 
        page_size: int = 20,
        keyword: Optional[str] = None
    ) -> Dict:
        """获取搜索历史"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # 构建查询
            where_clause = ""
            params = []
            
            if keyword:
                where_clause = "WHERE query LIKE ?"
                params.append(f"%{keyword}%")
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) FROM search_records {where_clause}"
            cursor = await db.execute(count_sql, params)
            total = (await cursor.fetchone())[0]
            
            # 获取分页数据
            offset = (page - 1) * page_size
            query_sql = f"""
                SELECT id, query, parsed_query, total_results, sources, created_at
                FROM search_records
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            
            cursor = await db.execute(query_sql, params + [page_size, offset])
            rows = await cursor.fetchall()
            
            history = []
            for row in rows:
                history.append({
                    "id": row["id"],
                    "query": row["query"],
                    "parsed_query": json.loads(row["parsed_query"]) if row["parsed_query"] else None,
                    "total_results": row["total_results"],
                    "sources": json.loads(row["sources"]) if row["sources"] else [],
                    "created_at": row["created_at"]
                })
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "data": history
            }
    
    async def get_search_detail(self, search_id: int) -> Optional[Dict]:
        """获取搜索详情"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # 获取搜索记录
            cursor = await db.execute(
                "SELECT * FROM search_records WHERE id = ?",
                (search_id,)
            )
            record = await cursor.fetchone()
            
            if not record:
                return None
            
            # 获取结果数据
            cursor = await db.execute(
                "SELECT * FROM search_results WHERE search_id = ?",
                (search_id,)
            )
            result_rows = await cursor.fetchall()
            
            results = []
            sources_count = {}
            for row in result_rows:
                source = row["source"]
                count = row["count"]
                results.append({
                    "source": source,
                    "count": count,
                    "data": json.loads(row["data"]) if row["data"] else []
                })
                sources_count[source] = count
            
            return {
                "id": record["id"],
                "query": record["query"],
                "parsed_query": json.loads(record["parsed_query"]) if record["parsed_query"] else None,
                "total_results": record["total_results"],
                "sources": sources_count,  # 使用实际统计的count
                "created_at": record["created_at"],
                "results": results
            }
    
    async def delete_search_record(self, search_id: int):
        """删除搜索记录"""
        async with aiosqlite.connect(self.db_path) as db:
            # 删除关联数据
            await db.execute("DELETE FROM search_results WHERE search_id = ?", (search_id,))
            await db.execute("DELETE FROM clinical_trials WHERE search_id = ?", (search_id,))
            await db.execute("DELETE FROM pubmed_articles WHERE search_id = ?", (search_id,))
            # 删除主记录
            await db.execute("DELETE FROM search_records WHERE id = ?", (search_id,))
            await db.commit()
    
    async def get_statistics(self) -> Dict:
        """获取系统统计信息"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # 总搜索次数
            cursor = await db.execute("SELECT COUNT(*) FROM search_records")
            stats["total_searches"] = (await cursor.fetchone())[0]
            
            # 总临床试验数
            cursor = await db.execute("SELECT COUNT(DISTINCT nct_id) FROM clinical_trials")
            stats["total_trials"] = (await cursor.fetchone())[0]
            
            # 总文献数
            cursor = await db.execute("SELECT COUNT(DISTINCT pmid) FROM pubmed_articles")
            stats["total_articles"] = (await cursor.fetchone())[0]
            
            # 最近7天搜索趋势
            cursor = await db.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM search_records
                WHERE created_at >= DATE('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            stats["recent_searches"] = [
                {"date": row[0], "count": row[1]}
                for row in await cursor.fetchall()
            ]
            
            # 热门搜索词
            cursor = await db.execute("""
                SELECT query, COUNT(*) as count
                FROM search_records
                GROUP BY query
                ORDER BY count DESC
                LIMIT 10
            """)
            stats["popular_queries"] = [
                {"query": row[0], "count": row[1]}
                for row in await cursor.fetchall()
            ]
            
            # 数据源分布
            cursor = await db.execute("""
                SELECT source, SUM(count) as total
                FROM search_results
                GROUP BY source
            """)
            stats["source_distribution"] = {
                row[0]: row[1]
                for row in await cursor.fetchall()
            }
            
            return stats
    
    async def get_trials_by_condition(self, condition: str, limit: int = 100) -> List[Dict]:
        """按条件查询临床试验"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                """
                SELECT * FROM clinical_trials
                WHERE title LIKE ? OR summary LIKE ?
                ORDER BY quality_score DESC
                LIMIT ?
                """,
                (f"%{condition}%", f"%{condition}%", limit)
            )
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_articles_by_keyword(self, keyword: str, limit: int = 100) -> List[Dict]:
        """按关键词查询文献"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                """
                SELECT * FROM pubmed_articles
                WHERE title LIKE ?
                ORDER BY quality_score DESC
                LIMIT ?
                """,
                (f"%{keyword}%", limit)
            )
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
