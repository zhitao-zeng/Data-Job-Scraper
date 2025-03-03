from fastapi import FastAPI, Query
from jobspy import scrape_jobs
import pandas as pd
import re

app = FastAPI()

def load_job_data(keyword):
    """Scrape job listings from multiple sites."""
    jobs = scrape_jobs(
        site_name=["linkedin", "glassdoor", "indeed"],
        search_term=keyword,
        location="United States",
        results_wanted=150,
        hours_old=24,  # Specific to Linkedin/Indeed
        country_indeed='USA',
        linkedin_fetch_description=True
    )
    return jobs

def remove_duplicate_jobs(jobs):
    """Remove duplicate jobs based on title, company."""
    return jobs.drop_duplicates(subset=['title', 'company'], keep='first')

def filter_jobs_by_keywords(jobs, keywords):
    """Filter jobs by specified keywords in job description."""
    if not keywords:
        return jobs  # 如果用户没传关键词，则不进行过滤

    def find_removal_reasons(description):
        return ', '.join(re.findall('|'.join(map(re.escape, keywords)), description, re.IGNORECASE)) if pd.notna(description) else ''
    
    jobs['Removal_Reason'] = jobs['description'].apply(find_removal_reasons)
    condition = jobs['description'].str.contains('|'.join(map(re.escape, keywords)), na=False, case=False)
    return jobs[~condition]  # 只返回未被过滤的职位

def filter_jobs_by_title(jobs, title_keywords):
    """Filter out jobs with certain titles."""
    if not title_keywords:
        return jobs  # 如果用户没传关键词，则不进行过滤
    
    condition = jobs['title'].str.contains('|'.join(map(re.escape, title_keywords)), na=False, case=False)
    return jobs[~condition]

@app.get("/")
def home():
    return {"message": "Data Job Scraper API is running!"}

@app.get("/jobs")
def get_jobs(
    query: str = Query("data scientist", description="Job title to search"),
    exclude_keywords: str = Query("", description="Comma-separated keywords to filter out from job descriptions"),
    exclude_titles: str = Query("", description="Comma-separated job titles to filter out")
):
    """API 端点，查询职位信息"""
    
    # 默认关键词（如果用户没传，就使用默认）
    default_keywords = ['5+', 'Secret Clearance', 'security clearance', 'US Citizen', 'TS/SCI', 'not sponsor']
    default_titles = ['Director', 'Manager', 'Lead', 'Principal', 'AVP', 'Intern']

    # 解析用户输入的关键词
    user_keywords = [k.strip() for k in exclude_keywords.split(",")] if exclude_keywords else []
    user_titles = [t.strip() for t in exclude_titles.split(",")] if exclude_titles else []

    # 组合用户和默认关键词
    keywords = list(set(default_keywords + user_keywords))
    title_keywords = list(set(default_titles + user_titles))

    # 加载数据
    jobs = load_job_data(query)
    jobs = remove_duplicate_jobs(jobs)

    # 过滤数据
    jobs = filter_jobs_by_keywords(jobs, keywords)
    jobs = filter_jobs_by_title(jobs, title_keywords)

    # 选择返回的字段
    jobs = jobs[['title', 'company', 'location', 'job_url', 'description']].to_dict(orient="records")

    return {
        "query": query,
        "exclude_keywords": keywords,
        "exclude_titles": title_keywords,
        "jobs": jobs
    }
