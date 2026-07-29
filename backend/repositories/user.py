from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session
from sqlalchemy.sql import insert, update

from backend.dto.user import UserUpdate

from ..dto.user import UserRequest, UserResponse
from ..models import UserModel


class UserRepository():

    def __init__(self,  db: Session):
        self.db = db

    def save_user(self, new_user: UserRequest) -> UserResponse:
        # IN CASE OF WRITING SQL, write: SELECT * FROM public.user => NOTICE THAT SCHEMA NAME IS SPECIFIED ASWELL
        query = insert(UserModel).values(
            username=new_user.username,
            display_name=new_user.display_name,
            password=new_user.password,
            email=new_user.email,
            is_student=new_user.is_student,
            country=new_user.country,
            city=new_user.city,
            avatar_img_src=new_user.avatar_img_src
        )
        # new_user_model = UserModel(username=new_user.username, password=new_user.password, email=new_user.email, is_student=new_user.is_student)
        # self.db.add(new_user_model) # when adding a non-model-object into the session, UnmappedInstanceError will get thrown
        result = self.db.execute(query)
        self.db.commit()
        # self.db.refresh(new_user_model) # when passing a non-model-object into the session functions, UnmappedInstanceError will get thrown
        # return UserResponse.model_validate(new_user_model)
        return UserResponse.model_validate(result)

    def get_user(self, user_id: str) -> UserResponse | None:
        query = select(UserModel).where(UserModel.id==user_id)
        result = self.db.execute(query).scalar_one_or_none()
        if not result:
            return None
        return UserResponse.model_validate(result)
    
    def get_users(self) -> list[UserResponse]:
        result = self.db.execute(text("SELECT * FROM public.user"))
        rows = result.mappings().all() # list of objects whose keys are columns in db and values are database values (simple as that)
        # db.commit() # if it is not commited, it will result in rollback => doesn't matter since values will still get returned
        print(rows)
        return [
            UserResponse(
                id=row.id,
                username=row.username,
                display_name=row.display_name,
                email=row.email,
                city=row.city,
                country=row.country,
                avatar_img_src=row.avatar_img_src,
                is_student=row["is_student"]
            )
            for row in rows
        ]

    def get_user_by_username(self, username: str) -> UserModel | None:
        query = select(UserModel).where(UserModel.username==username)
        return self.db.execute(query).scalar_one_or_none()

    def get_user_by_email(self, email: str) -> UserModel | None:
        query = select(UserModel).where(UserModel.email==email)
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

    def update_profile(self, user_id: str, updated_info: UserUpdate) -> UserUpdate:
        query = update(UserModel).where(UserModel.id==user_id).values(
            username=updated_info.username,
            display_name=updated_info.display_name, 
            email=updated_info.email,
            country=updated_info.country,
            city=updated_info.city
            )
        self.db.execute(query)
        self.db.commit()
        result = self.db.get(UserModel, user_id)
        return UserUpdate.model_validate(result)