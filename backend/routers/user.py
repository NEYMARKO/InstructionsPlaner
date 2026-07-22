from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request, HTTPException


from ..db import get_db
from backend.dto.user import UserResponse
from ..shared import SESSION_USER_UUID_STR
from .authentication import is_authenticated 
from ..services.user import UserService, UserNotFoundException, UserIdNotProvidedException

router = APIRouter(prefix="/users")

protected_router = APIRouter(prefix="/users", dependencies=[Depends(is_authenticated)])

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

@router.get("/")
async def get_users(service: Annotated[UserService, Depends(get_user_service)]) -> list[UserResponse]:
    return service.get_users()

@protected_router.get("/profile")
async def get_profile(request: Request, service: Annotated[UserService, Depends(get_user_service)]) -> UserResponse:
    result = None
    user_id = request.cookies.get(SESSION_USER_UUID_STR, "")
    try:
        result = service.get_profile(user_id)
    except UserIdNotProvidedException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result