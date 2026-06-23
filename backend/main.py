from fastapi import FastAPI
from backend.routers.user import router as users_router # has to be relative to the root - root is workspace folder (where you ar eositioned in terminal)

app = FastAPI()
app.include_router(users_router)