from __future__ import annotations
from fastapi import HTTPException
from ..dto.user import UserDTO, UserCreationDTO
from ..repositories.user import UserRepository
from sqlalchemy.orm import Session


repository = UserRepository()

def validate_email(email: str) -> bool:
    return "@" in email

class UserService():
    def get_service(self) -> UserService:
        return self
    
    def create_user(self, user: UserCreationDTO, db: Session) -> UserDTO:
        if not validate_email(user.email):
            raise HTTPException(status_code=400, detail="Email not verified")
        repository.save_user(user, db)
        return user