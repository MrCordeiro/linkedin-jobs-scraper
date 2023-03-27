"""Dataclass for company data"""
import json
from dataclasses import asdict, dataclass, field
from urllib.parse import parse_qs, urlencode, urlparse

from slugify import slugify

from job_scraper.scrapers.selenium import scrape_jobs_url
from job_scraper.settings import COMPANY_PAGE, PROJECT_DIR

COMPANIES_DIR = PROJECT_DIR / "data" / "companies"


def _filter_url_params(url: str, params: list[str]) -> str:
    """Excludes query parameters from a URL that are not in the list of params"""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    valid_params = {k: v for k, v in query_params.items() if k in params}
    new_query_string = urlencode(valid_params, doseq=True)
    new_url = parsed_url._replace(query=new_query_string).geturl()
    return new_url


@dataclass
class Company:
    """Company data refering to a LinkedIn company page"""

    name: str
    slug: str | None = None
    jobs_url: str | None = field(default=None, repr=False)

    def __post_init__(self):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.jobs_url:
            self.jobs_url = self._get_jobs_url()

    @property
    def url(self):
        """Returns the URL of the company page"""
        return f"{COMPANY_PAGE}/{self.slug}"

    @property
    def is_valid(self) -> bool:
        """Company is valid if it has a jobs URL"""
        return bool(self.jobs_url)

    def _get_jobs_url(self) -> str | None:
        """Fetch the URL for the jobs page of a company"""
        _valid_params = ["f_C", "geoId"]
        jobs_url = scrape_jobs_url(f"{self.url}/jobs")
        if jobs_url:
            jobs_url = _filter_url_params(jobs_url, _valid_params)
        return jobs_url

    def delete(self) -> None:
        """Deletes the company data file"""
        fp = COMPANIES_DIR / f"{self.slug}.json"
        if fp.exists():
            fp.unlink()

    def validate(self) -> bool:
        """Checks if the company data is valid and deletes it if not"""
        if not self.is_valid:
            self.delete()
            return False
        return True

    def save(self) -> None:
        """Stores the company data as a JSON file"""
        fp = COMPANIES_DIR / f"{self.slug}.json"
        if not fp.parent.exists():
            fp.parent.mkdir(parents=True)
        with open(COMPANIES_DIR / f"{self.slug}.json", "w", encoding="utf-8") as file:
            json.dump(asdict(self), file, indent=4)


def get_available_companies() -> list[Company]:
    """Reads company data from the COMPANIES_DIR directory"""
    existing_companies = COMPANIES_DIR.glob("*.json")
    companies = []
    for company_file in existing_companies:
        with open(company_file, encoding="utf-8") as file:
            company_dict = json.load(file)
        company = Company(**company_dict)
        companies.append(company)
    return companies


def get_company(name: str) -> tuple[Company, bool]:
    """
    Loads a company from the COMPANIES_DIR directory or creates a new one if it
    doesn't exist
    """
    file_path = COMPANIES_DIR / f"{slugify(name)}.json"
    try:
        with open(file_path, encoding="utf-8") as file:
            company_dict = json.load(file)
    except FileNotFoundError:
        company = Company(name)
        company.save()
        return company, True
    return Company(**company_dict), False
