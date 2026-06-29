from fastapi import FastAPI

from backend.routers.user import router as users_router # has to be relative to the root - root is workspace folder (where you ar positioned in terminal)
from .models import Base
from .db import engine

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(users_router)