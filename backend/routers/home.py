from typing import Annotated

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.consts import ElementPatchMode
from datastar_py.fastapi import DatastarResponse
from datastar_py.sanic import datastar_response
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from ..routers.user import get_user_service
from ..services.user import UserService
from ..shared import SESSION_USER_UUID_STR, templates
from .authentication import is_authenticated

router = APIRouter(
    prefix="",
    dependencies=[Depends(is_authenticated)]
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

@datastar_response
@router.get("/notifications", response_class=DatastarResponse, response_model=None)
def get_notifications(request: Request):
    print("USER REQUESTED NOTIFICATIONS")
    notifications = [
        {
            "title": "Training Reminder",
            "message": "Your strength training session starts today at 4:00 PM.",
            "created_at": "2 minutes ago",
            "type": "unread"
        },
        {
            "title": "New Instruction Assigned",
            "message": "A new workout plan has been assigned to you. Check the details before starting.",
            "created_at": "8 minutes ago",
            "type": "unread"
        },
        {
            "title": "Goal Completed",
            "message": "Congratulations! You completed your weekly training goal.",
            "created_at": "25 minutes ago",
            "type": "success"
        },
        {
            "title": "Schedule Updated",
            "message": "Your Monday training session has been moved to Wednesday at 6:30 PM.",
            "created_at": "1 hour ago",
            "type": "unread"
        },
        {
            "title": "Missed Training",
            "message": "You missed your planned workout yesterday. Would you like to reschedule it?",
            "created_at": "3 hours ago",
            "type": "danger"
        },
        {
            "title": "Long Message Test",
            "message": "This is an extremely long notification message designed to test how text wrapping behaves inside the notification side panel when there is a lot of content.",
            "created_at": "Yesterday",
            "type": "unread"
        },
        {
            "title": "Training Streak",
            "message": "Amazing work! You have maintained your training streak for 14 days.",
            "created_at": "1 week ago",
            "type": "success"
        }
    ]

    html = templates.get_template("components/home/notifications/notifications.html").render({"notifications": notifications, "request": request})
    yield SSE.patch_elements(html, selector="#notification-panel", mode=ElementPatchMode.OUTER)
    yield SSE.patch_signals({"notifCount": len(notifications)})