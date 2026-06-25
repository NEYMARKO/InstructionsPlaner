from ..dto.user import UserDTO, UserCreationDTO
from ..models import User

from sqlalchemy.orm import Session

class UserRepository():
    def save_user(self, new_user: UserCreationDTO, db: Session) -> UserDTO:
        new_user_model = User(username=new_user.username, password=new_user.password, email=new_user.email, is_student=new_user.is_student)
        db.add(new_user_model) # when adding a non-model-object into the session, UnmappedInstanceError will get thrown
        db.commit()
        db.refresh(new_user_model) # when passing a non-model-object into the session functions, UnmappedInstanceError will get thrown
        return new_user