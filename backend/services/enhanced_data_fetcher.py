#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版生物信息数据获取服务
支持更多数据源：Semantic Scholar, bioRxiv, medRxiv, Unpaywall, OpenAlex, WHO ICTRP等
"""

import asyncio
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx


class EnhancedBioDataFetcher:
    """增强版生物信息数据获取器"""
    
    def __init__(self):
        self.timeout = 30.0
        self.retry_count = 3
        self.retry_delay = 2.0
        
        # API端点
        self.apis = {
            "clinicaltrials": "https://clinicaltrials.gov/api/v2",
            "pubmed": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            "semantic_scholar": "https://api.semanticscholar.org/graph/v1",
            "biorxiv": "https://api.biorxiv.org/details/biorxiv",
            "medrxiv": "https://api.biorxiv.org/details/medrxiv",
            "unpaywall": "https://api.unpaywall.org/v2",
            "openalex": "https://api.openalex.org",
            "europe_pmc": "https://www.ebi.ac.uk/europepmc/webservices/rest",
        }
        
        # Unpaywall 需要邮箱（免费使用）
        self.unpaywall_email = os.environ.get("UNPAYWALL_EMAIL", "bioinfo@example.com")
    
    # ==================== Semantic Scholar ====================
    async def fetch_semantic_scholar(
        self, 
        search_term: str, 
        max_results: int = 100,
        year_from: Optional[int] = None
    ) -> List[Dict]:
        """
        从Semantic Scholar获取学术论文
        特点：包含引用数、影响力评分、相关论文推荐
        
        API文档: https://api.semanticscholar.org/
        """
        papers = []
        
        async with httpx.AsyncClient(timeout=self.timeout, proxy=None) as client:
            try:
                # 构建查询参数
                params = {
                    "query": search_term,
                    "limit": min(max_results, 100),  # API限制每次100
                    "fields": "paperId,title,abstract,authors,year,citationCount,influentialCitationCount,venue,publicationDate,openAccessPdf,externalIds,fieldsOfStudy,s2FieldsOfStudy,publicationTypes,journal"
                }
                
                if year_from:
                    params["year"] = f"{year_from}-"
                
                response = await client.get(
                    f"{self.apis['semantic_scholar']}/paper/search",
                    params=params,
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for paper in data.get("data", []):
                        # 提取作者信息
                        authors = ", ".join([
                            a.get("name", "") 
                            for a in paper.get("authors", [])[:5]
                        ])
                        if len(paper.get("authors", [])) > 5:
                            authors += " et al."
                        
                        # 提取外部ID
                        external_ids = paper.get("externalIds", {})
                        
                        papers.append({
                            "paper_id": paper.get("paperId"),
                            "title": paper.get("title"),
                            "abstract": paper.get("abstract"),
                            "authors": authors,
                            "year": paper.get("year"),
                            "publication_date": paper.get("publicationDate"),
                            "venue": paper.get("venue"),
                            "journal": paper.get("journal", {}).get("name") if paper.get("journal") else None,
                            "citation_count": paper.get("citationCount", 0),
                            "influential_citation_count": paper.get("influentialCitationCount", 0),
                            "fields_of_study": paper.get("fieldsOfStudy", []),
                            "publication_types": paper.get("publicationTypes", []),
                            "doi": external_ids.get("DOI"),
                            "pmid": external_ids.get("PubMed"),
                            "arxiv_id": external_ids.get("ArXiv"),
                            "open_access_pdf": paper.get("openAccessPdf", {}).get("url") if paper.get("openAccessPdf") else None,
                            "url": f"https://www.semanticscholar.org/paper/{paper.get('paperId')}",
                            "source": "semantic_scholar"
                        })
                    
                    # 如果需要更多结果，继续翻页
                    offset = 100
                    while len(papers) < max_results and data.get("next"):
                        params["offset"] = offset
                        response = await client.get(
                            f"{self.apis['semantic_scholar']}/paper/search",
                            params=params
                        )
                        if response.status_code == 200:
                            data = response.json()
                            for paper in data.get("data", []):
                                if len(papers) >= max_results:
                                    break
                                authors = ", ".join([a.get("name", "") for a in paper.get("authors", [])[:5]])
                                external_ids = paper.get("externalIds", {})
                                papers.append({
                                    "paper_id": paper.get("paperId"),
                                    "title": paper.get("title"),
                                    "abstract": paper.get("abstract"),
                                    "authors": authors,
                                    "year": paper.get("year"),
                                    "citation_count": paper.get("citationCount", 0),
                                    "doi": external_ids.get("DOI"),
                                    "open_access_pdf": paper.get("openAccessPdf", {}).get("url") if paper.get("openAccessPdf") else None,
                                    "url": f"https://www.semanticscholar.org/paper/{paper.get('paperId')}",
                                    "source": "semantic_scholar"
                                })
                            offset += 100
                        else:
                            break
                        
                        # 避免请求过快
                        await asyncio.sleep(0.5)
                        
            except Exception as e:
                print(f"Semantic Scholar API错误: {e}")
        
        return papers[:max_results]
    
    # ==================== bioRxiv / medRxiv ====================
    async def fetch_biorxiv(
        self, 
        search_term: str, 
        max_results: int = 100,
        server: str = "biorxiv"  # "biorxiv" 或 "medrxiv"
    ) -> List[Dict]:
        """
        从bioRxiv/medRxiv获取预印本论文
        特点：最新研究成果，尚未经过同行评审
        
        API文档: https://api.biorxiv.org/
        """
        papers = []
        
        # bioRxiv API 按日期范围查询，我们获取最近2年的数据
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient(timeout=self.timeout, proxy=None) as client:
            try:
                cursor = 0
                base_url = self.apis[server]
                
                while len(papers) < max_results:
                    # API格式: /details/{server}/{start}/{end}/{cursor}
                    url = f"{base_url}/{start_date}/{end_date}/{cursor}"
                    
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        collection = data.get("collection", [])
                        
                        if not collection:
                            break
                        
                        # 过滤匹配搜索词的论文
                        search_lower = search_term.lower()
                        for paper in collection:
                            title = paper.get("title", "").lower()
                            abstract = paper.get("abstract", "").lower()
                            
                            # 简单关键词匹配
                            if any(word in title or word in abstract 
                                   for word in search_lower.split()):
                                papers.append({
                                    "doi": paper.get("doi"),
                                    "title": paper.get("title"),
                                    "abstract": paper.get("abstract"),
                                    "authors": paper.get("authors"),
                                    "author_corresponding": paper.get("author_corresponding"),
                                    "author_corresponding_institution": paper.get("author_corresponding_institution"),
                                    "publication_date": paper.get("date"),
                                    "version": paper.get("version"),
                                    "category": paper.get("category"),
                                    "license": paper.get("license"),
                                    "jatsxml": paper.get("jatsxml"),  # XML全文链接
                                    "pdf_url": f"https://www.{server}.org/content/{paper.get('doi')}.full.pdf" if paper.get("doi") else None,
                                    "url": f"https://www.{server}.org/content/{paper.get('doi')}" if paper.get("doi") else None,
                                    "server": server,
                                    "source": server
                                })
                                
                                if len(papers) >= max_results:
                                    break
                        
                        # 移动游标
                        cursor += len(collection)
                        
                        # 如果返回数据少于100条，说明已经没有更多数据
                        if len(collection) < 100:
                            break
                            
                        await asyncio.sleep(0.3)
                    else:
                        break
                        
            except Exception as e:
                print(f"{server} API错误: {e}")
        
        return papers[:max_results]
    
    async def fetch_medrxiv(self, search_term: str, max_results: int = 100) -> List[Dict]:
        """从medRxiv获取医学预印本"""
        return await self.fetch_biorxiv(search_term, max_results, server="medrxiv")
    
    # ==================== OpenAlex ====================
    async def fetch_openalex(
        self, 
        search_term: str, 
        max_results: int = 100,
        year_from: Optional[int] = None
    ) -> List[Dict]:
        """
        从OpenAlex获取学术论文
        特点：完全开放的学术数据库，包含引用网络、作者信息、机构信息
        
        API文档: https://docs.openalex.org/
        """
        papers = []
        
        async with httpx.AsyncClient(timeout=self.timeout, proxy=None) as client:
            try:
                # 构建过滤条件
                filters = []
                if year_from:
                    filters.append(f"from_publication_date:{year_from}-01-01")
                
                params = {
                    "search": search_term,
                    "per_page": min(max_results, 200),
                    "mailto": self.unpaywall_email,  # 礼貌池
                }
                
                if filters:
                    params["filter"] = ",".join(filters)
                
                response = await client.get(
                    f"{self.apis['openalex']}/works",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for work in data.get("results", []):
                        # 提取作者
                        authorships = work.get("authorships", [])
                        authors = ", ".join([
                            a.get("author", {}).get("display_name", "")
                            for a in authorships[:5]
                        ])
                        if len(authorships) > 5:
                            authors += " et al."
                        
                        # 提取机构
                        institutions = []
                        for authorship in authorships[:3]:
                            for inst in authorship.get("institutions", []):
                                if inst.get("display_name"):
                                    institutions.append(inst["display_name"])
                        
                        # 提取主题/概念
                        concepts = [
                            c.get("display_name") 
                            for c in work.get("concepts", [])[:5]
                        ]
                        
                        # 获取开放获取信息
                        oa_info = work.get("open_access", {})
                        
                        papers.append({
                            "openalex_id": work.get("id"),
                            "doi": work.get("doi"),
                            "title": work.get("title"),
                            "abstract": work.get("abstract_inverted_index"),  # 需要转换
                            "authors": authors,
                            "institutions": institutions[:3],
                            "publication_date": work.get("publication_date"),
                            "year": work.get("publication_year"),
                            "journal": work.get("primary_location", {}).get("source", {}).get("display_name") if work.get("primary_location") else None,
                            "citation_count": work.get("cited_by_count", 0),
                            "concepts": concepts,
                            "type": work.get("type"),
                            "is_open_access": oa_info.get("is_oa", False),
                            "oa_status": oa_info.get("oa_status"),
                            "oa_url": oa_info.get("oa_url"),
                            "pdf_url": work.get("primary_location", {}).get("pdf_url") if work.get("primary_location") else None,
                            "url": work.get("id"),
                            "source": "openalex"
                        })
                        
            except Exception as e:
                print(f"OpenAlex API错误: {e}")
        
        return papers[:max_results]
    
    # ==================== Europe PMC ====================
    async def fetch_europe_pmc(
        self, 
        search_term: str, 
        max_results: int = 100
    ) -> List[Dict]:
        """
        从Europe PMC获取生物医学文献
        特点：欧洲生物医学文献数据库，包含全文挖掘功能
        
        API文档: https://europepmc.org/RestfulWebService
        """
        papers = []
        
        async with httpx.AsyncClient(timeout=self.timeout, proxy=None) as client:
            try:
                params = {
                    "query": search_term,
                    "format": "json",
                    "pageSize": min(max_results, 100),
                    "resultType": "core"  # 获取完整信息
                }
                
                response = await client.get(
                    f"{self.apis['europe_pmc']}/search",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for result in data.get("resultList", {}).get("result", []):
                        # 提取作者
                        author_list = result.get("authorList", {}).get("author", [])
                        authors = ", ".join([
                            f"{a.get('firstName', '')} {a.get('lastName', '')}".strip()
                            for a in author_list[:5]
                        ])
                        if len(author_list) > 5:
                            authors += " et al."
                        
                        papers.append({
                            "pmid": result.get("pmid"),
                            "pmcid": result.get("pmcid"),
                            "doi": result.get("doi"),
                            "title": result.get("title"),
                            "abstract": result.get("abstractText"),
                            "authors": authors,
                            "journal": result.get("journalTitle"),
                            "publication_date": result.get("firstPublicationDate"),
                            "year": result.get("pubYear"),
                            "citation_count": result.get("citedByCount", 0),
                            "is_open_access": result.get("isOpenAccess") == "Y",
                            "has_full_text": result.get("hasTextMinedTerms") == "Y",
                            "publication_types": result.get("pubTypeList", {}).get("pubType", []),
                            "mesh_terms": [
                                m.get("descriptorName") 
                                for m in result.get("meshHeadingList", {}).get("meshHeading", [])
                            ],
                            "url": f"https://europepmc.org/article/MED/{result.get('pmid')}" if result.get("pmid") else None,
                            "full_text_url": f"https://europepmc.org/articles/{result.get('pmcid')}" if result.get("pmcid") else None,
                            "source": "europe_pmc"
                        })
                        
            except Exception as e:
                print(f"Europe PMC API错误: {e}")
        
        return papers[:max_results]
    
    # ==================== Unpaywall ====================
    async def fetch_unpaywall(
        self, 
        dois: List[str]
    ) -> Dict[str, Dict]:
        """
        从Unpaywall获取开放获取信息和PDF链接
        输入DOI列表，返回每个DOI的开放获取信息
        
        API文档: https://unpaywall.org/products/api
        """
        results = {}
        
        async with httpx.AsyncClient(timeout=self.timeout, proxy=None) as client:
            for doi in dois:
                try:
                    # 清理DOI
                    clean_doi = doi.replace("https://doi.org/", "").strip()
                    
                    response = await client.get(
                        f"{self.apis['unpaywall']}/{clean_doi}",
                        params={"email": self.unpaywall_email}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # 找到最佳的开放获取版本
                        best_oa = data.get("best_oa_location", {})
                        
                        results[doi] = {
                            "is_oa": data.get("is_oa", False),
                            "oa_status": data.get("oa_status"),
                            "journal_is_oa": data.get("journal_is_oa", False),
                            "pdf_url": best_oa.get("url_for_pdf") if best_oa else None,
                            "landing_page_url": best_oa.get("url_for_landing_page") if best_oa else None,
                            "version": best_oa.get("version") if best_oa else None,
                            "host_type": best_oa.get("host_type") if best_oa else None,
                            "all_oa_locations": [
                                {
                                    "url": loc.get("url"),
                                    "pdf_url": loc.get("url_for_pdf"),
                                    "version": loc.get("version"),
                                    "host_type": loc.get("host_type")
                                }
                                for loc in data.get("oa_locations", [])
                            ]
                        }
                    
                    # 避免请求过快（Unpaywall限制100请求/秒）
                    await asyncio.sleep(0.02)
                    
                except Exception as e:
                    print(f"Unpaywall API错误 ({doi}): {e}")
                    results[doi] = {"is_oa": False, "error": str(e)}
        
        return results
    
    # ==================== 批量获取开放获取PDF ====================
    async def enrich_with_open_access(
        self, 
        papers: List[Dict]
    ) -> List[Dict]:
        """
        为论文列表添加开放获取信息
        自动查询Unpaywall获取免费PDF链接
        """
        # 收集所有DOI
        dois = [p.get("doi") for p in papers if p.get("doi")]
        
        if not dois:
            return papers
        
        # 批量查询Unpaywall
        oa_info = await self.fetch_unpaywall(dois)
        
        # 更新论文信息
        for paper in papers:
            doi = paper.get("doi")
            if doi and doi in oa_info:
                info = oa_info[doi]
                paper["is_open_access"] = info.get("is_oa", False)
                paper["oa_status"] = info.get("oa_status")
                if not paper.get("pdf_url") and info.get("pdf_url"):
                    paper["pdf_url"] = info["pdf_url"]
                paper["oa_locations"] = info.get("all_oa_locations", [])
        
        return papers
    
    # ==================== ClinicalTrials.gov (增强版) ====================
    async def fetch_clinical_trials(
        self, 
        search_term: str, 
        max_results: int = 100,
        status: Optional[List[str]] = None,
        phase: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        从ClinicalTrials.gov获取临床试验数据（增强版）
        """
        all_studies = []
        
        async with httpx.AsyncClient(timeout=self.timeout, proxy=None) as client:
            search_strategies = [
                {"query.cond": search_term, "query.intr": "vaccine"},
                {"query.term": f"{search_term} vaccine"},
                {"query.cond": search_term},
            ]
            
            for strategy in search_strategies:
                if len(all_studies) >= max_results:
                    break
                    
                try:
                    params = {
                        **strategy,
                        "pageSize": min(100, max_results - len(all_studies)),
                        "format": "json",
                        "fields": "NCTId,BriefTitle,OfficialTitle,OverallStatus,Phase,StartDate,CompletionDate,EnrollmentCount,StudyType,InterventionName,InterventionType,LeadSponsorName,LocationCountry,BriefSummary,EligibilityCriteria,PrimaryOutcomeMeasure,SecondaryOutcomeMeasure,MinimumAge,MaximumAge,Sex,Condition,Keyword"
                    }
                    
                    if status:
                        params["filter.overallStatus"] = ",".join(status)
                    if phase:
                        params["filter.phase"] = ",".join(phase)
                    
                    response = await client.get(
                        f"{self.apis['clinicaltrials']}/studies",
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        studies = data.get("studies", [])
                        
                        for study in studies:
                            protocol = study.get("protocolSection", {})
                            id_module = protocol.get("identificationModule", {})
                            status_module = protocol.get("statusModule", {})
                            design_module = protocol.get("designModule", {})
                            desc_module = protocol.get("descriptionModule", {})
                            arms_module = protocol.get("armsInterventionsModule", {})
                            sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
                            contacts_module = protocol.get("contactsLocationsModule", {})
                            eligibility_module = protocol.get("eligibilityModule", {})
                            outcomes_module = protocol.get("outcomesModule", {})
                            conditions_module = protocol.get("conditionsModule", {})
                            
                            nct_id = id_module.get("nctId")
                            
                            if any(s.get("nct_id") == nct_id for s in all_studies):
                                continue
                            
                            interventions = arms_module.get("interventions", [])
                            intervention_names = [i.get("name", "") for i in interventions]
                            
                            locations = contacts_module.get("locations", [])
                            countries = list(set([loc.get("country", "") for loc in locations if loc.get("country")]))
                            
                            primary_outcomes = outcomes_module.get("primaryOutcomes", [])
                            
                            all_studies.append({
                                "nct_id": nct_id,
                                "title": id_module.get("briefTitle"),
                                "official_title": id_module.get("officialTitle"),
                                "status": status_module.get("overallStatus"),
                                "phase": design_module.get("phases", ["N/A"])[0] if design_module.get("phases") else "N/A",
                                "start_date": status_module.get("startDateStruct", {}).get("date"),
                                "completion_date": status_module.get("completionDateStruct", {}).get("date"),
                                "enrollment": design_module.get("enrollmentInfo", {}).get("count"),
                                "study_type": design_module.get("studyType"),
                                "allocation": design_module.get("designInfo", {}).get("allocation"),
                                "interventions": intervention_names,
                                "sponsor": sponsor_module.get("leadSponsor", {}).get("name"),
                                "countries": countries,
                                "num_locations": len(locations),
                                "summary": desc_module.get("briefSummary"),
                                "conditions": conditions_module.get("conditions", []),
                                "keywords": conditions_module.get("keywords", []),
                                "min_age": eligibility_module.get("minimumAge"),
                                "max_age": eligibility_module.get("maximumAge"),
                                "sex": eligibility_module.get("sex"),
                                "primary_outcomes": [o.get("measure") for o in primary_outcomes[:3]],
                                "url": f"https://clinicaltrials.gov/study/{nct_id}",
                                "source": "clinicaltrials"
                            })
                            
                            if len(all_studies) >= max_results:
                                break
                                
                except Exception as e:
                    print(f"ClinicalTrials.gov API错误: {e}")
                    continue
        
        return all_studies[:max_results]
    
    # ==================== PubMed (保持原有) ====================
    async def fetch_pubmed(
        self, 
        search_term: str, 
        max_results: int = 100
    ) -> List[Dict]:
        """从PubMed获取文献数据"""
        articles = []
        
        async with httpx.AsyncClient(timeout=self.timeout, proxy=None) as client:
            try:
                search_response = await client.get(
                    f"{self.apis['pubmed']}/esearch.fcgi",
                    params={
                        "db": "pubmed",
                        "term": search_term,
                        "retmax": max_results,
                        "retmode": "json",
                        "sort": "relevance"
                    }
                )
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    id_list = search_data.get("esearchresult", {}).get("idlist", [])
                    
                    if id_list:
                        for i in range(0, len(id_list), 50):
                            batch = id_list[i:i+50]
                            
                            summary_response = await client.get(
                                f"{self.apis['pubmed']}/esummary.fcgi",
                                params={
                                    "db": "pubmed",
                                    "id": ",".join(batch),
                                    "retmode": "json"
                                }
                            )
                            
                            if summary_response.status_code == 200:
                                summary_data = summary_response.json()
                                results = summary_data.get("result", {})
                                
                                for pmid in batch:
                                    if pmid in results and pmid != "uids":
                                        article = results[pmid]
                                        
                                        authors = article.get("authors", [])
                                        author_str = ", ".join([
                                            a.get("name", "") for a in authors[:5]
                                        ])
                                        if len(authors) > 5:
                                            author_str += " et al."
                                        
                                        articles.append({
                                            "pmid": pmid,
                                            "title": article.get("title"),
                                            "authors": author_str,
                                            "journal": article.get("fulljournalname") or article.get("source"),
                                            "publication_date": article.get("pubdate"),
                                            "volume": article.get("volume"),
                                            "issue": article.get("issue"),
                                            "pages": article.get("pages"),
                                            "doi": next((id_info.get("value") for id_info in article.get("articleids", []) if id_info.get("idtype") == "doi"), None),
                                            "pub_type": article.get("pubtype", []),
                                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                                            "source": "pubmed"
                                        })
                            
                            await asyncio.sleep(0.5)
                            
            except Exception as e:
                print(f"PubMed API错误: {e}")
        
        return articles
    
    # ==================== 聚合搜索 ====================
    async def fetch_all(
        self,
        search_term: str,
        sources: List[str],
        max_results: int = 100,
        enrich_oa: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        从多个数据源并行获取数据
        
        Args:
            search_term: 搜索词
            sources: 数据源列表
            max_results: 每个数据源的最大结果数
            enrich_oa: 是否自动添加开放获取信息
        """
        results = {}
        tasks = []
        
        # 按数据源数量分配结果
        num_sources = len(sources)
        per_source_limit = max_results // num_sources if num_sources > 0 else max_results
        
        source_methods = {
            "clinicaltrials": lambda: self.fetch_clinical_trials(search_term, per_source_limit),
            "pubmed": lambda: self.fetch_pubmed(search_term, per_source_limit),
            "semantic_scholar": lambda: self.fetch_semantic_scholar(search_term, per_source_limit),
            "biorxiv": lambda: self.fetch_biorxiv(search_term, per_source_limit),
            "medrxiv": lambda: self.fetch_medrxiv(search_term, per_source_limit),
            "openalex": lambda: self.fetch_openalex(search_term, per_source_limit),
            "europe_pmc": lambda: self.fetch_europe_pmc(search_term, per_source_limit),
        }
        
        for source in sources:
            if source in source_methods:
                tasks.append((source, source_methods[source]()))
        
        # 并行执行
        for source, task in tasks:
            try:
                data = await task
                
                # 为文献类数据添加开放获取信息
                if enrich_oa and source in ["pubmed", "semantic_scholar", "openalex", "europe_pmc"]:
                    data = await self.enrich_with_open_access(data)
                
                results[source] = data
            except Exception as e:
                results[source] = []
                print(f"获取{source}数据失败: {e}")
        
        return results


class EnhancedDataSourceRegistry:
    """增强版数据源注册表"""
    
    SOURCES = {
        "clinicaltrials": {
            "name": "ClinicalTrials.gov",
            "description": "美国国立卫生研究院临床试验数据库",
            "url": "https://clinicaltrials.gov",
            "data_type": "clinical_trials",
            "category": "clinical_trials"
        },
        "pubmed": {
            "name": "PubMed",
            "description": "美国国家医学图书馆生物医学文献数据库",
            "url": "https://pubmed.ncbi.nlm.nih.gov",
            "data_type": "literature",
            "category": "literature"
        },
        "semantic_scholar": {
            "name": "Semantic Scholar",
            "description": "AI驱动的学术搜索引擎，提供引用分析和相关论文推荐",
            "url": "https://www.semanticscholar.org",
            "data_type": "literature",
            "category": "literature",
            "features": ["citation_count", "influential_citations", "open_access_pdf"]
        },
        "biorxiv": {
            "name": "bioRxiv",
            "description": "生物学预印本服务器，提供最新未经同行评审的研究",
            "url": "https://www.biorxiv.org",
            "data_type": "preprint",
            "category": "literature"
        },
        "medrxiv": {
            "name": "medRxiv",
            "description": "医学预印本服务器，提供最新未经同行评审的医学研究",
            "url": "https://www.medrxiv.org",
            "data_type": "preprint",
            "category": "literature"
        },
        "openalex": {
            "name": "OpenAlex",
            "description": "完全开放的学术数据库，包含引用网络和机构信息",
            "url": "https://openalex.org",
            "data_type": "literature",
            "category": "literature",
            "features": ["open_data", "institution_info", "concept_tags"]
        },
        "europe_pmc": {
            "name": "Europe PMC",
            "description": "欧洲生物医学文献数据库，支持全文挖掘",
            "url": "https://europepmc.org",
            "data_type": "literature",
            "category": "literature",
            "features": ["full_text_mining", "mesh_terms"]
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
    def get_sources_by_category(cls, category: str) -> List[Dict]:
        """按类别获取数据源"""
        return [
            {"id": k, **v}
            for k, v in cls.SOURCES.items()
            if v.get("category") == category
        ]
    
    @classmethod
    def get_source_info(cls, source_id: str) -> Optional[Dict]:
        """获取数据源信息"""
        if source_id in cls.SOURCES:
            return {"id": source_id, **cls.SOURCES[source_id]}
        return None
