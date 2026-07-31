
from typing import Annotated

from datastar_py.fastapi import DatastarResponse, read_signals
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..services.settings import SettingsService
from ..shared import SESSION_USER_UUID_STR, templates
from .authentication import is_authenticated

protected_router = APIRouter(prefix="/settings", dependencies=[Depends(is_authenticated)])

def get_service(db: Annotated[Session, Depends(get_db)]) -> SettingsService:
    return SettingsService(db)

def extract_user_id_from_cookie(request: Request) -> str:
    return request.cookies.get(SESSION_USER_UUID_STR, "")

@protected_router.get("/profile")
async def get_profile(request: Request, service: Annotated[SettingsService, Depends(get_service)]):
    user_id = extract_user_id_from_cookie(request)
    user = service.get_user(user_id)
    if not user:
        return 
    print(f"[PROFILE]: fetching user: {user=}")
    return templates.TemplateResponse(
        request=request, 
        name="pages/settings/profile.html", 
        context={
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "country": user.country,
            "city": user.city,
            "avatar_img_src": user.avatar_img_src
        }
    )

@protected_router.get("/account")
async def get_account(request: Request):
    return templates.TemplateResponse(request=request, name="pages/settings/account.html")

@protected_router.get("/appearance")
async def get_appearance(request: Request):
    return templates.TemplateResponse(request=request, name="pages/settings/appearance.html")

@protected_router.get("/accessibility")
async def get_accessibilityy(request: Request):
    return templates.TemplateResponse(request=request, name="pages/settings/accessibility.html")


@protected_router.get("/notifications")
async def get_notifications(request: Request):
    return templates.TemplateResponse(request=request, name="pages/settings/notifications.html")

@protected_router.patch("/profile")
async def update_profile(request: Request, service: Annotated[SettingsService, Depends(get_service)]) -> DatastarResponse:
    """
    Using read_signals instead of some DTO object because signals aren't organized inside of some form,
    but are spread accross page elements, which means that 422 error will get triggered, and payload will be {}
    whenever patch request gets called. If user_info: UserUpdate was left in function definition, this error would
    occur because request couldn't match all fields to member variables inside of UserUpdate class (it actually couldn't 
    match single member variable because patch method call is added to regular button, which isn't part of the form => data
    isn't collected in any way => signals need to be used because they are global)
    """
    print(f"PROFILE PATCH")
    signals: dict[str, str] = await read_signals(request)
    print(f"{signals=}")
    user_id = extract_user_id_from_cookie(request)
    service.update_profile(user_id, signals)
    return DatastarResponse()