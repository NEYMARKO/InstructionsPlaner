from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.shared import SESSION_USER_UUID_STR

from ..services.user import UserService
from ..shared import SESSION_USER_UUID_STR, templates
from .authentication import is_authenticated
from .user import get_user_service


class MissingUserException(HTTPException):
    pass

class WrongUserTypeException(HTTPException):
    pass

def get_user_service(db: Annotated[Session, Depends(get_db)]) -> UserService:
    return UserService(db)

def is_trainer(request: Request , service: Annotated[UserService, Depends(get_user_service)]):
    logged_user = service.get_user(request.cookies.get(SESSION_USER_UUID_STR, ""))
    if logged_user is None:
        raise MissingUserException(status_code=403, detail="Must be logged in to view resource")
    if logged_user.is_student:
        raise WrongUserTypeException(status_code=403, detail="Must be trainer to access this resource")

router = APIRouter(
    prefix="/training",
    dependencies=[Depends(is_authenticated)]
)

protected_router = APIRouter(
    prefix="/training",
    dependencies=[Depends(is_trainer)]
)

@router.get("/", response_class=HTMLResponse)
def get_home(request: Request, user_service: Annotated[UserService, Depends(get_user_service)]):
    user_id = request.cookies.get(SESSION_USER_UUID_STR, "")
    print(f"{user_id=}")

    user_obj = user_service.get_user(user_id)

    instructions = [
        {
            "status": "confirmed",
            "title": "Mathematics",
            "instructor": "John Smith",
            "date": "11/07/2027",
            "time": "10:00-11:30"
        },
        {
            "status": "pending",
            "title": "Physics",
            "instructor": "Emily Jhonson",
            "date": "01/01/2027",
            "time": "18:00-19:15"
        },
        {
            "status": "confirmed",
            "title": "Cardio",
            "instructor": "Pršo",
            "date": "10/05/2027",
            "time": "13:00 - 15:00"
        }
    ]
    print(f"[HOME_PAGE]: {user_obj=}")
    return templates.TemplateResponse(
        request=request, name="pages/home/home.html", 
        context={"instructions": instructions, "avatar_img_src": getattr(user_obj, "avatar_img_src", "")}
    )

# @datastar_response
@protected_router.get("/create")
def get_notifications(request: Request):
    return templates.TemplateResponse(
        request=request, name="pages/training/create_training.html")

    # html = templates.get_template("components/home/notifications/notifications.html").render({"notifications": notifications, "request": request})
    # yield SSE.patch_elements(html, selector="#notification-panel", mode=ElementPatchMode.OUTER)