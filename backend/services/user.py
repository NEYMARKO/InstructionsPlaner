from __future__ import annotations
from sqlalchemy.orm import Session

from ..repositories.user import UserRepository
from ..dto.user import UserResponse, UserRequest

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
        return self.repository.save_user(user)

    def get_user(self, user_id: str) -> UserResponse:
        return self.repository.get_user(user_id)
    
    def get_users(self) -> list[UserResponse]:
        return self.repository.get_users()
    
    def get_profile(self, user_id: str) -> UserResponse:
        if not user_id:
            raise UserIdNotProvidedException("User id hasn't been provided")
        if (result := self.repository.get_profile(user_id)) is None:
            raise UserNotFoundException(f"Can't locate user with id: {user_id}")
        return result

    def update_profile(self, changes: dict[str, str]):
        filtered = {k: v for k, v in changes.items() if v} # only pass attributes that have value => if some value is empty, it's attribute most likely isn't getting updated
        return self.repository.update_profile(filtered)