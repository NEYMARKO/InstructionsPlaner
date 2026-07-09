from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

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
    user_uuid: UUID
    token: str
    refreshes_at: datetime
    valid_until: datetime | None = None
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
        from_attributes=True
    )

class EmailConfirmationBase(BaseModel):
    email: str
    sent_uuid: UUID
    activated: bool
    requested_at: datetime
    model_config = {
        "from_attributes": True
    }
