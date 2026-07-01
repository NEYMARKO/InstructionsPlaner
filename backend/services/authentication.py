import uuid
from hashlib import sha256
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import HTTPException, Request


from ..shared import SESSION_USER_UUID_STR
from ..repositories.authentication import AuthRepository
from ..dto.authentication import UserCredentials, LoginResponse, Session as SessionDTO

def generate_token() -> str:
    return sha256(str(uuid.uuid4()).encode('utf-8')).hexdigest()

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
            raise HTTPException(status_code=401, detail="Invalid login credentials")
        
        if user_credentials.password != password:
            raise HTTPException(status_code=401, detail="Invalid login credentials")
        
        user_uuid, token = self.create_session(user_credentials.username)
        # Save session to db to compare it during every access to restriced endpoint
        return LoginResponse(message="Successfully logged in", user_uuid_str=user_uuid, token=token)

    def create_session(self, username: str) -> tuple[str, str]:
        token = generate_token()
        user_uuid = self.repository.get_user_uuid(username)
        if not user_uuid:
            raise HTTPException(status_code=404, detail="Unable to find user with given username")
        self.repository.create_session(SessionDTO(
            user_uuid=user_uuid, token=token,
            refreshes_at=datetime.now() + timedelta(hours=2),
            valid_until=datetime.now() + timedelta(days=2)
        ))
        return (user_uuid, token)
    
    def refresh_token(self, request: Request) -> None:
        user_uuid = request.cookies.get(SESSION_USER_UUID_STR, "")

        self.repository.refresh_token(SessionDTO(
            user_uuid=user_uuid,
            token=generate_token(),
            refreshes_at=datetime.now() + timedelta(hours=2)
        ))
        return