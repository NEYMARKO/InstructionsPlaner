from pydantic import BaseModel

class UserDTO(BaseModel):
    username: str
    email: str
    type: int

class UserCreationDTO(UserDTO):
    password: str