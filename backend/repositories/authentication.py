from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from ..dto.authentication import EmailConfirmationBase, SessionDTO
from ..models import EmailConfirmation, SessionModel, UserModel
from .user import UserRepository


class AuthRepository():
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repository = UserRepository(db)

    def get_user_by_username(self, username: str) -> UserModel | None:
        return self.user_repository.get_user_by_username(username)

    def get_user_by_email(self, email: str) -> UserModel | None:
        return self.user_repository.get_user_by_email(email)

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

    def delete_session(self, user_id: UUID, token: str) -> None:
        query = delete(SessionModel).where(
            (SessionModel.user_uuid==user_id) & (SessionModel.token==token)
        )
        self.db.execute(query)
        self.db.commit()
    
    def add_mail_verification_info(self, e_obj: EmailConfirmationBase) -> None:
        email_conf_model = EmailConfirmation(email=e_obj.email, sent_uuid=e_obj.sent_uuid, activated=e_obj.activated, requested_at=e_obj.requested_at)
        self.db.add(email_conf_model)
        self.db.commit()

    def get_mail_verification_info(self, email: str) -> EmailConfirmationBase:
        result = self.db.query(EmailConfirmation).get(email) # SELECT (read) does not need commit() - only INSERT, UPDATE and DELETE require it
        return EmailConfirmationBase.model_validate(result)

    def update_mail_verification_info(self, uuid: UUID) -> None:
        self.db.query(EmailConfirmation).\
            filter(EmailConfirmation.sent_uuid == uuid).\
                update({"activated": True})
        self.db.commit()

    def delete_mail_verification_info(self, email: str) -> None:
        self.db.query(EmailConfirmation).filter(EmailConfirmation.email == email).delete()
        self.db.commit()

    def create_session(
            self, token: str, refreshes_at: datetime, 
            valid_until: datetime, user_model: UserModel
        ) -> None:
        session_model = SessionModel(
            token=token,
            refreshes_at=refreshes_at,
            valid_until=valid_until,
            r_user=user_model
        )
        self.db.add(session_model)
        self.db.commit()

    def refresh_token(self, session_info: SessionDTO) -> None:
        query = update(SessionModel)\
            .where(SessionModel.user_uuid==session_info.user_uuid)\
                .values(
                    token=session_info.token,
                    refreshes_at=session_info.refreshes_at
                )
        self.db.execute(query)
        self.db.commit()
    
    def get_session(self, user_uuid: UUID, token: str) -> SessionDTO | None:
        query = select(SessionModel).where(
                (SessionModel.user_uuid==user_uuid) & (SessionModel.token==token)
        )
        result = self.db.scalars(query).one_or_none()
        print(f"{result=}")
        return SessionDTO.model_validate(result) if result is not None else result
    
    def delete_stale_sessions(self) -> None:
        self.db.execute(
            delete(SessionModel).where(SessionModel.valid_until < datetime.now(timezone.utc))
        )
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()