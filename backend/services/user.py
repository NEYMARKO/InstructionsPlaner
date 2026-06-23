from __future__ import annotations
from fastapi import HTTPException
from ..dto.user import UserDTO, UserCreationDTO

def validate_email(email: str) -> bool:
    return "@" in email

class UserService():
    def get_service(self) -> UserService:
        return self
    
    def create_user(self, user: UserCreationDTO) -> UserDTO:
        if not validate_email(user.email):
            raise HTTPException(status_code=400, detail="Email not verified")
        return user