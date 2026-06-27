from pydantic import BaseModel
# from sqlalchemy.dialects.postgresql import UUID
from uuid import UUID

class UserDTO(BaseModel):
    id: UUID 
    username: str
    email: str
    is_student: bool

class UserCreationDTO(UserDTO):
    password: str