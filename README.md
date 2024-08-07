### Project Title: Automated Job Data Scraper and Filtering System

#### Project Overview:
The Automated Job Data Scraper and Filtering System is a Python-based tool designed to streamline the process of job searching by scraping job listings from multiple online job portals, filtering out irrelevant or undesirable listings based on predefined criteria, and saving the refined data to a CSV file for further analysis. This project is particularly useful for job seekers who want to target specific roles while avoiding positions that do not meet their experience level, job title preferences, or company preferences.

#### Key Features:
1. **Multi-Site Job Scraping**:
   - The system utilizes the `jobspy` library to scrape job listings from multiple platforms, including LinkedIn, Glassdoor, and Indeed. It can retrieve up to 150 job postings per keyword search, ensuring a comprehensive collection of opportunities.

2. **Duplicate Removal**:
   - The system automatically removes duplicate job listings based on the job title and company name, ensuring that only unique opportunities are retained for further processing.

3. **Keyword-Based Filtering**:
   - The tool allows users to specify keywords related to experience requirements (e.g., "5+", "TS/SCI", "U.S. Citizen") and other criteria that are often deal-breakers for job applications. Jobs containing these keywords in their descriptions are identified and flagged for removal.

4. **Title-Based Filtering**:
   - In addition to description-based filtering, the system can filter out jobs based on specific title keywords (e.g., "Director", "Manager", "Lead"). This ensures that only positions matching the user’s desired career level are retained.

5. **Company-Based Exclusion**:
   - Users can specify a list of companies whose job postings they wish to exclude from the results. The system automatically filters out any jobs from these companies, refining the search results to align more closely with user preferences.

6. **Daily Job Comparison**:
   - The system compares job listings scraped on the current day with those from the previous day, identifying new or different listings. This feature is particularly useful for job seekers who want to stay updated on the latest opportunities without reviewing the same listings repeatedly.

7. **CSV Export**:
   - After processing and filtering, the system saves the refined job listings to a CSV file, named according to the current date. This file can be easily accessed and analyzed using standard data analysis tools.

#### Project Architecture:
- **Data Collection**: The `scrape_jobs` function collects job listings from specified online job portals.
- **Data Processing**: Jobs are filtered based on criteria such as experience level, job title, and company preferences.
- **Data Comparison**: The system compares the current day's listings with those from the previous day to identify new opportunities.
- **Data Storage**: Filtered job listings are saved to a CSV file for further analysis.

#### Technologies Used:
- **Python**: Core programming language for the project.
- **Pandas**: Used for data manipulation and filtering.
- **Regular Expressions (re)**: Used for keyword-based filtering in job descriptions.
- **Datetime**: Used to handle date comparisons and file naming.
- **CSV Module**: Used for exporting the processed data to a CSV file.
- **jobspy Library**: Used for scraping job data from multiple online platforms.

#### Potential Use Cases:
- **Job Seekers**: Individuals seeking specific roles can use this tool to automatically find and filter job opportunities that match their criteria.
- **Recruitment Agencies**: Agencies can automate the collection and filtering of job listings to present only the most relevant opportunities to their clients.
- **Career Services**: University career centers can use this tool to find job opportunities tailored to the specific needs of their students.

#### Future Enhancements:
- **Real-Time Alerts**: Implement a feature to send email or SMS alerts when new jobs matching the user's criteria are found.
- **Expanded Job Sources**: Integrate additional job portals for an even broader range of opportunities.
- **GUI Integration**: Develop a user-friendly graphical interface to make the tool accessible to non-technical users.

This project demonstrates the practical application of web scraping, data filtering, and automation to streamline job search processes, making it a valuable tool for anyone actively seeking new career opportunities.
