import json
import os
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

DATA_FILE = "jobs_data.json"

# --- 검색 및 태깅 키워드 ---
PRIORITY_1_KEYWORDS = ["하중해석", "하중 해석", "load analysis", "loads analysis", "통합하중", "통합 하중", "aeroelastic", "bladed", "openfast"]
PRIORITY_2_KEYWORDS = ["해상풍력", "해상 풍력", "offshore wind", "풍력발전", "하부구조물", "substructure", "jacket", "monopile"]
TARGET_COMPANIES = ["두산에너빌리티", "한화오션", "포스코인터내셔널"]
SEARCH_KEYWORDS = ["해상풍력 하중해석", "해상풍력", "하부구조물"] # 사람인/원티드 검색용

# 브라우저인 것처럼 속이는 헤더 (차단 방지)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def evaluate_priority(title, company, description=""):
    """제목과 회사명을 기반으로 1, 2, 3순위를 판정합니다."""
    text = f"{title} {description}".lower()
    
    if any(kw.lower() in text for kw in PRIORITY_1_KEYWORDS):
        return "1순위 (해상풍력 하중해석)"
    elif any(kw.lower() in text for kw in PRIORITY_2_KEYWORDS):
        return "2순위 (해상풍력 연관)"
    elif any(tc.lower() in company.lower() for tc in TARGET_COMPANIES):
        return "3순위 (타깃 기업 일반)"
    else:
        return "기타"

# ==========================================
# 1. 사람인 (Saramin) 크롤러
# ==========================================
def crawl_saramin(keyword):
    jobs = []
    print(f"[*] 사람인 검색 시작: {keyword}")
    url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={keyword}"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select(".item_recruit")
        
        for item in items:
            title_tag = item.select_one(".job_tit a")
            company_tag = item.select_one(".corp_name a")
            cond_tags = item.select(".job_condition span")
            
            if title_tag and company_tag:
                title = title_tag.get("title", "").strip()
                company = company_tag.text.strip()
                link = "https://www.saramin.co.kr" + title_tag.get("href", "")
                
                deadline = cond_tags[0].text.strip() if len(cond_tags) > 0 else "상시채용"
                location = cond_tags[1].text.strip() if len(cond_tags) > 1 else ""
                
                jobs.append({
                    "id": f"saramin-{link.split('rec_idx=')[-1][:8]}",
                    "company": company,
                    "title": title,
                    "url": link,
                    "source": "사람인",
                    "posted_date": datetime.now().strftime("%Y-%m-%d"),
                    "deadline": deadline,
                    "location": location,
                    "tech_stack": "",
                    "summary": ""
                })
    except Exception as e:
        print(f"[!] 사람인 크롤링 에러: {e}")
    
    time.sleep(1)
    return jobs

# ==========================================
# 2. 원티드 (Wanted) 크롤러
# ==========================================
def crawl_wanted(keyword):
    jobs = []
    print(f"[*] 원티드 검색 시작: {keyword}")
    url = f"https://www.wanted.co.kr/api/v4/jobs?country=kr&locations=all&years=-1&limit=20&query={keyword}"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        data = res.json()
        
        if "data" in data and data["data"]:
            for item in data["data"]:
                job = item.get("job", {})
                comp = item.get("company", {})
                
                jobs.append({
                    "id": f"wanted-{job.get('id')}",
                    "company": comp.get("name", ""),
                    "title": job.get("title", ""),
                    "url": f"https://www.wanted.co.kr/wd/{job.get('id')}",
                    "source": "원티드",
                    "posted_date": datetime.now().strftime("%Y-%m-%d"),
                    "deadline": "상시채용",
                    "location": job.get("address", {}).get("location", ""),
                    "tech_stack": "",
                    "summary": ""
                })
    except Exception as e:
        print(f"[!] 원티드 크롤링 에러: {e}")
    
    time.sleep(1)
    return jobs

def main_collector():
    all_jobs = []
    for kw in SEARCH_KEYWORDS:
        all_jobs.extend(crawl_saramin(kw))
        all_jobs.extend(crawl_wanted(kw))
        
    unique_jobs = {}
    for job in all_jobs:
        if job["url"] not in unique_jobs:
            unique_jobs[job["url"]] = job
            
    final_jobs = list(unique_jobs.values())
    for job in final_jobs:
        job["priority"] = evaluate_priority(job["title"], job["company"])
        
    return final_jobs

if __name__ == "__main__":
    collected = main_collector()
    
    existing_data = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            pass
            
    existing_urls = {job["url"] for job in existing_data}
    
    for job in collected:
        if job["url"] not in existing_urls:
            existing_data.append(job)
            
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
