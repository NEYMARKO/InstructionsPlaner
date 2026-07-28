from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request, HTTPException
from datastar_py.fastapi import DatastarResponse
from datastar_py import ServerSentEventGenerator as SSE

from ..db import get_db
from ..shared import templates
from .authentication import is_authenticated 

protected_router = APIRouter(prefix="/settings", dependencies=[Depends(is_authenticated)])

@protected_router.get("/profile")
async def get_profile(request: Request):
    return templates.TemplateResponse(request=request, name="profile/profile.html")

@protected_router.get("/account")
async def update_profile(request: Request):
    return templates.TemplateResponse(request=request, name="profile/account.html")
