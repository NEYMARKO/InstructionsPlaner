from ..models import UserModel
from ..dto.user import UserResponse, UserRequest

from uuid import UUID
from sqlalchemy import text
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

class UserRepository():

    def __init__(self,  db: Session):
        self.db = db

    def save_user(self, new_user: UserRequest) -> UserResponse:
        # IN CASE OF WRITING SQL, write: SELECT * FROM public.user => NOTICE THAT SCHEMA NAME IS SPECIFIED ASWELL
        new_user_model = UserModel(username=new_user.username, password=new_user.password, email=new_user.email, is_student=new_user.is_student)
        try:
            self.db.add(new_user_model) # when adding a non-model-object into the session, UnmappedInstanceError will get thrown
            self.db.commit()
            self.db.refresh(new_user_model) # when passing a non-model-object into the session functions, UnmappedInstanceError will get thrown
        except IntegrityError:
            raise ValidationError("Email already exists in db")
        return UserResponse.model_validate(new_user_model)
    
    def get_users(self) -> list[UserResponse]:
        result = self.db.execute(text("SELECT * FROM public.user"))
        rows = result.mappings().all() # list of objects whose keys are columns in db and values are database values (simple as that)
        # db.commit() # if it is not commited, it will result in rollback => doesn't matter since values will still get returned
        print(rows)
        return [
            UserResponse(
                id=row.id,
                username=row.username,
                email=row.email,
                is_student=row["is_student"]
            )
            for row in rows
        ]

    def get_user_by_username(self, username: str) -> UserModel | None:
        query = select(UserModel).where(UserModel.username==username)
        return self.db.execute(query).scalar_one_or_none()
        
    def get_user_by_id(self, id: UUID) -> UserModel | None:
        query = select(UserModel).where(UserModel.id==id)
        return self.db.execute(query).scalar_one_or_none()

    def get_profile(self, user_id: str) -> UserResponse | None:
        result = self.db.execute(
            select(UserModel).where(UserModel.id==UUID(user_id))
        ).scalar_one_or_none()
        if result is None:
            return None
        return UserResponse.model_validate(result)