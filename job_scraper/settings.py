"""Settings for job_scraper."""
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent

TIMEOUT_LIMIT_SECONDS = 10

# LinkedIn
LOGIN_PAGE = "https://www.linkedin.com/login"
COMPANY_PAGE = "https://www.linkedin.com/company"
JOB_LIST_PAGE = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
JOB_DETAIL_PAGE = "https://www.linkedin.com/jobs/view"
JOBS_PER_PAGE = 25
MAX_JOBS = 1000 - JOBS_PER_PAGE

# Selenium
WEBDRIVER_PATH = Path.home() / "chromedriver" / "stable"

# Database
SQLITE_DATABASE_URL = f"sqlite:///{PROJECT_DIR}/linkedin.sqlite3"
