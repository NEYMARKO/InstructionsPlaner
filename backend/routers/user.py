from typing import Annotated

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.fastapi import DatastarResponse
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..services.user import (
    UserService,
)
from ..shared import SESSION_USER_UUID_STR
from .authentication import is_authenticated

router = APIRouter(prefix="/user")

protected_router = APIRouter(prefix="/user", dependencies=[Depends(is_authenticated)])

# this needs to be dependency because it is using db Session, which is getting destroyed after endpoint has ran
# => if UserService object didn't also get destroyed, it would hold reference to stale/destroyed Session object
# (repository would actually store that stale value, but service stores repository reference, which stores Session reference)
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

# @router.get("/")
# async def get_users(service: Annotated[UserService, Depends(get_user_service)]) -> list[UserResponse]:
#     return service.get_users()

@router.get("/")
async def get_user(request: Request, service: Annotated[UserService, Depends(get_user_service)]) -> DatastarResponse:
    print("HERE")
    user_info = service.get_user(request.cookies.get(SESSION_USER_UUID_STR, ""))
    if not user_info:
        return DatastarResponse()
    return DatastarResponse(
        SSE.patch_signals({"name": user_info.username, "email": user_info.email})
    )

# @protected_router.get("/profile")
# async def get_profile(request: Request, service: Annotated[UserService, Depends(get_user_service)]):
#     return templates.TemplateResponse(request=request, name="profile/profile.html")

# @protected_router.patch("/profile")
# async def update_profile(request: Request, user_changes: UserUpdate, service: Annotated[UserService, Depends(get_user_service)]):
#     service.update_user(request.cookies.get(SESSION_USER_UUID_STR, ""), user_changes)
#     return
