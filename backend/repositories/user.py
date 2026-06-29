from ..dto.user import UserResponse, UserRequest, EmailConfirmationBase
from ..models import User, EmailConfirmation

from uuid import UUID
from sqlalchemy import text
from sqlalchemy.orm import Session

class UserRepository():

    def __init__(self,  db: Session):
        self.db = db

    def save_user(self, new_user: UserRequest) -> UserResponse:
        # IN CASE OF WRITING SQL, write: SELECT * FROM public.user => NOTICE THAT SCHEMA NAME IS SPECIFIED ASWELL
        new_user_model = User(username=new_user.username, password=new_user.password, email=new_user.email, is_student=new_user.is_student)
        self.db.add(new_user_model) # when adding a non-model-object into the session, UnmappedInstanceError will get thrown
        self.db.commit()
        self.db.refresh(new_user_model) # when passing a non-model-object into the session functions, UnmappedInstanceError will get thrown
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

    def add_email_verification(self, e_obj: EmailConfirmationBase) -> None:
        email_conf_model = EmailConfirmation(email=e_obj.email, sent_uuid=e_obj.sent_uuid, activated=e_obj.activated, requested_at=e_obj.requested_at)
        self.db.add(email_conf_model)
        self.db.commit()
        return

    def delete_mail_verif(self, email: str) -> None:
        self.db.query(EmailConfirmation).filter(EmailConfirmation.email == email).delete()
        self.db.commit()
        return

    def get_email_confirmation(self, email: str) -> EmailConfirmationBase:
        result = self.db.query(EmailConfirmation).get(email)
        return EmailConfirmationBase.model_validate(result)

    def update_mail_verif(self, uuid: UUID) -> None:
        # query = """
        # UPDATE email_confirmation
        # SET activated = TRUE
        # WHERE sent_uuid = :uuid
        # """
        # self.db.execute(text(query), {"uuid": uuid})
        # self.db.commit()
        self.db.query(EmailConfirmation).\
            filter(EmailConfirmation.sent_uuid == uuid).\
                update({"activated": True})
        self.db.commit()
        return