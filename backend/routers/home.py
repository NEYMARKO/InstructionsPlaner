from typing import Annotated

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.consts import ElementPatchMode
from datastar_py.fastapi import DatastarResponse
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from ..services.authentication import AuthService
from ..shared import SESSION_USER_UUID_STR, templates
from .authentication import get_service, is_authenticated

router = APIRouter(prefix="")


@router.get("/", response_class=HTMLResponse)
def get_home(request: Request, auth_service: Annotated[AuthService, Depends(get_service)]):
    authenticated = False
    user_id = request.cookies.get(SESSION_USER_UUID_STR, "")
    print(f"{user_id=}")

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
    try:
        authenticated = is_authenticated(request=request, service=auth_service)
    except HTTPException:
        pass
    return templates.TemplateResponse(
        request=request, name="home/home.html", context={"instructions": instructions}
    )
@router.get("/notifications", response_class=DatastarResponse)
def get_notifications(request: Request):
    print("USER REQUESTED NOTIFICATIONS")
    notifications = [
        {
            "message": "Don't forget to eat your vegetables" 
        },
        {
            "message": "Training starting at 4 o'clock"
        },
        {
            "message": "I'm in love with a cocoa"
        },
        {
            "message": "Can't stop lifting"
        }
    ]
    html = templates.get_template("home/notifications.html").render({"notifications": notifications, "request": request})
    # return templates.TemplateResponse(
    #     request=request, name="home/home.html", context={"notifications": notifications}
    # )
    print(f"{html=}")
    return DatastarResponse(
        # SSE.patch_elements(html, selector="#notification-panel", mode=ElementPatchMode.OUTER)
        SSE.patch_elements(html, selector="#notification-panel", mode="outer")
    )