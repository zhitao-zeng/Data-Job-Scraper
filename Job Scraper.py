import pandas as pd
import re
import datetime
import csv
from jobspy import scrape_jobs
import os

def load_job_data(keyword):
    """Scrape job listings from multiple sites."""
    jobs = scrape_jobs(
        #site_name=[ "linkedin", "zip_recruiter", "glassdoor"],
        site_name=[ "linkedin",  "glassdoor"],
        search_term=keyword,
        location="United States",
        results_wanted=150,
        hours_old=24,  # Specific to Linkedin/Indeed
        country_indeed='USA',
        linkedin_fetch_description=True
    )
    #print(f"Found {len(jobs)} jobs")
    #print(jobs.head())
    return jobs

def remove_duplicate_jobs(jobs):
    """Remove duplicate jobs based on title, company, and location."""
    return jobs.drop_duplicates(subset=['title', 'company'], keep='first', inplace=False)

def find_removal_reasons(description, keywords):
    """Identify keywords in job descriptions."""
    escaped_keywords = [re.escape(keyword) for keyword in keywords]
    pattern = '|'.join(escaped_keywords)
    return ', '.join(re.findall(pattern, description, re.IGNORECASE))

def filter_jobs_by_keywords(jobs, keywords):
    """Filter jobs by keywords and create a column for removal reasons."""
    jobs['Removal_Reason'] = jobs['description'].apply(
        lambda desc: find_removal_reasons(desc, keywords) if pd.notna(desc) else ''
    )
    condition = jobs['description'].str.contains('|'.join(map(re.escape, keywords)), na=False, case=False)
    return jobs[~condition], jobs[condition]

def filter_jobs_by_title(jobs, title_keywords):
    """Filter jobs by title keywords."""
    condition = jobs['title'].str.contains('|'.join(map(re.escape, title_keywords)), na=False, case=False)
    return jobs[~condition]

def delete_jobs_by_company(jobs, companies_to_delete):
    """Delete jobs from the DataFrame based on a list of company names."""
    return jobs[~jobs['company'].isin(companies_to_delete)]

def save_jobs_to_csv(jobs, filename):
    """Save jobs to a CSV file."""
    jobs.to_csv(filename, quoting=csv.QUOTE_NONNUMERIC, escapechar='\\', index=False)
def read_previous_data(yesterday):
    """Read previous day's job data from CSV."""
    filename = f"jobs_{yesterday}.csv"
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        print("No data for previous day.")
        return pd.DataFrame()

def compute_difference(today_jobs, yesterday_jobs):
    """Compute the difference between today's and yesterday's job listings."""
    if not yesterday_jobs.empty:
        diff_jobs = pd.concat([today_jobs, yesterday_jobs]).drop_duplicates(subset=['title', 'company'], keep=False)
        return diff_jobs
    else:
        print("No previous day's data to compare. Saving only today's data.")
        return pd.DataFrame()

def save_jobs_to_csv(jobs, filename):
    """Save jobs to a CSV file."""
    if not jobs.empty:
        jobs.to_csv(filename, quoting=csv.QUOTE_NONNUMERIC, escapechar='\\', index=False)
        print(f"Data saved to {filename}")
    else:
        print(f"No new or different data to save for {filename}")

def main():
    # 获取今天和昨天的日期
    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)

    # 定义关键词和职位关键词
    keywords = ['5+', 'Secret Clearance', 'security clearance','US Citizen', '3+', '4+', 'TS/SCI', '5+','6+', '7+','8+', '6-10','8-10','5-7','Minimum 5 years','Must be a U.S Citizen',
                'Minimum of 5 years',"U.S. Citizen",'At least 5 years',"5-10 years","Minimum of 3 years","5 years of experience","Minimum of five years",'Minimum of 7 years',
                "Five (5) years’ experience",'3-5 years','Experience level: 5 years','Minimum 3 years',"3 or more years","Six or more years",'not sponsor',"it is not our practice to sponsor individuals for work visas"] 
    title_keywords = ['Director', 'Manager','Lead','Principal','AVP','Intern']

    # 定义需要查询的职位类型
    job_types = [ "data scientist","data analyst","Model Risk","data engineer"]

    # 初始化一个空的DataFrame来存储所有结果
    all_jobs = pd.DataFrame()

    for job_type in job_types:
        # 加载每个职位类型的工作数据
        today_jobs = load_job_data(job_type)
        
        # 删除重复项
        today_jobs.drop_duplicates(subset=['title', 'company', 'location'], keep='first', inplace=True)

        # 删除合同类型的工作
        today_jobs = today_jobs[today_jobs['job_type'].str.lower() != 'contract']
        
        # 删除指定公司的工作
        companies_to_delete = ['Opinion Focus Panel LLC', 'Diverserec','myGwork - LGBTQ+ Business Community','Jobs for Humanity','Team Remotely Inc','HireMeFast LLC','Phoenix Recruitment','ClearanceJobs','Augment Jobs','Jobot',"Dice","Jobs via eFinancialCareers",'Energy Jobline']
        today_jobs = delete_jobs_by_company(today_jobs, companies_to_delete)

        # 使用关键词过滤工作
        today_filtered, removed_jobs = filter_jobs_by_keywords(today_jobs, keywords)
        
        # 使用职位关键词进一步过滤
        today_filtered_final = filter_jobs_by_title(today_filtered, title_keywords)
        
        # 将过滤后的结果添加到总的DataFrame中
        all_jobs = pd.concat([all_jobs, today_filtered_final])

    # 删除合并后的DataFrame中的重复项
    all_jobs.drop_duplicates(subset=['title', 'company'], keep='first', inplace=True)

    # 保存到CSV文件
    today_file = f"jobs_{today}.csv"
    all_jobs.to_csv(today_file, index=False,quotechar='"', quoting=2)

    print(f"Found {len(all_jobs)} unique jobs across all categories.")

if __name__ == "__main__":
    main()
