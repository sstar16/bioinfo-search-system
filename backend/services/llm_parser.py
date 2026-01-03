#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM查询解析服务
使用本地Ollama或其他LLM将自然语言解析为结构化查询
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Any
import httpx

class LLMQueryParser:
    """LLM查询解析器"""
    
    # 生物医学领域关键词映射
    DOMAIN_KEYWORDS = {
        "vaccine": ["疫苗", "vaccine", "immunization", "vaccination", "接种"],
        "clinical_trial": ["临床试验", "clinical trial", "trial", "study", "研究"],
        "disease": ["疾病", "disease", "condition", "disorder", "syndrome", "病"],
        "drug": ["药物", "drug", "medication", "medicine", "pharmaceutical", "药"],
        "protein": ["蛋白", "protein", "enzyme", "酶"],
        "gene": ["基因", "gene", "genetic", "genomic", "DNA", "RNA"],
        "bacteria": ["细菌", "bacteria", "bacterial", "菌"],
        "virus": ["病毒", "virus", "viral"],
    }
    
    # 常见疾病/病原体名称映射
    CONDITION_MAPPING = {
        "脑膜炎": "meningitis",
        "脑膜炎球菌": "meningococcal",
        "B群脑膜炎": "meningococcal B",
        "新冠": "COVID-19",
        "流感": "influenza",
        "肺炎": "pneumonia",
        "乙肝": "hepatitis B",
        "狂犬病": "rabies",
        "麻疹": "measles",
        "结核": "tuberculosis",
        "疟疾": "malaria",
        "艾滋病": "HIV/AIDS",
        "癌症": "cancer",
        "肿瘤": "tumor",
        "糖尿病": "diabetes",
        "高血压": "hypertension",
        "心脏病": "heart disease",
        "阿尔茨海默": "Alzheimer",
        "帕金森": "Parkinson",
    }
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.model = "llama3.2"  # 默认模型
        self.timeout = 60.0
        
    async def check_connection(self) -> Dict[str, Any]:
        """检查Ollama连接状态"""
        try:
            # 禁用代理访问本地服务
            async with httpx.AsyncClient(timeout=5.0, proxy=None) as client:
                response = await client.get(f"{self.ollama_host}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {
                        "connected": True,
                        "available_models": models,
                        "current_model": self.model
                    }
        except Exception as e:
            print(f"[DEBUG] Ollama连接异常: {type(e).__name__}: {e}")
        
        return {
            "connected": False,
            "available_models": [],
            "error": "无法连接到Ollama服务"
        }
    
    async def parse_query(self, query: str) -> Dict[str, Any]:
        """
        解析自然语言查询
        
        Args:
            query: 用户输入的自然语言查询
            
        Returns:
            解析后的结构化查询字典
        """
        # 先尝试使用LLM解析
        llm_result = await self._llm_parse(query)
        
        if llm_result and llm_result.get("success"):
            return llm_result["parsed"]
        
        # LLM解析失败，使用规则解析
        return self._rule_based_parse(query)
    
    async def _llm_parse(self, query: str) -> Optional[Dict]:
        """使用LLM解析查询"""
        prompt = self._build_prompt(query)
        
        try:
            # 禁用代理访问本地Ollama服务
            async with httpx.AsyncClient(timeout=self.timeout, proxy=None) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_predict": 500
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result_text = data.get("response", "")
                    
                    # 解析LLM返回的JSON
                    parsed = self._extract_json(result_text)
                    if parsed:
                        parsed["original"] = query
                        parsed["parse_method"] = "llm"
                        return {"success": True, "parsed": parsed}
                        
        except Exception as e:
            print(f"LLM解析错误: {e}")
        
        return None
    
    def _build_prompt(self, query: str) -> str:
        """构建LLM提示词"""
        return f"""You are a biomedical query parser. Parse the following natural language query into structured search parameters for biomedical databases (ClinicalTrials.gov, PubMed).

User Query: "{query}"

Extract and return a JSON object with these fields:
- "condition": The disease or medical condition (in English, e.g., "meningococcal B", "COVID-19")
- "intervention": The treatment or intervention type (e.g., "vaccine", "drug")
- "keywords": Array of relevant search keywords in English
- "phase": Clinical trial phase if mentioned (e.g., "Phase 1", "Phase 2", "Phase 3")
- "status": Trial status if mentioned (e.g., "recruiting", "completed")
- "date_range": Time range if mentioned (e.g., "last 5 years")
- "target_population": Target population if mentioned (e.g., "children", "adults", "elderly")
- "data_sources": Recommended data sources ["clinicaltrials", "pubmed"]

Important:
1. Translate Chinese medical terms to English
2. Keep keywords specific and relevant to biomedical research
3. Return ONLY valid JSON, no explanation

JSON Output:"""
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """从LLM响应中提取JSON"""
        # 尝试直接解析
        try:
            return json.loads(text.strip())
        except:
            pass
        
        # 尝试提取JSON块
        json_patterns = [
            r'\{[^{}]*\}',
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
        
        return None
    
    def _rule_based_parse(self, query: str) -> Dict[str, Any]:
        """基于规则的查询解析（后备方案）"""
        result = {
            "original": query,
            "parse_method": "rule_based",
            "keywords": [],
            "condition": "",
            "intervention": "",
            "data_sources": ["clinicaltrials", "pubmed"]
        }
        
        query_lower = query.lower()
        
        # 检测疾病/病原体
        for cn_name, en_name in self.CONDITION_MAPPING.items():
            if cn_name in query or en_name.lower() in query_lower:
                result["condition"] = en_name
                result["keywords"].append(en_name)
                break
        
        # 检测领域关键词
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in query_lower:
                    if domain == "vaccine":
                        result["intervention"] = "vaccine"
                    result["keywords"].append(kw)
                    break
        
        # 检测临床试验阶段
        phase_match = re.search(r'(phase\s*[1-4]|[一二三四]期|第[一二三四]期)', query_lower)
        if phase_match:
            phase_text = phase_match.group(1)
            phase_map = {"一": "1", "二": "2", "三": "3", "四": "4", "第一": "1", "第二": "2", "第三": "3", "第四": "4"}
            for cn, num in phase_map.items():
                if cn in phase_text:
                    result["phase"] = f"Phase {num}"
                    break
            if "phase" not in result:
                num_match = re.search(r'[1-4]', phase_text)
                if num_match:
                    result["phase"] = f"Phase {num_match.group()}"
        
        # 检测时间范围
        year_match = re.search(r'(\d+)\s*(年|years?)', query_lower)
        if year_match:
            result["date_range"] = f"last {year_match.group(1)} years"
        
        # 检测状态
        status_keywords = {
            "进行中": "recruiting",
            "招募": "recruiting",
            "完成": "completed",
            "终止": "terminated",
            "recruiting": "recruiting",
            "completed": "completed",
        }
        for kw, status in status_keywords.items():
            if kw in query_lower:
                result["status"] = status
                break
        
        # 检测目标人群
        population_keywords = {
            "儿童": "children",
            "成人": "adults",
            "老年": "elderly",
            "婴儿": "infants",
            "青少年": "adolescents",
            "children": "children",
            "adults": "adults",
        }
        for kw, pop in population_keywords.items():
            if kw in query_lower:
                result["target_population"] = pop
                break
        
        # 如果没有提取到关键词，使用分词
        if not result["keywords"]:
            # 简单分词
            words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', query)
            result["keywords"] = [w for w in words if len(w) > 1][:10]
        
        # 去重
        result["keywords"] = list(set(result["keywords"]))
        
        return result


class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self):
        # 同义词扩展
        self.synonyms = {
            "vaccine": ["vaccination", "immunization", "inoculation"],
            "meningococcal": ["meningitis", "Neisseria meningitidis"],
            "COVID-19": ["SARS-CoV-2", "coronavirus", "COVID"],
        }
    
    def expand_query(self, parsed_query: Dict) -> Dict:
        """扩展查询（添加同义词）"""
        keywords = parsed_query.get("keywords", [])
        expanded = set(keywords)
        
        for kw in keywords:
            kw_lower = kw.lower()
            for term, syns in self.synonyms.items():
                if term.lower() == kw_lower:
                    expanded.update(syns)
        
        parsed_query["keywords"] = list(expanded)
        parsed_query["expanded"] = True
        
        return parsed_query
    
    def build_search_string(self, parsed_query: Dict, source: str) -> str:
        """构建特定数据源的搜索字符串"""
        condition = parsed_query.get("condition", "")
        intervention = parsed_query.get("intervention", "")
        keywords = parsed_query.get("keywords", [])
        
        if source == "clinicaltrials":
            # ClinicalTrials.gov 查询格式
            parts = []
            if condition:
                parts.append(condition)
            if intervention:
                parts.append(intervention)
            return " ".join(parts) if parts else " ".join(keywords[:3])
        
        elif source == "pubmed":
            # PubMed 查询格式（支持布尔逻辑）
            terms = []
            if condition:
                terms.append(f'"{condition}"[Title/Abstract]')
            if intervention:
                terms.append(f'"{intervention}"[Title/Abstract]')
            if not terms:
                terms = [f'"{kw}"' for kw in keywords[:3]]
            return " AND ".join(terms)
        
        return " ".join(keywords)
