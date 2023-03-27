"""Scraping LinkedIn with Selenium"""
import os

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from job_scraper.settings import LOGIN_PAGE, TIMEOUT_LIMIT_SECONDS, WEBDRIVER_PATH

load_dotenv()


def authenticate(browser: webdriver.Chrome, login_url: str) -> None:
    """Authenticate a browser with LinkedIn credentials."""
    browser.get(login_url)

    email = browser.find_element(By.ID, "username")
    email.send_keys(os.getenv("LINKEDIN_USERNAME"))
    password = browser.find_element(By.ID, "password")
    password.send_keys(os.getenv("LINKEDIN_PASSWORD"))
    password.send_keys(Keys.RETURN)
    WebDriverWait(browser, timeout=TIMEOUT_LIMIT_SECONDS).until(
        EC.presence_of_element_located((By.XPATH, "//h1[text()='Feed Updates']"))
    )


def get_chrome() -> webdriver.Chrome:
    """Return a Chrome browser instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off
    chrome_options.add_argument("--no-sandbox")

    webdriver_service = Service(str(WEBDRIVER_PATH / "chromedriver"))
    browser = webdriver.Chrome(service=webdriver_service, options=chrome_options)

    return browser


def scrape_jobs_url(company_page_url: str) -> str | None:
    """Scrape the jobs URL from a company page."""
    browser = get_chrome()
    authenticate(browser, LOGIN_PAGE)
    browser.get(company_page_url)
    # jobs_selector = browser.find_elements(
    #     By.CLASS_NAME, "org-jobs-recently-posted-jobs-module"
    # )
    jobs_selector = WebDriverWait(browser, timeout=TIMEOUT_LIMIT_SECONDS).until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, "org-jobs-recently-posted-jobs-module")
        )
    )

    try:
        see_all_jobs_btn = jobs_selector.find_elements(By.TAG_NAME, "a")[0]
        jobs_url = see_all_jobs_btn.get_attribute("href")
    except IndexError:
        return None
    finally:
        browser.quit()
    return jobs_url
