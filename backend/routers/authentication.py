from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from ..db import get_db
from ..services.authentication import AuthService
from ..dto.authentication import UserCredentials, LoginResponse
from ..shared import SESSION_TOKEN_STR, SESSION_USER_UUID_STR

router = APIRouter(prefix="/auth")

def is_authenticated(request: Request, db: Annotated[Session, Depends(get_db)]) -> bool:
    """
    Checks whether user is authenticated by getting user's `session_id` stored in cookie.
    It then retrives session information for that id from the database and checks whether it has expired.
    In case session is no longer valid, exception with status `401` is thrown - user will have to log in again.
    """
    session_id = request.cookies.get("sid")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return True

def get_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(db)

@router.post("/login")
async def login(credentials: UserCredentials, service: Annotated[AuthService, Depends(get_service)]) -> None:
    service_response: LoginResponse = service.login(credentials)
    response = JSONResponse(
        content={"message": service_response.message}
    )
    response.set_cookie(
        key=SESSION_TOKEN_STR,
        value=service_response.token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )

    response.set_cookie(
        key=SESSION_USER_UUID_STR,
        value=service_response.user_uuid_str,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )
    return
