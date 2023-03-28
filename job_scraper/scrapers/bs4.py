"""Scraping LinkedIn with BeautifulSoup"""
import logging
import re
import time
from collections.abc import Generator
from datetime import datetime
from http import HTTPStatus
from urllib.parse import parse_qs, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup
from bs4.element import Tag
from fake_useragent import UserAgent

from job_scraper.companies import Company
from job_scraper.locations import Location
from job_scraper.models import JobPost
from job_scraper.settings import (
    JOB_DETAIL_PAGE,
    JOB_LIST_PAGE,
    JOBS_PER_PAGE,
    MAX_JOBS,
    TIMEOUT_LIMIT_SECONDS,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # type: ignore


user_agent = UserAgent()


class JobPostNotFoundError(Exception):
    """Raised when a job post is not found"""


def _get_job_list_page(
    company: Company, location: Location | None = None, start: int = 0
) -> requests.Response:
    """Requests a page of available jobs for a company"""
    company_qs = urlparse(company.jobs_url).query
    query_string = dict(parse_qs(company_qs))  # type: ignore
    params = {
        "f_C": query_string.get("f_C"),
        "f_CR": location.value if location else None,
        "geoId": query_string.get("geoId"),
        "trk": "public_jobs_jobs-search-bar_search-submit",
        "start": start,
    }
    headers = {"User-Agent": user_agent.random}
    return requests.get(
        url=JOB_LIST_PAGE,
        headers=headers,
        timeout=TIMEOUT_LIMIT_SECONDS,
        params=params,
        verify=False,
    )


def _collect_job_detail_page(job_id: str | int) -> requests.Response:
    headers = {"User-Agent": user_agent.random}
    return requests.get(
        url=f"{JOB_DETAIL_PAGE}/{job_id}",
        headers=headers,
        timeout=TIMEOUT_LIMIT_SECONDS,
        allow_redirects=False,
        verify=False,
    )


def _remove_html_tags_and_newlines(text: str) -> str:
    """Remove HTML tags and newlines from a string"""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove \n symbols
    text = re.sub(r"\n", "", text)
    # Remove multiple spaces
    text = re.sub(r"\s+", "", text)
    return text


def _collect_jobs_for_company(
    company: Company, location: Location | None
) -> Generator[requests.Response, None, None]:
    n_jobs = 0

    while True:
        prev = n_jobs
        resp = _get_job_list_page(company, location, n_jobs)

        is_resp_empty = len(_remove_html_tags_and_newlines(resp.text)) == 0
        if is_resp_empty:
            logging.info("No more jobs for %s", company.name)
            break

        if resp.status_code != HTTPStatus.OK:
            if n_jobs >= MAX_JOBS:
                # Linkedin redirects to https://www.linkedin.com/authwall
                # when the number of requests is too high
                logging.info("Reached max number of requests for %s", company.name)
                break

            # Waiting for security check
            # Retrying after 2 seconds
            logging.warning("Waiting ...")
            time.sleep(2)
            resp = _get_job_list_page(company, location, n_jobs)

        if resp.status_code == HTTPStatus.OK:
            yield resp

            n_jobs += JOBS_PER_PAGE
        logging.info("%s: Collected jobs %s to %s", company.name, prev, n_jobs)


def _parse_jobpost_list(card: Tag) -> JobPost:
    """Parse a job post into a JobPost object"""

    def find_text(elem: Tag, class_name: str) -> str | None:
        element = elem.find(class_=class_name)
        return element.text.strip() if element else None

    job_id = int(re.findall(r"\d+", card["data-entity-urn"])[0])  # type: ignore
    title = find_text(card, "base-search-card__title")
    location = find_text(card, "job-search-card__location")
    salary = find_text(card, "job-search-card__salary-ifo")
    company_name = find_text(card, "base-search-card__subtitle") or Company.name

    posted_at = card.find("time", {"datetime": True})
    if posted_at and isinstance(posted_at, Tag):
        posted_at = datetime.strptime(posted_at.attrs["datetime"], "%Y-%m-%d")

    return JobPost(
        linkedin_id=job_id,
        title=title,
        location=location,
        salary=salary,
        company=company_name,
        posted_at=posted_at,
    )


def _saves_jobs_from_response(
    response: requests.Response, language: str | None = None
) -> None:
    """Parse the job list response and save the jobs to the database

    Args:
        response (requests.Response): A HTTP response with the job list page
        language (str): The assumed language of the job posts, to be saved in
            the database
    """
    soup = BeautifulSoup(response.content, "html.parser")
    for card in soup.find_all(attrs={"class": "job-search-card"}):
        job = _parse_jobpost_list(card)
        job.lang = language
        job.save()


def _update_job_description(job: JobPost, response: requests.Response) -> None:
    """Scrape job description for a job post and update the model.

    The session is not committed, so the caller must commit the session.

    Args:
        job (JobPost): _description_
        response (requests.Response): _description_
    """
    soup = BeautifulSoup(response.content, "html.parser")

    description = soup.find(attrs={"class": "show-more-less-html__markup"})
    if description:
        job.description = description.get_text(separator="\n", strip=True)


def scrape_company_jobs(
    company: Company, location: Location | None, language: str | None
) -> None:
    """Scrape jobs for a company"""
    logging.info("Scraping jobs for %s", company.name)
    for response in _collect_jobs_for_company(company, location):
        _saves_jobs_from_response(response, language)
    logging.info("All done! 🥳")


def scrape_job_description(job: JobPost) -> None:
    """Scrape job description for a job post.

    Args:
        job (JobPost): A saved job post

    Raises:
        JobPostNotFoundError: If the job post is not found
    """
    response = _collect_job_detail_page(job.linkedin_id)
    if response.status_code == HTTPStatus.OK:
        _update_job_description(job, response)
    elif response.status_code in [HTTPStatus.MOVED_PERMANENTLY]:
        raise JobPostNotFoundError(f"Job post with id '{job.linkedin_id}' not found")
