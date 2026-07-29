from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class UserBase(BaseModel):
    username: str
    display_name: str
    email: str
    city: str | None
    country: str | None
    avatar_img_src: str | None
    is_student: bool = False

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
        from_attributes=True
    )

class UserUpdate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID

class UserRequest(UserBase):
    password: str