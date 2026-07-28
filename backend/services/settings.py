from __future__ import annotations

from sqlalchemy.orm import Session

from backend.dto.user import UserResponse, UserUpdate

from ..repositories.settings import SettingsRepository
from .user import UserService


class SettingsService:
    def __init__(self, db: Session):
        self.repository = SettingsRepository(db)
        self.user_service = UserService(db)

    def get_user(self, user_id: str) -> UserResponse | None:
        return self.user_service.get_user(user_id)

    def update_profile(self, user_id: str, updated_info: UserUpdate) -> UserUpdate:
        # all_values = vars(updated_info)
        # updated_values = {k: v for k,v in all_values.items() if v}
        return self.user_service.update_user(user_id, updated_info)
 