"""Entry point for the job scraper application."""
# pylint: disable=not-callable
import logging

import click
from sqlalchemy import func, select

from job_scraper.companies import get_company
from job_scraper.database import LocalSession
from job_scraper.locations import Location
from job_scraper.models import JobPost
from job_scraper.scrapers.bs4 import (
    JobPostNotFoundError,
    scrape_company_jobs,
    scrape_job_description,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def scrape_job_descriptions() -> None:
    """Scrape job descriptions for jobs that don't have them yet."""
    with LocalSession() as session:
        jobs_to_search = select(JobPost).filter_by(description=None)

        count_query = select(func.count()).select_from(jobs_to_search.alias())
        n_jobs = session.scalar(count_query)

        if n_jobs == 0:
            logging.info("No job descriptions to scrape")
            return

        for count, job in enumerate(session.scalars(jobs_to_search)):
            logging.info(
                "Scraping job description for %s (%d/%d)", job.title, count, n_jobs
            )
            try:
                scrape_job_description(job)
            except JobPostNotFoundError:
                # The job is no longer active. The description information will
                # continue to be available in the SPA. However, for the server-
                # side page, we are redirected to another page, that doesn't
                # have the job description anymore. We might as well delete it
                # for now.
                session.delete(job)
            session.commit()


@click.command()
@click.option(
    "-c",
    "--company",
    "company_name",
    help="Scrape jobs from a specific company",
    prompt=True,
)
@click.option(
    "-l",
    "--location",
    help=(
        "Scrape jobs from a specific country. Use the ISO 3166-1 alpha-2 code (e.g. "
        "'US', 'GB', 'FR', etc.)"
    ),
    type=click.Choice(Location.as_list()),
)
@click.option(
    "--set-lang",
    "-sl",
    "language",
    help="Set the language for the job posts if you know it",
)
def main(company_name: str, location: str | None, language: str | None):
    """Main entry point of the application."""

    # Input validation
    company, _ = get_company(company_name)
    if not company.validate():
        raise click.BadParameter(
            f"Unable to find jobs for this company: {company.name}"
        )
    location = Location[location] if location else None
    language = language.lower() if language else None

    # Collect jobs
    scrape_company_jobs(company, location, language)

    # Update incomplete job descriptions
    scrape_job_descriptions()

    return 0


if __name__ == "__main__":
    main()
