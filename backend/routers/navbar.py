
from typing import Annotated

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.consts import ElementPatchMode
from datastar_py.fastapi import DatastarResponse
from datastar_py.sanic import datastar_response
from fastapi import APIRouter, Depends, HTTPException, Request

from ..routers.user import get_user_service
from ..services.user import UserService
from ..shared import SESSION_USER_UUID_STR, templates
from .authentication import is_authenticated

protected_router = APIRouter(prefix="/navbar", dependencies=[Depends(is_authenticated)])

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


def extract_user_id_from_cookie(request: Request) -> str:
    return request.cookies.get(SESSION_USER_UUID_STR, "")

@datastar_response
@protected_router.get("/", response_class=DatastarResponse, response_model=None)
async def get_navbar(request: Request, user_service: Annotated[UserService, Depends(get_user_service)]):
    user_id = extract_user_id_from_cookie(request)
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authorized")
    print(f"[NAVBAR_ROUTER]: fetching user: {user=}")

    yield SSE.patch_signals(
        {
            "username": user.username,
            "avatarImgSrc": user.avatar_img_src,
            "notifCount": len(notifications),
            "email": user.email
        }
    )

@datastar_response
@protected_router.get("/notifications", response_class=DatastarResponse, response_model=None)
async def render_notifications(request: Request):
    html = templates.get_template("components/home/notifications/notifications.html").render({"notifications": notifications, "request": request})
    yield SSE.patch_elements(html, selector="#notification-panel", mode=ElementPatchMode.OUTER)
    yield SSE.patch_signals({"notifCount": len(notifications)})
