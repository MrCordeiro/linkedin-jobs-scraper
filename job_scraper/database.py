"""Database configuration."""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from job_scraper.settings import SQLITE_DATABASE_URL

engine = create_engine(SQLITE_DATABASE_URL)


Base = declarative_base()


def init_db() -> None:
    """Create the database tables."""
    Base.metadata.create_all(engine)


LocalSession: Session = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)  # type: ignore
