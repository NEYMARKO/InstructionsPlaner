from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str
    is_student: bool = False

    model_config = {
        "from_attributes": True
    }

class UserResponse(UserBase):
    id: UUID

class UserRequest(UserBase):
    password: str

class UserCredentials(BaseModel):
    username: str
    password: str

class EmailConfirmationBase(BaseModel):
    email: str
    sent_uuid: UUID
    activated: bool
    requested_at: datetime
    model_config = {
        "from_attributes": True
    }
    
class LoginResponse(BaseModel):
    message: str
    user_uuid_str: str
    session_uuid_str: str

class LogoutResponse(BaseModel):
    message: str

# class UserResponse(BaseModel):
#     id: UUID
#     username: str
#     email: str
#     is_student: bool

# class UserRequest(UserResponse):
#     password: str