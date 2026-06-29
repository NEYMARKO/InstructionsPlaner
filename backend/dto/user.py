from pydantic import BaseModel
# from sqlalchemy.dialects.postgresql import UUID
from uuid import UUID

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

# class UserResponse(BaseModel):
#     id: UUID
#     username: str
#     email: str
#     is_student: bool

# class UserRequest(UserResponse):
#     password: str