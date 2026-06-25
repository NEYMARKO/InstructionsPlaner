import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(str(Path(__file__).parent / ".env"))

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host_name = os.getenv("DB_HOST_NAME")
port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

db_url = f"postgresql+psycopg2://{user}:{password}@{host_name}:{port}/{db_name}"
engine = create_engine(db_url, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
