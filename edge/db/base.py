from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from edge.config.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, echo=False)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)