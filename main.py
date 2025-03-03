from fastapi import FastAPI, Query, BackgroundTasks
import sqlite3
import pandas as pd
import re
import time
from jobspy import scrape_jobs

app = FastAPI()

# 初始化 SQLite 数据库
def init_db():
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            job_url TEXT,
            description TEXT,
            search_query TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()  # 服务器启动时，初始化数据库

def load_job_data(keyword):
    """爬取职位数据"""
    jobs = scrape_jobs(
        site_name=["linkedin", "glassdoor", "indeed"],
        search_term=keyword,
        location="United States",
        results_wanted=150,
        hours_old=24,
        country_indeed='USA',
        linkedin_fetch_description=True
    )
    return jobs

def remove_duplicate_jobs(jobs):
    """去除重复职位"""
    return jobs.drop_duplicates(subset=['title', 'company'], keep='first')

def filter_jobs_by_keywords(jobs, keywords):
    """过滤职位描述中的关键词"""
    if not keywords:
        return jobs

    def find_removal_reasons(description):
        return ', '.join(re.findall('|'.join(map(re.escape, keywords)), description, re.IGNORECASE)) if pd.notna(description) else ''
    
    jobs['Removal_Reason'] = jobs['description'].apply(find_removal_reasons)
    condition = jobs['description'].str.contains('|'.join(map(re.escape, keywords)), na=False, case=False)
    return jobs[~condition]  # 只返回未被过滤的职位

def filter_jobs_by_title(jobs, title_keywords):
    """过滤职位标题"""
    if not title_keywords:
        return jobs
    
    condition = jobs['title'].str.contains('|'.join(map(re.escape, title_keywords)), na=False, case=False)
    return jobs[~condition]

def scrape_and_save_jobs(query: str, keywords: list, title_keywords: list):
    """爬取数据，并存入数据库"""
    print(f"开始爬取: {query}")
    start_time = time.time()
    
    # 爬取职位数据
    jobs = load_job_data(query)
    jobs = remove_duplicate_jobs(jobs)
    jobs = filter_jobs_by_keywords(jobs, keywords)
    jobs = filter_jobs_by_title(jobs, title_keywords)

    # 连接数据库
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()

    # 清除旧数据
    c.execute("DELETE FROM jobs WHERE search_query = ?", (query,))

    # 插入新数据
    for _, job in jobs.iterrows():
        c.execute("""
            INSERT INTO jobs (title, company, location, job_url, description, search_query, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (job["title"], job["company"], job["location"], job["job_url"], job["description"], query))

    conn.commit()
    conn.close()

    end_time = time.time()
    print(f"爬取完成: {query}, 耗时: {end_time - start_time:.2f} 秒")

@app.get("/")
def home():
    return {"message": "Data Job Scraper API is running!"}

@app.get("/start_scrape")
async def start_scrape(
    query: str = Query("data scientist", description="职位关键词"),
    exclude_keywords: str = Query("", description="要排除的关键词（逗号分隔）"),
    exclude_titles: str = Query("", description="要排除的职位头衔（逗号分隔）"),
    background_tasks: BackgroundTasks = None
):
    """异步启动爬取任务"""
    
    # 默认排除的关键词
    default_keywords = ['5+', 'Secret Clearance', 'security clearance', 'US Citizen', 'TS/SCI', 'not sponsor']
    default_titles = ['Director', 'Manager', 'Lead', 'Principal', 'AVP', 'Intern']

    # 用户输入的排除关键词
    user_keywords = [k.strip() for k in exclude_keywords.split(",")] if exclude_keywords else []
    user_titles = [t.strip() for t in exclude_titles.split(",")] if exclude_titles else []

    # 合并默认关键词和用户关键词
    keywords = list(set(default_keywords + user_keywords))
    title_keywords = list(set(default_titles + user_titles))

    # 添加异步任务
    background_tasks.add_task(scrape_and_save_jobs, query, keywords, title_keywords)
    
    return {"message": f"爬取任务已启动: {query}，请稍后查询结果！"}

@app.get("/get_jobs")
def get_jobs(query: str = Query("data scientist", description="职位关键词")):
    """查询数据库中的职位数据"""
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    c.execute("SELECT title, company, location, job_url, description FROM jobs WHERE search_query=? ORDER BY timestamp DESC", (query,))
    jobs = c.fetchall()
    conn.close()
    
    if not jobs:
        return {"message": f"数据未就绪，请稍后再试: {query}"}
    
    return {
        "query": query,
        "jobs": [{"title": j[0], "company": j[1], "location": j[2], "job_url": j[3], "description": j[4]} for j in jobs]
    }
