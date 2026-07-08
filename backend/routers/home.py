from typing import Annotated
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, Request, HTTPException

from ..services.authentication import AuthService
from ..shared import SESSION_USER_UUID_STR, templates
from .authentication import is_authenticated, get_service

router = APIRouter(prefix="")


@router.get("/", response_class=HTMLResponse)
def get_home(request: Request, auth_service: Annotated[AuthService, Depends(get_service)]):
    authenticated = False
    user_id = request.cookies.get(SESSION_USER_UUID_STR, "")
    print(f"{user_id=}")
    try:
        authenticated = is_authenticated(request=request, service=auth_service)
    except HTTPException:
        pass
    return templates.TemplateResponse(
        request=request, name="index/index.html", context={"user_id": user_id, "authenticated": authenticated}
    )