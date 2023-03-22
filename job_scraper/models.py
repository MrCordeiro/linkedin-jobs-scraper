"""SQLAlchemy models"""
# pylint: disable=not-callable, too-few-public-methods
from datetime import datetime

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import TIMESTAMP


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""


class JobPost(Base):
    """
    A job post from LinkedIn.

    This is the job post information available using BeautifulSoup. Some
    information are only available on the LinkedIn SPA (Single Page
    Application) page for logged-in users (e.g. salary, workplace type, whether
    the post is accepting applicats or not)
    """

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    linkedin_id: Mapped[int] = mapped_column()
    lang: Mapped[str] = mapped_column(String(5), default="en")
    title: Mapped[str] = mapped_column(String(100))
    company: Mapped[str] = mapped_column(String(60))
    location: Mapped[str] = mapped_column(String(60))
    salary: Mapped[str | None] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(Text)
    posted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # By itself, the linkedin_id is not unique, as companies may try to reuse
    # old job postings. However, the combination of linkedin_id and title
    # should be
    __table_args__ = (UniqueConstraint(linkedin_id, title, name="u_lid_title"),)
