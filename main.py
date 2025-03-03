from fastapi import FastAPI, Query, BackgroundTasks
import sqlite3
import pandas as pd
import re
import time
from jobspy import scrape_jobs
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

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
            timestamp TEXT,
            posted_date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()  # 服务器启动时，初始化数据库

def load_job_data(keyword, results_wanted=150):
    """爬取职位数据"""
    jobs = scrape_jobs(
        site_name=["linkedin", "glassdoor", "indeed"],
        search_term=keyword,
        location="United States",
        results_wanted=results_wanted,
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
    if not keywords or jobs.empty:  # 添加空数据框检查
        return jobs

    # 确保description列存在
    if 'description' not in jobs.columns:
        jobs['description'] = 'No description available'

    def find_removal_reasons(description):
        return ', '.join(re.findall('|'.join(map(re.escape, keywords)), description, re.IGNORECASE)) if pd.notna(description) else ''
    
    jobs['Removal_Reason'] = jobs['description'].apply(find_removal_reasons)
    condition = jobs['description'].str.contains('|'.join(map(re.escape, keywords)), na=False, case=False)
    return jobs[~condition]

def filter_jobs_by_title(jobs, title_keywords):
    """过滤职位标题"""
    if not title_keywords:
        return jobs
    
    condition = jobs['title'].str.contains('|'.join(map(re.escape, title_keywords)), na=False, case=False)
    return jobs[~condition]

def scrape_and_save_jobs(query: str, keywords: list, title_keywords: list, results_wanted: int):
    """爬取数据，并存入数据库"""
    print(f"开始爬取: {query}")
    start_time = time.time()
    
    try:
        # 爬取职位数据，传入爬取数量参数
        jobs = load_job_data(query, results_wanted)
        
        # 检查是否成功获取到数据
        if jobs is None or jobs.empty:
            print(f"未找到任何职位: {query}")
            return
            
        # 确保必要的列存在
        required_columns = ['title', 'company', 'location', 'job_url', 'description']
        for col in required_columns:
            if col not in jobs.columns:
                jobs[col] = 'N/A'
        
        jobs = remove_duplicate_jobs(jobs)
        jobs = filter_jobs_by_keywords(jobs, keywords)
        jobs = filter_jobs_by_title(jobs, title_keywords)

        # 连接数据库
        conn = sqlite3.connect("jobs.db")
        c = conn.cursor()

        # 确保数据库表结构正确
        c.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                company TEXT,
                location TEXT,
                job_url TEXT,
                description TEXT,
                search_query TEXT,
                timestamp TEXT,
                posted_date TEXT
            )
        """)
        conn.commit()

        # 清除旧数据
        c.execute("DELETE FROM jobs WHERE search_query = ?", (query,))

        # 插入新数据
        for _, job in jobs.iterrows():
            c.execute("""
                INSERT INTO jobs (
                    title, company, location, job_url, description, 
                    search_query, timestamp, posted_date
                ) 
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)
            """, (
                job["title"], job["company"], job["location"], 
                job["job_url"], job["description"], query, 
                job.get("posted_date", "N/A")  # 获取发布日期，如果没有则显示N/A
            ))

        conn.commit()
        conn.close()

        end_time = time.time()
        print(f"爬取完成: {query}, 耗时: {end_time - start_time:.2f} 秒")
        
    except Exception as e:
        print(f"爬取过程中出错: {str(e)}")
        # 可以在这里添加错误处理逻辑，比如记录日志等

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/start_scrape")
async def start_scrape(
    query: str = Query("data scientist", description="职位关键词"),
    exclude_keywords: str = Query("", description="要排除的关键词（逗号分隔）"),
    exclude_titles: str = Query("", description="要排除的职位头衔（逗号分隔）"),
    results_wanted: int = Query(150, description="需要爬取的职位数量"),
    background_tasks: BackgroundTasks = None
):
    """异步启动爬取任务"""
    
    # 首先检查数据库表结构
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    
    # 检查是否存在posted_date列
    c.execute("PRAGMA table_info(jobs)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'posted_date' not in columns:
        # 添加posted_date列
        c.execute("ALTER TABLE jobs ADD COLUMN posted_date TEXT")
        conn.commit()
    
    conn.close()
    
    # 默认排除的关键词
    default_keywords = ['5+', 'Secret Clearance', 'security clearance', 'US Citizen', 'TS/SCI', 'not sponsor']
    default_titles = ['Director', 'Manager', 'Lead', 'Principal', 'AVP', 'Intern']

    # 用户输入的排除关键词
    user_keywords = [k.strip() for k in exclude_keywords.split(",")] if exclude_keywords else []
    user_titles = [t.strip() for t in exclude_titles.split(",")] if exclude_titles else []

    # 合并默认关键词和用户关键词
    keywords = list(set(default_keywords + user_keywords))
    title_keywords = list(set(default_titles + user_titles))

    # 添加异步任务，传入爬取数量参数
    background_tasks.add_task(scrape_and_save_jobs, query, keywords, title_keywords, results_wanted)
    
    return {"message": f"爬取任务已启动: {query}，请稍后查询结果！"}

@app.get("/get_jobs")
def get_jobs(query: str = Query("data scientist", description="职位关键词")):
    """查询数据库中的职位数据"""
    conn = sqlite3.connect("jobs.db")
    c = conn.cursor()
    c.execute("""
        SELECT title, company, location, job_url, description, 
               CASE 
                   WHEN job_url LIKE '%linkedin%' THEN 'LinkedIn'
                   WHEN job_url LIKE '%glassdoor%' THEN 'Glassdoor'
                   WHEN job_url LIKE '%indeed%' THEN 'Indeed'
                   ELSE 'Other'
               END as source,
               posted_date
        FROM jobs 
        WHERE search_query=? 
        ORDER BY 
            CASE 
                WHEN posted_date = 'N/A' THEN 1 
                ELSE 0 
            END,
            posted_date DESC
    """, (query,))
    jobs = c.fetchall()
    conn.close()
    
    if not jobs:
        return {"message": f"数据未就绪，请稍后再试: {query}"}
    
    return {
        "query": query,
        "jobs": [{
            "title": j[0], 
            "company": j[1], 
            "location": j[2], 
            "job_url": j[3], 
            "description": j[4],
            "source": j[5],
            "posted_date": j[6]
        } for j in jobs]
    }
