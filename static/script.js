let jobsData = []; // 存储职位数据

async function startScrape() {
    const searchQuery = document.getElementById('searchQuery').value;
    const excludeKeywords = document.getElementById('excludeKeywords').value;
    const excludeTitles = document.getElementById('excludeTitles').value;
    const resultsWanted = document.getElementById('resultsWanted').value;
    
    const message = document.getElementById('message');
    message.innerHTML = '正在搜索职位，请稍候...';
    message.className = 'message';
    
    try {
        const response = await fetch(`/start_scrape?query=${encodeURIComponent(searchQuery)}&exclude_keywords=${encodeURIComponent(excludeKeywords)}&exclude_titles=${encodeURIComponent(excludeTitles)}&results_wanted=${resultsWanted}`);
        const data = await response.json();
        
        message.innerHTML = data.message;
        message.className = 'message success';
    } catch (error) {
        message.innerHTML = '发生错误，请稍后重试';
        message.className = 'message error';
    }
}

async function getJobs() {
    const searchQuery = document.getElementById('searchQuery').value;
    const message = document.getElementById('message');
    const loading = document.getElementById('loading');
    const jobsList = document.getElementById('jobsList');
    const statsSection = document.getElementById('statsSection');
    
    // 显示加载动画
    loading.style.display = 'block';
    jobsList.innerHTML = '';
    statsSection.style.display = 'none';
    
    try {
        const response = await fetch(`/get_jobs?query=${encodeURIComponent(searchQuery)}`);
        const data = await response.json();
        
        if (data.message) {
            message.innerHTML = data.message;
            message.className = 'message';
            loading.style.display = 'none';
            return;
        }
        
        jobsData = data.jobs; // 保存职位数据
        updateJobsDisplay();
        
        // 显示统计信息
        const stats = calculateStats(jobsData);
        document.querySelector('.stats-info').innerHTML = 
            `找到 ${jobsData.length} 个职位 | ${stats.companies} 家公司 | ${stats.locations} 个地区`;
        
        statsSection.style.display = 'flex';
        message.innerHTML = '';
        
    } catch (error) {
        message.innerHTML = '获取数据时发生错误';
        message.className = 'message error';
    } finally {
        loading.style.display = 'none';
    }
}

function calculateStats(jobs) {
    const companies = new Set(jobs.map(job => job.company)).size;
    const locations = new Set(jobs.map(job => job.location)).size;
    return { companies, locations };
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatPostedDate(postedDate) {
    if (postedDate === 'N/A') return '发布日期未知';
    
    // 尝试解析日期
    const date = new Date(postedDate);
    if (isNaN(date.getTime())) {
        // 如果无法解析为日期，直接返回原始文本
        return postedDate;
    }
    
    // 计算发布时间距离现在的时间
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return '今天';
    if (diffDays === 1) return '昨天';
    if (diffDays < 7) return `${diffDays}天前`;
    if (diffDays < 30) return `${Math.floor(diffDays/7)}周前`;
    if (diffDays < 365) return `${Math.floor(diffDays/30)}个月前`;
    return `${Math.floor(diffDays/365)}年前`;
}

function getSourceIcon(source) {
    switch(source) {
        case 'LinkedIn':
            return 'fab fa-linkedin';
        case 'Glassdoor':
            return 'fas fa-door-open';
        case 'Indeed':
            return 'fas fa-search';
        default:
            return 'fas fa-globe';
    }
}

function updateJobsDisplay() {
    const jobsList = document.getElementById('jobsList');
    
    jobsList.innerHTML = jobsData.map(job => {
        const skills = [...new Set(job.description.match(/[A-Z][a-zA-Z]+/g) || [])];
        const skillTags = skills.slice(0, 5).map(skill => `<span class="tag">${skill}</span>`).join('');
        
        return `
            <div class="job-card">
                <div class="job-header">
                    <div class="job-info">
                        <h2 class="job-title">${job.title}</h2>
                        <div class="job-meta">
                            <span><i class="fas fa-building"></i>${job.company}</span>
                            <span><i class="fas fa-map-marker-alt"></i>${job.location}</span>
                            <span><i class="far fa-clock"></i>${formatPostedDate(job.posted_date)}</span>
                        </div>
                    </div>
                    <div class="job-meta-right">
                        <span class="source-tag source-${job.source.toLowerCase()}">
                            <i class="${getSourceIcon(job.source)}"></i>
                            ${job.source}
                        </span>
                    </div>
                </div>
                <div class="job-tags">
                    ${skillTags}
                </div>
                <div class="job-description" onclick="toggleDescription(this)">
                    ${job.description}
                    <div class="description-fade"></div>
                </div>
                <button class="expand-btn" onclick="event.stopPropagation(); toggleDescription(this.previousElementSibling)">
                    展开详情
                </button>
                <a href="${job.job_url}" target="_blank" class="job-url">查看职位详情</a>
            </div>
        `;
    }).join('');
}

function toggleDescription(element) {
    element.classList.toggle('expanded');
    const btn = element.nextElementSibling;
    btn.textContent = element.classList.contains('expanded') ? '收起详情' : '展开详情';
}

function sortJobs() {
    const sortBy = document.getElementById('sortSelect').value;
    
    switch(sortBy) {
        case 'date':
            jobsData.sort((a, b) => {
                if (a.posted_date === 'N/A') return 1;
                if (b.posted_date === 'N/A') return -1;
                return new Date(b.posted_date) - new Date(a.posted_date);
            });
            break;
        case 'company':
            jobsData.sort((a, b) => a.company.localeCompare(b.company));
            break;
        case 'title':
            jobsData.sort((a, b) => a.title.localeCompare(b.title));
            break;
        case 'location':
            jobsData.sort((a, b) => a.location.localeCompare(b.location));
            break;
        default:
            return;
    }
    
    updateJobsDisplay();
} 