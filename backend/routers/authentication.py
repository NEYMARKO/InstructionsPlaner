from typing import Annotated, Literal
from uuid import UUID

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.fastapi import DatastarResponse
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..dto.authentication import UserCredentials
from ..dto.user import UserRequest
from ..services.authentication import AuthService, InternalServerException
from ..shared import (
    EVENT_SUBSCRIPTION_ID,
    SESSION_TOKEN_STR,
    SESSION_USER_UUID_STR,
    templates,
)

router = APIRouter(prefix="/auth")

class NotAuthenticatedException(Exception):
    pass

def get_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(db)

def is_authenticated(request: Request, service: Annotated[AuthService, Depends(get_service)]):
    """
    Checks whether user is authenticated by getting user's `session_id` stored in cookie.
    It then retrives session information for that id from the database and checks whether it has expired.
    In case session is no longer valid, exception with status `401` is thrown - user will have to log in again.
    """
    token = request.cookies.get(SESSION_TOKEN_STR)
    if not token:
        raise NotAuthenticatedException()
    try:
        user_id: str = request.cookies.get(SESSION_USER_UUID_STR, "")
        token = request.cookies.get(SESSION_TOKEN_STR, "")
        if not service.token_valid(user_id=user_id, token=token):
            print("COULDN'T LOCATE TOKEN FOR USER")
            raise NotAuthenticatedException()
    except InternalServerException:
        raise NotAuthenticatedException
    return True

def construct_cookie_response(
        response: DatastarResponse | None,
        key: str, value: str, is_secure: bool = True, 
        http_only: bool = True, samesite: Literal['lax', 'strict', 'none'] | None = 'lax', max_age: int = 3600
    ) -> DatastarResponse:

    print(f"Constructing cookie for key: {key}")
    if not response:
        response = DatastarResponse()
    response.set_cookie(
        key=key,
        value=value,
        httponly=http_only,
        secure=is_secure,
        samesite=samesite,
        max_age=max_age
    )
    return response

protected_router = APIRouter(prefix="/auth", dependencies=[Depends(is_authenticated)])

@router.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse(
        request=request, name="pages/login/login.html"
    )

@router.post("/login")
async def login(request: Request, credentials: UserCredentials, service: Annotated[AuthService, Depends(get_service)]) -> DatastarResponse:
    service_response = None
    event_subscription_id = request.cookies.get(EVENT_SUBSCRIPTION_ID, "")
    print(f"[LOGIN] passed credentials: {credentials}")
    service_response = service.login(event_subscription_id, credentials)
    if not service_response:
        return DatastarResponse() # don't patch anything because that will overwrite original error msg
    response = DatastarResponse(SSE.execute_script("window.location='/'"))
    response = construct_cookie_response(response, SESSION_TOKEN_STR, service_response.token)
    response = construct_cookie_response(response, SESSION_USER_UUID_STR, service_response.user_uuid_str)
    return response

@router.get("/sign-up", response_class=HTMLResponse)
def get_sign_up(request: Request):
    return templates.TemplateResponse(
        request=request, name="pages/registration/register.html"
    )

@router.post("/sign-up", response_model=None)
async def sign_user_up(request: Request, user: UserRequest, service: Annotated[AuthService, Depends(get_service)]) -> DatastarResponse | None:
    event_subscription_id = request.cookies.get(EVENT_SUBSCRIPTION_ID, "")
    print(f"[USER SIGN-UP REQUEST]: {user}")
    service_response = await service.sign_up(event_subscription_id, user)
    if service_response:
        print("SERVICE RESPONSE IS ALRIGHT")
        response = DatastarResponse(SSE.execute_script("window.location='/'"))
        response = construct_cookie_response(response, SESSION_TOKEN_STR, service_response.token)
        response = construct_cookie_response(response, SESSION_USER_UUID_STR, service_response.user_id)
        return response
    print("SERVICE RESPONSE IS NOT TRUTHY")
    return

@router.get("/confirm/{uuid}", response_class=HTMLResponse)
async def confirm_email(uuid: UUID, request: Request, service: Annotated[AuthService, Depends(get_service)]):
    service.confirm_mail(uuid)
    return templates.TemplateResponse(
        request=request, name="pages/registration/confirmation.html"
    )

@protected_router.post("/logout")
async def logout(request: Request, service: Annotated[AuthService, Depends(get_service)]) -> DatastarResponse:
    user_id = request.cookies.get(SESSION_USER_UUID_STR, "")
    token = request.cookies.get(SESSION_TOKEN_STR, "")
    service.logout(user_id=user_id, token=token)
    
    response = DatastarResponse(
        SSE.execute_script("window.location.reload()") # used for refreshing page after logging out to apply the changes
    )
    response.delete_cookie(SESSION_TOKEN_STR) 
    response.delete_cookie(SESSION_USER_UUID_STR) # cookies are not tied to the `Response`` object (you don't need to pass reference)
                                                  # we receive from FastAPI. They're tied to browser (or Postman) and the browser updates
                                                  # them based on Set-Cookie headers in response => imagine it as sending a signal through
                                                  # the browser that will invalidate cookies with SESSION_TOKEN_STR and SESSION_USER_UUID_STR
                                                  # keys => delete_cookie sends signal in the browser which makes browser invalidate them - sets their
                                                  # expiration day to 01.01.1970
    print("LOGGED OUT")

    return response