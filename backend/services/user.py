from __future__ import annotations
from fastapi import HTTPException
from ..dto.user import UserDTO, UserCreationDTO
from ..repositories.user import UserRepository
from sqlalchemy.orm import Session

def validate_email(email: str) -> bool:
    return "@" in email

class UserService():

    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def get_service(self) -> UserService:
        return self
    
    def create_user(self, user: UserCreationDTO) -> UserDTO:
        if not validate_email(user.email):
            raise HTTPException(status_code=400, detail="Email not verified")
        self.repository.save_user(user)
        return user
    
    def get_users(self) -> list[UserDTO]:
        return self.repository.get_users()