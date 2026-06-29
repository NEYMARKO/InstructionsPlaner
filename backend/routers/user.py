from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from uuid import UUID

from ..dto.user import UserResponse, UserRequest
from ..services.user import UserService
from ..db import get_db

router = APIRouter(prefix="/users")

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
    return service.create_user(user)

# @router.delete("/delete/{id}")
# async def delete_user(id: UUID, service: Annotated[UserService, Depends(get_user_service)]) -> None:
#     return service.delete_user(id)

@router.get("/confirm/{uuid}")
async def confirm_email(uuid: UUID, service: Annotated[UserService, Depends(get_user_service)]) -> UUID:
    # return service.validate_email(uuid)
    return uuid