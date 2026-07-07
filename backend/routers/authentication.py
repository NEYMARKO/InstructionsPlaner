from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException

from ..db import get_db
from ..services.authentication import AuthService
from ..dto.authentication import UserCredentials, LoginResponse
from ..shared import SESSION_TOKEN_STR, SESSION_USER_UUID_STR

router = APIRouter(prefix="/auth")

def get_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(db)

def is_authenticated(request: Request, service: Annotated[AuthService, Depends(get_service)]) -> bool:
    """
    Checks whether user is authenticated by getting user's `session_id` stored in cookie.
    It then retrives session information for that id from the database and checks whether it has expired.
    In case session is no longer valid, exception with status `401` is thrown - user will have to log in again.
    """
    token = request.cookies.get(SESSION_TOKEN_STR)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not service.token_valid(request=request):
        raise HTTPException(status_code=401, detail="Session expired")
    return True

@router.post("/login")
async def login(credentials: UserCredentials, service: Annotated[AuthService, Depends(get_service)]) -> JSONResponse:
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
    return response

@router.post("/logout")
async def logout(request: Request, service: Annotated[AuthService, Depends(get_service)]) -> JSONResponse:
    user_uuid = request.cookies.get(SESSION_USER_UUID_STR, "")
    service.logout(user_uuid)
    
    response = JSONResponse(
        content={"message": "Successfully logged out"}
    )
    response.delete_cookie(SESSION_TOKEN_STR) 
    response.delete_cookie(SESSION_USER_UUID_STR) # cookies are not tied to the `Response`` object (you don't need to pass reference)
                                                  # we receive from FastAPI. They're tied to browser (or Postman) and the browser updates
                                                  # them based on Set-Cookie headers in response => imagine it as sending a signal through
                                                  # the browser that will invalidate cookies with SESSION_TOKEN_STR and SESSION_USER_UUID_STR
                                                  # keys => delete_cookie sends signal in the browser which makes browser invalidate them - sets their
                                                  # expiration day to 01.01.1970
    return response