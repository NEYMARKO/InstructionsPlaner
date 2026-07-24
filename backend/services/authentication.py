import asyncio
import os
import smtplib
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from hashlib import sha256
from typing import Literal

import psycopg2
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..dto.authentication import (
    EmailConfirmationBase,
    SignUpResponse,
    LoginResponse,
    SessionDTO,
    UserCredentials,
)
from ..dto.user import UserRequest
from ..notifications import event_system as ES
from ..repositories.authentication import AuthRepository
from ..services.user import UserService


def generate_token() -> str:
    return sha256(str(uuid.uuid4()).encode('utf-8')).hexdigest()

TOKEN_REFRESH_LIFETIME_HOURS = 2
TOKEN_VALIDITY_LIFETIME_DAYS = 2 

CHECK_INTERVAL_SEC = 2


EventType = Literal["info", "error", "success"]

class RequestDuplicateException(Exception):
    pass

class RequestTimeoutException(Exception):
    pass

class EmailAlreadyRegisteredException(Exception):
    pass

class EmailConfirmationValidationException(Exception):
    pass

class UserCreationException(Exception):
    pass

class UserIdNotProvidedException(Exception):
    pass

class InvalidLoginCredentialsException(Exception):
    pass

class UserNotFoundException(Exception):
    pass

class InternalServerException(Exception):
    pass

def send_confirmation_mail(email: str, confirmation_uuid: uuid.UUID) -> None:
    
    mail_sender = os.getenv("MAIL_SENDER")
    mail_sender_pass = os.getenv("MAIL_SENDER_PASS")

    if not mail_sender or not mail_sender_pass:
        raise RuntimeError("Can't locate mail sender or his password in env")

    SMTPServer = "smtp.office365.com"
    SMTPPort = 587
    recipients = [email]

    subject = "E-mail confirmation"
    body = f'Please confirm your email by clicking on the following link: <a href="http://127.0.0.1:8000/auth/confirm/{confirmation_uuid}">Confirm</a>'

    try:
        msg = MIMEMultipart()
        msg['From'] = mail_sender
        msg['To'] = ", ".join(recipients)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, "html", "utf-8"))
        server = smtplib.SMTP(SMTPServer, SMTPPort)
        server.connect(SMTPServer, SMTPPort)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(mail_sender, mail_sender_pass)
        server.send_message(msg)
        server.quit()
    except Exception:
        print(f"{traceback.format_exc()=}")
    
    return

class AuthService():
    def __init__(self, db: Session) -> None:
        self.user_service = UserService(db)
        self.repository = AuthRepository(db)
    
    def email_confirmed(self, email: str, wait_time: int) -> bool:
        """
        Returns True in case `activated` attribute is set to `True` and not more than `wait_time` seconds have
        elapsed since the time user creation has been requested (`requested_at` attribute). 

        :param str email: Email address of person requesting creation
        :param int wait_time: Time interval in which email activation link is valid
        :return: `True` if activation link has been clicked before time has ran out, `False` otherwise
        """
        confirm_obj = None
        try:
            confirm_obj = self.repository.get_mail_verification_info(email)
        except ValidationError:
            raise EmailConfirmationValidationException("Email confirmation could not get validated")
        return confirm_obj.activated and (datetime.now(timezone.utc) - confirm_obj.requested_at).total_seconds() < wait_time

    async def wait_for_confirmation(self, user: UserRequest, wait_time: int) -> bool:
        start = datetime.now()
        i = 0
        while(not (confirmed:= self.email_confirmed(user.email, wait_time)) and (datetime.now() - start).total_seconds() <= wait_time):
                print(f"[CHECKING] Pefrorming check no. {i}...")
                await asyncio.sleep(CHECK_INTERVAL_SEC)
                i += 1
        self.repository.delete_mail_verification_info(user.email) # this info needs to be deleted no matter the outcome (it will otherwise block any future mail sending to that address)
        if not confirmed:
            raise RequestTimeoutException("Email wasn't confirmed in time")            
        return True
    

    def send_confirmation(self, user: UserRequest) -> None:
        confirmation_uuid = uuid.uuid4()

        if self.repository.get_user_by_email(user.email):
            raise EmailAlreadyRegisteredException("Provided e-mail address has already been registered")
        
        try:
            self.repository.add_mail_verification_info(EmailConfirmationBase(email=user.email, sent_uuid=confirmation_uuid, activated=False, requested_at=datetime.now()))
        except IntegrityError:
            self.repository.rollback()
            raise RequestDuplicateException("Request has already been sent for this email address")
        
        send_confirmation_mail(user.email, confirmation_uuid)
        return

    def confirm_mail(self, validation_uuid: uuid.UUID) -> str:
        print("MAIL CONFIRMED")
        self.repository.update_mail_verification_info(validation_uuid)
        return "Your confirmation has been registered"

    def save_user(self, user: UserRequest) -> bool:
        try:
            self.user_service.add_user(user)
        except ValidationError:
            raise UserCreationException("Problems with creating user")
        except psycopg2.errors.UniqueViolation:
            self.repository.rollback()
            raise EmailAlreadyRegisteredException("Provided e-mail address has already been registered")
        return True

    # async def sign_up(self, user: UserRequest) -> AsyncGenerator[tuple[EventType, str], None]:
    async def sign_up(self, event_subscription_id: str, user: UserRequest) -> SignUpResponse | None:
        user_saved = False
        try:
            self.send_confirmation(user)
            ES.add_notification_to_queue(event_subscription_id, {"infoMsg": f"Mail has been sent to {user.email}, please confirm it.", "errorMsg": "", "successMsg": ""})
        except (RequestDuplicateException, EmailAlreadyRegisteredException) as e:
            ES.add_notification_to_queue(event_subscription_id, {"infoMsg": "", "errorMsg": str(e), "successMsg": ""})
            return
        try:
            try:
                if await asyncio.create_task(self.wait_for_confirmation(user, wait_time=20)):
                    user_saved = self.save_user(user)
            except asyncio.CancelledError:
                print("CANCELLED MID WAIT")
        except RequestTimeoutException as e:
            ES.add_notification_to_queue(event_subscription_id, {"infoMsg": "", "errorMsg": str(e), "successMsg": ""})
            return
        except (EmailConfirmationValidationException, UserCreationException):
            ES.add_notification_to_queue(event_subscription_id, {"infoMsg": "", "errorMsg": "Something went wrong, please try again.", "successMsg": ""})
        if user_saved:
            ES.add_notification_to_queue(event_subscription_id, {"infoMsg": "", "errorMsg": "", "successMsg": "Sucessfully signed up"})
        user_id, token = self.create_session(user.username)
        return SignUpResponse(token=token, user_id=user_id)

    def login(self, event_subscription_id: str, user_credentials: UserCredentials) -> LoginResponse | None:
        """
        Checks whether user with these particular credentials exists. In case user has logged with
        valid credentials, session is created and session id is passed through cookies in response.    
        """
        token = ""
        user_uuid = ""

        password = self.repository.get_user_password(user_credentials.username)
        
        if user_credentials.password != password:
            ES.add_notification_to_queue(event_subscription_id, {"error": "Invalid login credentials"})
            return None
        
        # Save session to db to compare it during every access to restriced endpoint
        try:
            user_uuid, token = self.create_session(user_credentials.username)
        except UserNotFoundException:
            ES.add_notification_to_queue(event_subscription_id, {"error": "Invalid login credentials"})
            return None

        if not user_uuid or not token:
            ES.add_notification_to_queue(event_subscription_id, {"error": "Something went wrong, please try again."})
            return None
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