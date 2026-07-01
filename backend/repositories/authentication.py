from sqlalchemy.orm import Session
from sqlalchemy import insert, update, select, delete

from .user import UserRepository
from ..models import SessionModel 
from ..dto.authentication import SessionDTO 

class AuthRepository():
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repository = UserRepository(db)
    
    def get_user_password(self, username: str) -> str | None:
        """
        Retrives password for provided username.
        """
        user = self.user_repository.get_user_by_username(username)
        return user.password if user else None
    
    def get_user_uuid(self, username: str) -> str | None:
        """
        Retrives uuid for user with provided username.
        """
        user = self.user_repository.get_user_by_username(username)
        return str(user.id) if user else None

    def delete_session(self, user_uuid: str) -> None:
        query = delete(SessionModel).where(SessionModel.user_uuid==user_uuid)
        self.db.execute(query)
        self.db.commit()
        return

    def create_session(self, session_info: SessionDTO) -> None:
        query = insert(SessionModel).values(
            user_uuid=session_info.user_uuid, token=session_info.token, 
            refreshes_at=session_info.refreshes_at, valid_until=session_info.valid_until
        )
        self.db.execute(query)
        self.db.commit()
        return

    def refresh_token(self, session_info: SessionDTO) -> None:
        query = update(SessionModel)\
            .where(SessionModel.user_uuid==session_info.user_uuid)\
                .values(
                    token=session_info.token,
                    refreshes_at=session_info.refreshes_at
                )
        self.db.execute(query)
        self.db.commit()
        return
    
    def get_session(self, user_uuid: str) -> SessionDTO | None:
        query = select(SessionModel).where(SessionModel.user_uuid==user_uuid)
        result = self.db.execute(query).one_or_none()
        return SessionDTO.model_validate(result) if result is not None else result