from datetime import datetime
from pydantic import BaseModel, ConfigDict

class LoginResponse(BaseModel):
    message: str
    token: str
    user_uuid_str: str

class LogoutResponse(BaseModel):
    message: str

class UserCredentials(BaseModel):
    username: str
    password: str

# class SessionResponse(BaseModel):
#     token: str
#     user_uuid: str

# class SessionRequest(BaseModel):
#     user_uuid: str
#     token: str
#     expires_at: datetime
#     valid_until: datetime

class SessionDTO(BaseModel): # otherwise it is ambiguous when working with sqlalchemy.org.Session
    user_uuid: str
    token: str
    refreshes_at: datetime
    valid_until: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
