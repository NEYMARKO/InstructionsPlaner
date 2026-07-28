import asyncio
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.routers.authentication import NotAuthenticatedException
from backend.routers.authentication import protected_router as protected_auth_router
from backend.routers.authentication import router as auth_router
from backend.routers.counter import router as counter_router
from backend.routers.event_system import router as event_system_router
from backend.routers.home import router as home_router
from backend.routers.settings import protected_router as settings_router
from backend.routers.user import protected_router as protected_user_router
from backend.routers.user import (  # has to be relative to the root - root is workspace folder (where you ar positioned in terminal)
    router as user_router,
)

from .db import engine
from .models import Base
from .notifications import event_system as ES


@asynccontextmanager
async def lifespan(app: FastAPI):
    original_sigint = signal.getsignal(signal.SIGINT)
    original_sigterm = signal.getsignal(signal.SIGTERM)

    def handle_signal(signum, frame): # this will only ever be used in developer mode - server won't get restarted on keypress in reallife situation
        print(f"[shutdown] received signal {signum} at {asyncio.get_event_loop().time()}")
        # chain to uvicorn's original handler so its own shutdown sequence still runs
        ES.shutdown_streams()
        if signum == signal.SIGINT and callable(original_sigint):
            original_sigint(signum, frame)
        elif signum == signal.SIGTERM and callable(original_sigterm):
            original_sigterm(signum, frame)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield # everything before yield will be executed before the application starts, everything after it
          # will be executed after application has finished

app = FastAPI(lifespan=lifespan) # this gets triggered every time application is started or when code changes are saved

@app.exception_handler(NotAuthenticatedException)
async def not_authenticated_handler(request: Request, exc: NotAuthenticatedException):
    return RedirectResponse(url="/auth/login", status_code=303)

app.include_router(home_router)
app.include_router(user_router)
app.include_router(protected_user_router)
app.include_router(auth_router)
app.include_router(protected_auth_router)
app.include_router(event_system_router)
app.include_router(settings_router)

app.include_router(counter_router)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")