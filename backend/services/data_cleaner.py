#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据清洗服务
对获取的生物信息数据进行标准化清洗和处理
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd


class DataCleaningService:
    """数据清洗服务"""
    
    def __init__(self):
        self.cleaning_log = []
        
    def clean_data(self, data: List[Dict], source: str) -> List[Dict]:
        """
        清洗数据
        
        Args:
            data: 原始数据列表
            source: 数据源标识
            
        Returns:
            清洗后的数据列表
        """
        if not data:
            return []
        
        if source == "clinicaltrials":
            return self._clean_clinical_trials(data)
        elif source == "pubmed":
            return self._clean_pubmed(data)
        elif source == "semantic_scholar":
            return self._clean_semantic_scholar(data)
        elif source in ["biorxiv", "medrxiv"]:
            return self._clean_preprint(data)
        elif source == "openalex":
            return self._clean_openalex(data)
        elif source == "europe_pmc":
            return self._clean_europe_pmc(data)
        else:
            return self._generic_clean(data)
    
    def _clean_clinical_trials(self, data: List[Dict]) -> List[Dict]:
        """清洗临床试验数据"""
        cleaned = []
        
        for item in data:
            cleaned_item = {}
            
            # 基本字段清洗
            cleaned_item["nct_id"] = self._clean_text(item.get("nct_id", ""))
            cleaned_item["title"] = self._clean_text(item.get("title", ""))
            cleaned_item["official_title"] = self._clean_text(item.get("official_title", ""))
            
            # 状态标准化
            cleaned_item["status"] = self._standardize_status(item.get("status", ""))
            
            # 阶段标准化
            cleaned_item["phase"] = self._standardize_phase(item.get("phase", ""))
            
            # 日期标准化
            cleaned_item["start_date"] = self._standardize_date(item.get("start_date"))
            cleaned_item["completion_date"] = self._standardize_date(item.get("completion_date"))
            
            # 数值处理
            cleaned_item["enrollment"] = self._extract_number(item.get("enrollment", 0))
            cleaned_item["num_locations"] = self._extract_number(item.get("num_locations", 0))
            
            # 年龄提取
            cleaned_item["min_age_years"] = self._extract_age(item.get("min_age", ""))
            cleaned_item["max_age_years"] = self._extract_age(item.get("max_age", ""))
            
            # 文本字段
            cleaned_item["study_type"] = self._clean_text(item.get("study_type", ""))
            cleaned_item["allocation"] = self._clean_text(item.get("allocation", ""))
            cleaned_item["vaccine_names"] = self._clean_text(item.get("vaccine_names", ""))
            cleaned_item["all_interventions"] = self._clean_text(item.get("all_interventions", ""))
            cleaned_item["sponsor"] = self._clean_text(item.get("sponsor", ""))
            cleaned_item["collaborators"] = self._clean_text(item.get("collaborators", "")) or "N/A"
            cleaned_item["countries"] = self._clean_text(item.get("countries", "")) or "N/A"
            cleaned_item["primary_outcome"] = self._clean_text(item.get("primary_outcome", ""))
            cleaned_item["summary"] = self._clean_text(item.get("summary", ""))
            
            # 其他字段
            cleaned_item["sex"] = self._clean_text(item.get("sex", ""))
            cleaned_item["healthy_volunteers"] = item.get("healthy_volunteers", "")
            cleaned_item["url"] = item.get("url", "")
            cleaned_item["source"] = "clinicaltrials"
            cleaned_item["fetched_at"] = item.get("fetched_at", datetime.now().isoformat())
            cleaned_item["cleaned_at"] = datetime.now().isoformat()
            
            # 数据质量标记
            cleaned_item["quality_score"] = self._calculate_quality_score(cleaned_item)
            
            cleaned.append(cleaned_item)
        
        return cleaned
    
    def _clean_pubmed(self, data: List[Dict]) -> List[Dict]:
        """清洗PubMed文献数据"""
        cleaned = []
        
        for item in data:
            cleaned_item = {}
            
            cleaned_item["pmid"] = self._clean_text(item.get("pmid", ""))
            cleaned_item["title"] = self._clean_text(item.get("title", ""))
            cleaned_item["authors"] = self._clean_text(item.get("authors", ""))
            cleaned_item["journal"] = self._clean_text(item.get("journal", ""))
            cleaned_item["publication_date"] = self._standardize_date(item.get("publication_date"))
            cleaned_item["volume"] = self._clean_text(item.get("volume", ""))
            cleaned_item["issue"] = self._clean_text(item.get("issue", ""))
            cleaned_item["pages"] = self._clean_text(item.get("pages", ""))
            cleaned_item["doi"] = self._clean_text(item.get("doi", ""))
            cleaned_item["pub_type"] = self._clean_text(item.get("pub_type", ""))
            cleaned_item["url"] = item.get("url", "")
            cleaned_item["source"] = "pubmed"
            cleaned_item["fetched_at"] = item.get("fetched_at", datetime.now().isoformat())
            cleaned_item["cleaned_at"] = datetime.now().isoformat()
            
            # 数据质量标记
            cleaned_item["quality_score"] = self._calculate_pubmed_quality(cleaned_item)
            
            cleaned.append(cleaned_item)
        
        return cleaned
    
    def _clean_semantic_scholar(self, data: List[Dict]) -> List[Dict]:
        """清洗Semantic Scholar数据"""
        cleaned = []
        
        for item in data:
            cleaned_item = {}
            
            cleaned_item["paper_id"] = self._clean_text(item.get("paper_id", ""))
            cleaned_item["title"] = self._clean_text(item.get("title", ""))
            cleaned_item["abstract"] = self._clean_text(item.get("abstract", ""))
            cleaned_item["authors"] = self._clean_text(item.get("authors", ""))
            cleaned_item["year"] = item.get("year")
            cleaned_item["publication_date"] = self._standardize_date(item.get("publication_date"))
            cleaned_item["venue"] = self._clean_text(item.get("venue", ""))
            cleaned_item["journal"] = self._clean_text(item.get("journal", ""))
            cleaned_item["citation_count"] = item.get("citation_count", 0)
            cleaned_item["influential_citation_count"] = item.get("influential_citation_count", 0)
            cleaned_item["fields_of_study"] = item.get("fields_of_study", [])
            cleaned_item["doi"] = self._clean_text(item.get("doi", ""))
            cleaned_item["pmid"] = self._clean_text(item.get("pmid", ""))
            cleaned_item["open_access_pdf"] = item.get("open_access_pdf")
            cleaned_item["pdf_url"] = item.get("pdf_url") or item.get("open_access_pdf")
            cleaned_item["url"] = item.get("url", "")
            cleaned_item["source"] = "semantic_scholar"
            cleaned_item["fetched_at"] = item.get("fetched_at", datetime.now().isoformat())
            cleaned_item["cleaned_at"] = datetime.now().isoformat()
            
            # 质量评分（基于引用数）
            cleaned_item["quality_score"] = self._calculate_ss_quality(cleaned_item)
            
            cleaned.append(cleaned_item)
        
        return cleaned
    
    def _clean_preprint(self, data: List[Dict]) -> List[Dict]:
        """清洗预印本数据（bioRxiv/medRxiv）"""
        cleaned = []
        
        for item in data:
            cleaned_item = {}
            
            cleaned_item["doi"] = self._clean_text(item.get("doi", ""))
            cleaned_item["title"] = self._clean_text(item.get("title", ""))
            cleaned_item["abstract"] = self._clean_text(item.get("abstract", ""))
            cleaned_item["authors"] = self._clean_text(item.get("authors", ""))
            cleaned_item["publication_date"] = self._standardize_date(item.get("publication_date"))
            cleaned_item["category"] = self._clean_text(item.get("category", ""))
            cleaned_item["version"] = item.get("version")
            cleaned_item["pdf_url"] = item.get("pdf_url")
            cleaned_item["url"] = item.get("url", "")
            cleaned_item["server"] = item.get("server", "")
            cleaned_item["source"] = item.get("source", "biorxiv")
            cleaned_item["fetched_at"] = item.get("fetched_at", datetime.now().isoformat())
            cleaned_item["cleaned_at"] = datetime.now().isoformat()
            
            # 预印本质量评分
            cleaned_item["quality_score"] = self._calculate_preprint_quality(cleaned_item)
            
            cleaned.append(cleaned_item)
        
        return cleaned
    
    def _clean_openalex(self, data: List[Dict]) -> List[Dict]:
        """清洗OpenAlex数据"""
        cleaned = []
        
        for item in data:
            cleaned_item = {}
            
            cleaned_item["openalex_id"] = self._clean_text(item.get("openalex_id", ""))
            cleaned_item["doi"] = self._clean_text(item.get("doi", ""))
            cleaned_item["title"] = self._clean_text(item.get("title", ""))
            
            # OpenAlex返回倒排索引格式的摘要，需要转换
            abstract = item.get("abstract")
            if isinstance(abstract, dict):
                # 倒排索引转文本
                words = {}
                for word, positions in abstract.items():
                    for pos in positions:
                        words[pos] = word
                cleaned_item["abstract"] = " ".join([words[i] for i in sorted(words.keys())])
            else:
                cleaned_item["abstract"] = self._clean_text(abstract or "")
            
            cleaned_item["authors"] = self._clean_text(item.get("authors", ""))
            cleaned_item["institutions"] = item.get("institutions", [])
            cleaned_item["publication_date"] = self._standardize_date(item.get("publication_date"))
            cleaned_item["year"] = item.get("year")
            cleaned_item["journal"] = self._clean_text(item.get("journal", ""))
            cleaned_item["citation_count"] = item.get("citation_count", 0)
            cleaned_item["concepts"] = item.get("concepts", [])
            cleaned_item["type"] = item.get("type", "")
            cleaned_item["is_open_access"] = item.get("is_open_access", False)
            cleaned_item["oa_status"] = item.get("oa_status", "")
            cleaned_item["pdf_url"] = item.get("pdf_url") or item.get("oa_url")
            cleaned_item["url"] = item.get("url", "")
            cleaned_item["source"] = "openalex"
            cleaned_item["fetched_at"] = item.get("fetched_at", datetime.now().isoformat())
            cleaned_item["cleaned_at"] = datetime.now().isoformat()
            
            cleaned_item["quality_score"] = self._calculate_openalex_quality(cleaned_item)
            
            cleaned.append(cleaned_item)
        
        return cleaned
    
    def _clean_europe_pmc(self, data: List[Dict]) -> List[Dict]:
        """清洗Europe PMC数据"""
        cleaned = []
        
        for item in data:
            cleaned_item = {}
            
            cleaned_item["pmid"] = self._clean_text(item.get("pmid", ""))
            cleaned_item["pmcid"] = self._clean_text(item.get("pmcid", ""))
            cleaned_item["doi"] = self._clean_text(item.get("doi", ""))
            cleaned_item["title"] = self._clean_text(item.get("title", ""))
            cleaned_item["abstract"] = self._clean_text(item.get("abstract", ""))
            cleaned_item["authors"] = self._clean_text(item.get("authors", ""))
            cleaned_item["journal"] = self._clean_text(item.get("journal", ""))
            cleaned_item["publication_date"] = self._standardize_date(item.get("publication_date"))
            cleaned_item["year"] = item.get("year")
            cleaned_item["citation_count"] = item.get("citation_count", 0)
            cleaned_item["is_open_access"] = item.get("is_open_access", False)
            cleaned_item["has_full_text"] = item.get("has_full_text", False)
            cleaned_item["publication_types"] = item.get("publication_types", [])
            cleaned_item["mesh_terms"] = item.get("mesh_terms", [])
            cleaned_item["url"] = item.get("url", "")
            cleaned_item["full_text_url"] = item.get("full_text_url")
            cleaned_item["source"] = "europe_pmc"
            cleaned_item["fetched_at"] = item.get("fetched_at", datetime.now().isoformat())
            cleaned_item["cleaned_at"] = datetime.now().isoformat()
            
            cleaned_item["quality_score"] = self._calculate_europepmc_quality(cleaned_item)
            
            cleaned.append(cleaned_item)
        
        return cleaned
    
    def _calculate_ss_quality(self, item: Dict) -> float:
        """计算Semantic Scholar数据质量分数"""
        score = 50.0  # 基础分
        
        if item.get("title"):
            score += 10
        if item.get("abstract"):
            score += 10
        if item.get("authors"):
            score += 5
        if item.get("doi"):
            score += 5
        if item.get("year"):
            score += 5
        
        # 引用数加分
        citations = item.get("citation_count", 0)
        if citations > 0:
            score += min(15, citations / 10)
        
        return min(100, score)
    
    def _calculate_preprint_quality(self, item: Dict) -> float:
        """计算预印本数据质量分数"""
        score = 40.0  # 预印本基础分较低（未经同行评审）
        
        if item.get("title"):
            score += 15
        if item.get("abstract"):
            score += 15
        if item.get("authors"):
            score += 10
        if item.get("doi"):
            score += 10
        if item.get("pdf_url"):
            score += 10
        
        return min(100, score)
    
    def _calculate_openalex_quality(self, item: Dict) -> float:
        """计算OpenAlex数据质量分数"""
        score = 50.0
        
        if item.get("title"):
            score += 10
        if item.get("abstract"):
            score += 10
        if item.get("authors"):
            score += 5
        if item.get("doi"):
            score += 5
        if item.get("is_open_access"):
            score += 5
        
        citations = item.get("citation_count", 0)
        if citations > 0:
            score += min(15, citations / 10)
        
        return min(100, score)
    
    def _calculate_europepmc_quality(self, item: Dict) -> float:
        """计算Europe PMC数据质量分数"""
        score = 50.0
        
        if item.get("title"):
            score += 10
        if item.get("abstract"):
            score += 10
        if item.get("authors"):
            score += 5
        if item.get("pmid"):
            score += 5
        if item.get("is_open_access"):
            score += 5
        if item.get("has_full_text"):
            score += 10
        
        citations = item.get("citation_count", 0)
        if citations > 0:
            score += min(5, citations / 20)
        
        return min(100, score)
    
    def _generic_clean(self, data: List[Dict]) -> List[Dict]:
        """通用数据清洗"""
        cleaned = []
        
        for item in data:
            cleaned_item = {}
            for key, value in item.items():
                if isinstance(value, str):
                    cleaned_item[key] = self._clean_text(value)
                else:
                    cleaned_item[key] = value
            cleaned_item["cleaned_at"] = datetime.now().isoformat()
            cleaned.append(cleaned_item)
        
        return cleaned
    
    def _clean_text(self, text: Any) -> str:
        """清洗文本"""
        # 处理 None 和空值
        if text is None:
            return ""
        
        # 处理列表/数组类型
        if isinstance(text, (list, tuple)):
            if len(text) == 0:
                return ""
            # 将列表转为逗号分隔的字符串
            return ", ".join(str(item) for item in text if item)
        
        # 处理 pandas NA 值
        try:
            if pd.isna(text):
                return ""
        except (ValueError, TypeError):
            # 如果 pd.isna 无法处理，继续处理
            pass
        
        text = str(text).strip()
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 去除特殊字符
        text = re.sub(r'[\r\n\t]', ' ', text)
        
        return text
    
    def _standardize_status(self, status: str) -> str:
        """标准化试验状态"""
        if not status:
            return "UNKNOWN"
        
        status_upper = status.upper().strip()
        
        status_mapping = {
            "RECRUITING": "RECRUITING",
            "ACTIVE, NOT RECRUITING": "ACTIVE",
            "NOT YET RECRUITING": "NOT_RECRUITING",
            "COMPLETED": "COMPLETED",
            "TERMINATED": "TERMINATED",
            "WITHDRAWN": "WITHDRAWN",
            "SUSPENDED": "SUSPENDED",
            "ENROLLING BY INVITATION": "ENROLLING",
            "UNKNOWN STATUS": "UNKNOWN",
        }
        
        for key, value in status_mapping.items():
            if key in status_upper:
                return value
        
        return status_upper
    
    def _standardize_phase(self, phase: str) -> str:
        """标准化临床试验阶段"""
        if not phase or phase == "N/A":
            return "UNKNOWN"
        
        phase_upper = phase.upper().strip()
        
        # 标准化阶段表示
        phase_mapping = {
            "PHASE1": "PHASE_1",
            "PHASE 1": "PHASE_1",
            "PHASE2": "PHASE_2",
            "PHASE 2": "PHASE_2",
            "PHASE3": "PHASE_3",
            "PHASE 3": "PHASE_3",
            "PHASE4": "PHASE_4",
            "PHASE 4": "PHASE_4",
            "EARLY_PHASE1": "EARLY_PHASE_1",
            "EARLY PHASE 1": "EARLY_PHASE_1",
        }
        
        for old, new in phase_mapping.items():
            phase_upper = phase_upper.replace(old, new)
        
        return phase_upper
    
    def _standardize_date(self, date_str: Any) -> Optional[str]:
        """标准化日期格式为ISO 8601"""
        if not date_str or pd.isna(date_str):
            return None
        
        date_str = str(date_str).strip()
        
        # 尝试多种日期格式
        date_formats = [
            "%Y-%m-%d",
            "%Y-%m",
            "%Y",
            "%B %Y",  # January 2020
            "%B %d, %Y",  # January 15, 2020
            "%b %Y",  # Jan 2020
            "%d %b %Y",  # 15 Jan 2020
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # 尝试pandas解析
        try:
            dt = pd.to_datetime(date_str, errors='coerce')
            if pd.notna(dt):
                return dt.strftime("%Y-%m-%d")
        except:
            pass
        
        return None
    
    def _extract_number(self, value: Any) -> int:
        """提取数值"""
        if isinstance(value, (int, float)):
            return int(value)
        
        if isinstance(value, str):
            match = re.search(r'(\d+)', value)
            if match:
                return int(match.group(1))
        
        return 0
    
    def _extract_age(self, age_str: str) -> Optional[float]:
        """从年龄字符串提取年龄值（转换为年）"""
        if not age_str or age_str == "N/A":
            return None
        
        age_str = str(age_str).lower()
        
        # 提取数字
        match = re.search(r'(\d+(?:\.\d+)?)', age_str)
        if not match:
            return None
        
        age = float(match.group(1))
        
        # 单位转换
        if "month" in age_str:
            age = age / 12
        elif "week" in age_str:
            age = age / 52
        elif "day" in age_str:
            age = age / 365
        
        return round(age, 2)
    
    def _calculate_quality_score(self, item: Dict) -> float:
        """计算数据质量分数（0-100）"""
        score = 0
        max_score = 100
        
        # 关键字段完整性（60分）
        key_fields = [
            ("nct_id", 10),
            ("title", 10),
            ("status", 10),
            ("phase", 10),
            ("sponsor", 10),
            ("summary", 10),
        ]
        
        for field, weight in key_fields:
            if item.get(field) and item[field] not in ["", "N/A", "UNKNOWN"]:
                score += weight
        
        # 数值字段有效性（20分）
        if item.get("enrollment", 0) > 0:
            score += 10
        if item.get("min_age_years") is not None:
            score += 5
        if item.get("max_age_years") is not None:
            score += 5
        
        # 日期有效性（20分）
        if item.get("start_date"):
            score += 10
        if item.get("completion_date"):
            score += 10
        
        return min(score, max_score)
    
    def _calculate_pubmed_quality(self, item: Dict) -> float:
        """计算PubMed数据质量分数"""
        score = 0
        
        key_fields = [
            ("pmid", 15),
            ("title", 20),
            ("authors", 15),
            ("journal", 15),
            ("publication_date", 15),
            ("doi", 10),
        ]
        
        for field, weight in key_fields:
            if item.get(field) and item[field] not in ["", "N/A"]:
                score += weight
        
        return min(score, 100)


class DataIntegrationService:
    """数据集成服务"""
    
    def __init__(self):
        pass
    
    def integrate_results(self, results: Dict[str, List[Dict]]) -> Dict:
        """
        集成多数据源结果
        
        Args:
            results: 各数据源的结果字典
            
        Returns:
            集成后的结果
        """
        integrated = {
            "summary": {
                "total_records": 0,
                "by_source": {},
                "integrated_at": datetime.now().isoformat()
            },
            "clinical_trials": [],
            "literature": [],
            "all_data": []
        }
        
        for source, data in results.items():
            count = len(data)
            integrated["summary"]["total_records"] += count
            integrated["summary"]["by_source"][source] = count
            
            if source == "clinicaltrials":
                integrated["clinical_trials"] = data
            elif source == "pubmed":
                integrated["literature"] = data
            
            for item in data:
                item["_source"] = source
                integrated["all_data"].append(item)
        
        return integrated
    
    def merge_trial_literature(
        self, 
        trials: List[Dict], 
        literature: List[Dict]
    ) -> List[Dict]:
        """
        合并试验和文献数据
        
        基于关键词匹配关联试验和相关文献
        """
        merged = []
        
        for trial in trials:
            trial_data = {**trial}
            trial_data["related_publications"] = []
            
            # 简单的关键词匹配
            trial_title = trial.get("title", "").lower()
            trial_nct = trial.get("nct_id", "")
            
            for lit in literature:
                lit_title = lit.get("title", "").lower()
                
                # 检查是否引用了NCT ID
                if trial_nct and trial_nct.lower() in lit_title:
                    trial_data["related_publications"].append(lit.get("pmid"))
                    continue
                
                # 简单关键词匹配
                keywords = trial_title.split()[:5]
                matches = sum(1 for kw in keywords if kw in lit_title and len(kw) > 3)
                if matches >= 2:
                    trial_data["related_publications"].append(lit.get("pmid"))
            
            trial_data["related_count"] = len(trial_data["related_publications"])
            merged.append(trial_data)
        
        return merged


class DataQualityAnalyzer:
    """数据质量分析器"""
    
    def analyze(self, data: List[Dict]) -> Dict:
        """分析数据质量"""
        if not data:
            return {"error": "No data to analyze"}
        
        df = pd.DataFrame(data)
        
        report = {
            "total_records": len(df),
            "total_columns": len(df.columns),
            "completeness": {},
            "quality_scores": {},
            "summary": {}
        }
        
        # 计算各列完整性
        for col in df.columns:
            non_null = df[col].notna().sum()
            non_empty = df[col].apply(lambda x: x not in ["", "N/A", "UNKNOWN", None]).sum()
            report["completeness"][col] = {
                "non_null_rate": round(non_null / len(df) * 100, 2),
                "valid_rate": round(non_empty / len(df) * 100, 2)
            }
        
        # 质量分数统计
        if "quality_score" in df.columns:
            report["quality_scores"] = {
                "mean": round(df["quality_score"].mean(), 2),
                "median": round(df["quality_score"].median(), 2),
                "min": round(df["quality_score"].min(), 2),
                "max": round(df["quality_score"].max(), 2)
            }
        
        # 汇总
        avg_completeness = sum(
            v["valid_rate"] for v in report["completeness"].values()
        ) / len(report["completeness"])
        
        report["summary"] = {
            "average_completeness": round(avg_completeness, 2),
            "high_quality_records": len(df[df.get("quality_score", 0) >= 80]) if "quality_score" in df.columns else 0
        }
        
        return report