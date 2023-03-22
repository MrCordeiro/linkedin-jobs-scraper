"""Database configuration."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from job_scraper.models import Base
from job_scraper.settings import SQLITE_DATABASE_URL

engine = create_engine(SQLITE_DATABASE_URL)


Base.metadata.create_all(engine)


Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
