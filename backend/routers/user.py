import uuid
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi import Response, Request, HTTPException

from ..db import get_db
from ..services.user import UserService
from ..dto.user import UserResponse, UserRequest, UserCredentials, LoginResponse

router = APIRouter(prefix="/users")

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

def get_user_service(db: Annotated[Session, Depends(get_db)]) -> UserService:
    """
    Since `UserService` holds a `db` session, and sessions are request-scoped, not application scoped,
    `UserService` object can't be defined globally (outside the scope of all router functions) like this:
    ```python
    service = UserService(get_db())

    @router.get("/")
    ...
    ```
    
    The service object itself is reusable, but the DB connection it talks through is not. That's why FastAPI
    needs to be handled duty of managing life cycle of db connection in order to avoid:
    1. Stale session state
    2. No transcation isolation
    3. Connection leak
    4. Thread related errors - SQLAlchemy sessions are not thread safe

    The service and repository objects are cheap to create - what matters is that the `db` session inside them
    is fresh per request.
    """
    return UserService(db)

@router.get("/")
async def get_users(service: Annotated[UserService, Depends(get_user_service)]) -> list[UserResponse]:
    return service.get_users()

@router.post("/create")
async def create_user(user: UserRequest, service: Annotated[UserService, Depends(get_user_service)]) -> UserResponse:
    return await service.create_user(user)

# @router.delete("/delete/{id}")
# async def delete_user(id: UUID, service: Annotated[UserService, Depends(get_user_service)]) -> None:
#     return service.delete_user(id)

@router.get("/confirm/{uuid}")
async def confirm_email(uuid: uuid.UUID, service: Annotated[UserService, Depends(get_user_service)]) -> str:
    return service.confirm_mail(uuid)

@router.get("/login")
async def login(user_credentials: UserCredentials, service: Annotated[UserService, Depends(get_user_service)]) -> JSONResponse:
    service_login_response = service.login(user_credentials)
    response = JSONResponse(
        content={"message": service_login_response.message, "user_uuid": service_login_response.user_uuid_str}
    )
    response.set_cookie(
        key="sid",
        value=service_login_response.session_uuid_str,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )
    return response 