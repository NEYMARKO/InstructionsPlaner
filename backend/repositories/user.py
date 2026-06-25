from ..dto.user import UserDTO, UserCreationDTO
from ..models import User

from sqlalchemy import text
from sqlalchemy.orm import Session

class UserRepository():
    def save_user(self, new_user: UserCreationDTO, db: Session) -> UserDTO:
        # IN CASE OF WRITING SQL, write: SELECT * FROM public.user => NOTICE THAT SCHEMA NAME IS SPECIFIED ASWELL
        new_user_model = User(username=new_user.username, password=new_user.password, email=new_user.email, is_student=new_user.is_student)
        db.add(new_user_model) # when adding a non-model-object into the session, UnmappedInstanceError will get thrown
        db.commit()
        db.refresh(new_user_model) # when passing a non-model-object into the session functions, UnmappedInstanceError will get thrown
        return new_user
    
    def get_users(self, db: Session) -> list[UserDTO]:
        result = db.execute(text("SELECT * FROM public.user"))
        rows = result.mappings().all()
        # db.commit() # if it is not commited, it will result in rollback => doesn't matter since values will still get returned
        return [
            UserDTO(
                username=row["username"],
                email=row["email"],
                is_student=row["is_student"]
            )
            for row in rows
        ]