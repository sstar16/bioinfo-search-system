#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生物信息数据获取服务
从ClinicalTrials.gov, PubMed等公开数据库获取数据
"""

import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx

class BioDataFetcher:
    """生物信息数据获取器"""
    
    def __init__(self):
        self.timeout = 30.0
        self.retry_count = 3
        self.retry_delay = 2.0
        
        # API端点
        self.ct_base_url = "https://clinicaltrials.gov/api/v2"
        self.pubmed_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
    async def fetch_clinical_trials(
        self, 
        search_term: str, 
        max_results: int = 100
    ) -> List[Dict]:
        """
        从ClinicalTrials.gov获取临床试验数据
        
        Args:
            search_term: 搜索词
            max_results: 最大结果数
            
        Returns:
            临床试验数据列表
        """
        all_studies = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 尝试多种搜索策略
            search_strategies = [
                {"query.cond": search_term, "query.intr": "vaccine"},
                {"query.term": f"{search_term} vaccine"},
                {"query.cond": search_term},
            ]
            
            for strategy in search_strategies:
                params = {
                    **strategy,
                    "pageSize": min(100, max_results),
                    "format": "json",
                    "countTotal": "true"
                }
                
                try:
                    response = await client.get(
                        f"{self.ct_base_url}/studies",
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        studies = data.get("studies", [])
                        
                        if studies:
                            all_studies.extend(studies)
                            
                            # 分页获取更多
                            page_token = data.get("nextPageToken")
                            while page_token and len(all_studies) < max_results:
                                params["pageToken"] = page_token
                                response = await client.get(
                                    f"{self.ct_base_url}/studies",
                                    params=params
                                )
                                if response.status_code == 200:
                                    data = response.json()
                                    new_studies = data.get("studies", [])
                                    all_studies.extend(new_studies)
                                    page_token = data.get("nextPageToken")
                                    if not new_studies:
                                        break
                                else:
                                    break
                                await asyncio.sleep(0.3)
                            
                            break  # 成功获取数据就停止
                            
                except Exception as e:
                    print(f"ClinicalTrials.gov 请求错误: {e}")
                    continue
        
        # 去重并提取详细信息
        seen_ids = set()
        unique_studies = []
        for study in all_studies:
            nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
            if nct_id and nct_id not in seen_ids:
                seen_ids.add(nct_id)
                unique_studies.append(self._extract_trial_details(study))
        
        return unique_studies[:max_results]
    
    def _extract_trial_details(self, study: Dict) -> Dict:
        """提取临床试验详细信息"""
        protocol = study.get("protocolSection", {})
        
        identification = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        arms = protocol.get("armsInterventionsModule", {})
        sponsor = protocol.get("sponsorCollaboratorsModule", {})
        contacts = protocol.get("contactsLocationsModule", {})
        outcomes = protocol.get("outcomesModule", {})
        eligibility = protocol.get("eligibilityModule", {})
        description = protocol.get("descriptionModule", {})
        
        # 提取干预措施
        interventions = arms.get("interventions", [])
        vaccine_names = [
            i.get("name", "") 
            for i in interventions 
            if "vaccine" in i.get("type", "").lower() or "vaccine" in i.get("name", "").lower()
        ]
        
        # 提取国家
        locations = contacts.get("locations", [])
        countries = list(set([loc.get("country", "") for loc in locations if loc.get("country")]))
        
        return {
            "nct_id": identification.get("nctId", ""),
            "title": identification.get("briefTitle", ""),
            "official_title": identification.get("officialTitle", ""),
            "status": status.get("overallStatus", ""),
            "phase": ", ".join(design.get("phases", [])),
            "start_date": status.get("startDateStruct", {}).get("date", ""),
            "completion_date": status.get("completionDateStruct", {}).get("date", ""),
            "enrollment": design.get("enrollmentInfo", {}).get("count", 0),
            "study_type": design.get("studyType", ""),
            "allocation": design.get("designInfo", {}).get("allocation", ""),
            "vaccine_names": " | ".join(vaccine_names),
            "all_interventions": " | ".join([i.get("name", "") for i in interventions]),
            "sponsor": sponsor.get("leadSponsor", {}).get("name", ""),
            "collaborators": ", ".join([c.get("name", "") for c in sponsor.get("collaborators", [])]),
            "countries": ", ".join(countries),
            "num_locations": len(locations),
            "primary_outcome": (
                outcomes.get("primaryOutcomes", [{}])[0].get("measure", "")[:200]
                if outcomes.get("primaryOutcomes") else ""
            ),
            "min_age": eligibility.get("minimumAge", ""),
            "max_age": eligibility.get("maximumAge", ""),
            "sex": eligibility.get("sex", ""),
            "healthy_volunteers": eligibility.get("healthyVolunteers", ""),
            "summary": description.get("briefSummary", "")[:500],
            "url": f"https://clinicaltrials.gov/study/{identification.get('nctId', '')}",
            "source": "clinicaltrials",
            "fetched_at": datetime.now().isoformat()
        }
    
    async def fetch_pubmed(
        self, 
        search_term: str, 
        max_results: int = 100
    ) -> List[Dict]:
        """
        从PubMed获取文献数据
        
        Args:
            search_term: 搜索词
            max_results: 最大结果数
            
        Returns:
            文献数据列表
        """
        articles = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 第一步：搜索获取PMID列表
            search_params = {
                "db": "pubmed",
                "term": f"{search_term} vaccine clinical trial",
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance"
            }
            
            try:
                response = await client.get(
                    f"{self.pubmed_base_url}/esearch.fcgi",
                    params=search_params
                )
                
                if response.status_code != 200:
                    return articles
                
                search_data = response.json()
                pmids = search_data.get("esearchresult", {}).get("idlist", [])
                
                if not pmids:
                    return articles
                
                # 第二步：获取文献详情（分批处理）
                batch_size = 50
                for i in range(0, len(pmids), batch_size):
                    batch_pmids = pmids[i:i+batch_size]
                    
                    fetch_params = {
                        "db": "pubmed",
                        "id": ",".join(batch_pmids),
                        "retmode": "json"
                    }
                    
                    response = await client.get(
                        f"{self.pubmed_base_url}/esummary.fcgi",
                        params=fetch_params
                    )
                    
                    if response.status_code != 200:
                        continue
                    
                    fetch_data = response.json()
                    results = fetch_data.get("result", {})
                    
                    for pmid in batch_pmids:
                        if pmid in results and isinstance(results[pmid], dict):
                            article = results[pmid]
                            articles.append(self._extract_pubmed_details(pmid, article))
                    
                    await asyncio.sleep(0.3)
                    
            except Exception as e:
                print(f"PubMed 请求错误: {e}")
        
        return articles
    
    def _extract_pubmed_details(self, pmid: str, article: Dict) -> Dict:
        """提取PubMed文献详细信息"""
        authors = article.get("authors", [])
        author_list = [a.get("name", "") for a in authors[:5]]
        
        return {
            "pmid": pmid,
            "title": article.get("title", ""),
            "authors": ", ".join(author_list) + (" et al." if len(authors) > 5 else ""),
            "journal": article.get("fulljournalname", article.get("source", "")),
            "publication_date": article.get("pubdate", ""),
            "volume": article.get("volume", ""),
            "issue": article.get("issue", ""),
            "pages": article.get("pages", ""),
            "doi": article.get("elocationid", "").replace("doi: ", ""),
            "pub_type": ", ".join(article.get("pubtype", [])),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "source": "pubmed",
            "fetched_at": datetime.now().isoformat()
        }
    
    async def fetch_all_sources(
        self, 
        search_term: str, 
        sources: List[str],
        max_results: int = 100
    ) -> Dict[str, List[Dict]]:
        """
        从多个数据源并行获取数据
        
        Args:
            search_term: 搜索词
            sources: 数据源列表
            max_results: 每个源的最大结果数
            
        Returns:
            各数据源的结果字典
        """
        results = {}
        tasks = []
        
        # 按数据源数量分配max_results
        num_sources = len([s for s in sources if s in ["clinicaltrials", "pubmed"]])
        per_source_limit = max_results // num_sources if num_sources > 0 else max_results
        
        if "clinicaltrials" in sources:
            tasks.append(("clinicaltrials", self.fetch_clinical_trials(search_term, per_source_limit)))
        
        if "pubmed" in sources:
            tasks.append(("pubmed", self.fetch_pubmed(search_term, per_source_limit)))
        
        # 并行执行
        for source, task in tasks:
            try:
                data = await task
                results[source] = data
            except Exception as e:
                results[source] = []
                print(f"获取{source}数据失败: {e}")
        
        return results


class DataSourceRegistry:
    """数据源注册表"""
    
    SOURCES = {
        "clinicaltrials": {
            "name": "ClinicalTrials.gov",
            "description": "美国国立卫生研究院临床试验数据库",
            "url": "https://clinicaltrials.gov",
            "data_type": "clinical_trials"
        },
        "pubmed": {
            "name": "PubMed",
            "description": "美国国家医学图书馆生物医学文献数据库",
            "url": "https://pubmed.ncbi.nlm.nih.gov",
            "data_type": "literature"
        }
    }
    
    @classmethod
    def get_available_sources(cls) -> List[Dict]:
        """获取可用数据源列表"""
        return [
            {"id": k, **v}
            for k, v in cls.SOURCES.items()
        ]
    
    @classmethod
    def get_source_info(cls, source_id: str) -> Optional[Dict]:
        """获取数据源信息"""
        if source_id in cls.SOURCES:
            return {"id": source_id, **cls.SOURCES[source_id]}
        return None
