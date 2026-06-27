import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv(str(Path(__file__).parent / ".env"))

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host_name = os.getenv("DB_HOST_NAME")
port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

db_url = f"postgresql+psycopg2://{user}:{password}@{host_name}:{port}/{db_name}"
engine = create_engine(db_url, echo=True)

SessionLocal: sessionmaker[Session] = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Creates generator function which works in a specific way when used with FastAPI as dependency.

    When a function contains `yield`, calling it doesn't execute the body - it returns a generator object.
    The caller controls when the execution proceeds:

    execution enters => runs until yield => PAUSES => caller uses yielded value => execution resumes => `finally`
    runs (db.close() gets triggered)

    `get_db()` has 2 phases:
    1. Before `yield` - creates the session and hands it to the caller
    2. After `yield` - the `finally` block closes the session

    When is `finally` reached?
    
    => It runs when the caller explicitly advances the generator past the yield point. In FastAPI, the dependency 
    injection system does this automatically.

    A new session is created per request => it is not "alive through the whole app duration"

    What happens under the hood:
    - Request arrives => `get_db` generatior is created, `SessionLocal` is called
    - Handler runs => `db` session is active and usable
    - Handler returns => generator resumes, `finally` closes the session
    - Next request => A brand new generator and session are created
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
