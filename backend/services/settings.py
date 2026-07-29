from __future__ import annotations

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
        from database 
        """
        is_user_student = self.user_service.is_user_student(user_id)
        if is_user_student is None:
            raise AmbiguousUserTypeException("Can't determine whether user is student or trainer")
        updated_info_obj = UserUpdate.model_validate(updated_info)
        updated_info_obj.is_student = is_user_student
        self.user_service.update_user(user_id, updated_info_obj)
 