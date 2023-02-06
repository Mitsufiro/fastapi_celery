import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.util.compat import contextmanager
from dotenv import load_dotenv

load_dotenv('.env')

engine = create_engine(url=os.environ['DATABASE_URL'])
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


db_context = contextmanager(get_db_session)
