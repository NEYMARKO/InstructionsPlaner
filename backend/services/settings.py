from __future__ import annotations

import random

from sqlalchemy.orm import Session

from backend.dto.user import UserResponse, UserUpdate

from ..repositories.settings import SettingsRepository
from .user import UserService


class AmbiguousUserTypeException(Exception):
    pass

class SettingsService:
    def __init__(self, db: Session):
        self.repository = SettingsRepository(db)
        self.user_service = UserService(db)

    def get_user(self, user_id: str) -> UserResponse | None:
        return self.user_service.get_user(user_id)

    def update_profile(self, user_id: str, updated_info: dict[str, str]) -> None:
        """
        Updates all info about user except `is_student` value, as that is the only 
        value that shouldn't get changed once user has been created. It is instead extracted
        from database.

        In case that user is using defualt avatar, it will also get updated to match `display_name` initials 
        """

        user_obj = self.user_service.get_user(user_id)
        is_user_student = self.user_service.is_user_student(user_obj=user_obj)
        if is_user_student is None:
            raise AmbiguousUserTypeException("Can't determine whether user is student or trainer")
            
        updated_info_obj = UserUpdate.model_validate(updated_info)
        updated_info_obj.is_student = is_user_student

        if updated_info_obj.display_name != getattr(user_obj, "display_name")\
            and self.user_service.has_default_avatar(user_obj=user_obj):
            background = f"{random.randrange(0x444444):06x}"
            updated_info_obj.avatar_img_src = (
                f"https://ui-avatars.com/api/?name={updated_info_obj.display_name.replace(' ', '+')}"
                f"&background={background}"
                "&color=f0f6fc&size=80"
            )
        print(f"{updated_info_obj=}")
        self.user_service.update_user(user_id, updated_info_obj)
 