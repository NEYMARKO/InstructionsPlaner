from __future__ import annotations

import re

from sqlalchemy.orm import Session

from backend.dto.user import UserUpdate
from backend.models import UserModel

from ..dto.user import UserBase, UserRequest, UserResponse
from ..repositories.user import UserRepository


class EmptyIDProvidedException(Exception):
    pass

class NoRelevantInfoProvided(Exception):
    pass

class UserIdNotProvidedException(Exception):
    pass

class UserNotFoundException(Exception):
    pass

class UserService:

    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def get_service(self) -> UserService:
        return self
    
    def add_user(self, user: UserRequest) -> UserResponse:
        user_model: UserModel = self.repository.save_user(user) 
        return UserResponse.model_validate(user_model)

    def get_user(self, user_id: str) -> UserResponse | None:
        if not user_id:
            raise EmptyIDProvidedException("User ID has not been provided")
        return self.repository.get_user(user_id)
    
    def get_users(self) -> list[UserResponse]:
        return self.repository.get_users()
    
    def get_profile(self, user_id: str) -> UserResponse:
        if not user_id:
            raise UserIdNotProvidedException("User id hasn't been provided")
        if (result := self.repository.get_profile(user_id)) is None:
            raise UserNotFoundException(f"Can't locate user with id: {user_id}")
        return result

    def update_user(self, user_id: str, updated_info: UserUpdate) -> UserUpdate:
        # filtered = {k: v for k, v in changes.items() if v} # only pass attributes that have value => if some value is empty, it's attribute most likely isn't getting updated
        return self.repository.update_profile(user_id, updated_info)
        # return self.repository.update_profile(filtered)

    def is_user_student(self, user_obj: UserBase | None = None, user_id: str = "" ) -> bool | None:
        if not user_obj and not user_id:
            raise NoRelevantInfoProvided("Neither user object, nor user id have been provided")
        return getattr(self.get_user(user_id), "is_student", None) if not user_obj else user_obj.is_student

    def has_default_avatar(self, user_obj: UserBase | None = None, user_id: str = "") -> bool:
        """
        Checks whether user's avatar has been created by using following expression:

        ```
        'https://ui-avatars.com/api/?name=' + $displayName.split(' ').join('+') + '&background=' + Math.floor(Math.random() * 0x444444).toString(16).padStart(6, '0') + '&color=f0f6fc&size=80'
        ```
        
        That is the expression that is used for generating avatar image when user first signs up.
        """
        if not user_obj and not user_id:
            raise NoRelevantInfoProvided("Neither user object, nor user id have been provided")
        
        avatar_img_src = getattr(self.get_user(user_id), "avatar_img_src", None) if not user_obj else user_obj.avatar_img_src
        if not avatar_img_src:
            print(f"Can't locate avatar image for user: {avatar_img_src is not None}")
            return False
        pattern = re.compile(
            r"^https://ui-avatars\.com/api/\?"
            r"name=[^&]*"
            r"&background=[0-9a-f]{6}"
            r"&color=f0f6fc"
            r"&size=80$"
        )
        if pattern.fullmatch(avatar_img_src):
            print("User has default avatar")
            return True
        return False