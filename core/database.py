from sqlalchemy_utils import database_exists, create_database
from sqlmodel import create_engine, SQLModel, Session
from .config import settings
from core.logger import get_logger
import logging

engine = create_engine(settings.DATABASE_URL, echo=False)

sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
sqlalchemy_logger.setLevel(logging.INFO)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    if not database_exists(engine.url):
        create_database(engine.url)
    SQLModel.metadata.create_all(engine)