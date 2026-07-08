from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles

from backend.routers.home import router as home_router
from backend.routers.user import router as user_router, protected_router as protected_user_router # has to be relative to the root - root is workspace folder (where you ar positioned in terminal)
from backend.routers.authentication import router as auth_router, protected_router as protected_auth_router
from .models import Base
from .db import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield # everything before yield will be executed before the application starts, everything after it
          # will be executed after application has finished

app = FastAPI(lifespan=lifespan) # this gets triggered every time application is started or when code changes are saved
app.include_router(home_router)
app.include_router(user_router)
app.include_router(protected_user_router)
app.include_router(auth_router)
app.include_router(protected_auth_router)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")