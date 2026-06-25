from pydantic import BaseModel

class UserDTO(BaseModel):
    username: str
    email: str
    is_student: bool

class UserCreationDTO(UserDTO):
    password: str