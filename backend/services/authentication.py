import uuid
import psycopg2
from hashlib import sha256
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from ..repositories.authentication import AuthRepository
from ..dto.authentication import UserCredentials, LoginResponse, SessionDTO

def generate_token() -> str:
    return sha256(str(uuid.uuid4()).encode('utf-8')).hexdigest()

TOKEN_REFRESH_LIFETIME_HOURS = 2
TOKEN_VALIDITY_LIFETIME_DAYS = 2 

class InvalidLoginCredentialsException(Exception):
    pass

class UserNotFoundException(Exception):
    pass

class InternalServerException(Exception):
    pass

class AuthService():
    def __init__(self, db: Session) -> None:
        self.repository = AuthRepository(db)
    
    def login(self, user_credentials: UserCredentials) -> LoginResponse:
        """
        Checks whether user with these particular credentials exists. In case user has logged with
        valid credentials, session is created and session id is passed through cookies in response.    
        """
        password = ""
        try:
            password = self.repository.get_user_password(user_credentials.username)
        except ValueError:
            raise InvalidLoginCredentialsException("Invalid login credentials")
        
        if user_credentials.password != password:
            raise InvalidLoginCredentialsException("Invalid login credentials")
        
        # Save session to db to compare it during every access to restriced endpoint
        user_uuid, token = self.create_session(user_credentials.username)

        if not user_uuid or not token:
            raise 
        return LoginResponse(message="Successfully logged in", user_uuid_str=user_uuid, token=token)

    def token_expired(self, valid_until: datetime | None) -> bool:
        # valid_until is of type: datetime | None => check whether it is None before comparing it
        return valid_until is not None and valid_until < datetime.now(timezone.utc)

    def token_requires_refresh(self, refresh_at: datetime) -> bool:
        return refresh_at < datetime.now(timezone.utc)

    def create_session(self, username: str) -> tuple[str, str]:
        token = generate_token()
        user_model = self.repository.get_user_by_username(username)
        if not user_model:
            raise UserNotFoundException("Unable to find user with given username")
        try:
            self.repository.create_session(
                token=token,
                refreshes_at=datetime.now() + timedelta(hours=TOKEN_REFRESH_LIFETIME_HOURS),
                valid_until=datetime.now() + timedelta(days=TOKEN_VALIDITY_LIFETIME_DAYS),
                user_model=user_model
            )
            print("[SESSION::CREATE]: created session")
        
        except psycopg2.errors.UniqueViolation: # tried to add session for user who already has it
            self.repository.rollback()
            raise InternalServerException("Violation of unique property when creating session")
        
        return (str(user_model.id), token)
    
    def refresh_token(self, user_id: str) -> None:
        print("[SESSION::TOKEN_REFRESH]: Token's refresh threshold exceeded => refreshing it")
        if not user_id:
            raise InternalServerException("[SESSION::REFRESH_TOKEN]: User id not provided")

        self.repository.refresh_token(SessionDTO(
            user_uuid=uuid.UUID(user_id),
            token=generate_token(),
            refreshes_at=datetime.now() + timedelta(hours=TOKEN_REFRESH_LIFETIME_HOURS)
        ))
        return

    def token_valid(self, user_id: str, token: str) -> bool:
        if not user_id:
            return False
        session = self.repository.get_session(uuid.UUID(user_id), token)
        if not session or self.token_expired(session.valid_until):
            return False
        elif self.token_requires_refresh(session.refreshes_at):
            self.refresh_token(user_id=user_id)
        return True

    def logout(self, user_id: str, token: str) -> None:
        self.repository.delete_session(uuid.UUID(user_id), token)
        return