from __future__ import annotations
import os
import uuid
import asyncio
import smtplib
import traceback
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session
from email.utils import formatdate
from email.mime.text import MIMEText
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from ..dto.user import EmailConfirmationBase
from email.mime.multipart import MIMEMultipart
from ..repositories.user import UserRepository
from ..dto.user import UserResponse, UserRequest

load_dotenv(str(Path(__file__).parent / ".env"))

def send_confirmation_mail(email, confirmation_uuid: uuid.UUID) -> None:
    
    mail_sender = os.getenv("MAIL_SENDER")
    mail_sender_pass = os.getenv("MAIL_SENDER_PASS")

    if not mail_sender or not mail_sender_pass:
        raise RuntimeError("Can't locate mail sender or his password in env")

    SMTPServer = "smtp.office365.com"
    SMTPPort = 587
    recipients = [email]

    subject = "E-mail confirmation"
    body = f'Please confirm your email by clicking on the following link: <a href="http://127.0.0.1:8000/users/confirm/{confirmation_uuid}">Confirm</a>'

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

class UserService():

    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def get_service(self) -> UserService:
        return self
       
    def email_confirmed(self, email: str, wait_time: int) -> bool:
        """
        Returns True in case `activated` attribute is set to `True` and not more than `wait_time` seconds have
        elapsed since the time user creation has been requested (`requested_at` attribute). 

        :param str email: Email address of person requesting creation
        :param int wait_time: Time interval in which email activation link is valid
        :return: `True` if activation link has been clicked before time has ran out, `False` otherwise
        """
        confirm_obj = self.repository.get_mail_verification_info(email)
        return confirm_obj.activated and (datetime.now(timezone.utc) - confirm_obj.requested_at).total_seconds() < wait_time

    async def validate_email(self, email: str, wait_time: int = 60) -> bool:
        """
        Sends e-mail with activation link to the provided e-mail address (`email`) and waits
        `wait_time` seconds for user to confirm. In case `wait_time` is exceeded, exception is
        thrown.
        """
        confirmation_uuid = uuid.uuid4()
        
        try:
            self.repository.add_mail_verification_info(EmailConfirmationBase(email=email, sent_uuid=confirmation_uuid, activated=False, requested_at=datetime.now()))
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Request has already been sent for this email address")
        
        send_confirmation_mail(email, confirmation_uuid)
        
        start = datetime.now()
        while(not (confirmed:= self.email_confirmed(email, wait_time)) and (datetime.now() - start).total_seconds() <= wait_time):
            await asyncio.sleep(0.5)
        return confirmed
    
    async def create_user(self, user: UserRequest) -> UserResponse:
        if not await self.validate_email(user.email):
            raise HTTPException(status_code=408, detail="Wait time exceeded: mail not verified in time")
        self.repository.delete_mail_verification_info(user.email)
        return self.repository.save_user(user)
    
    def confirm_mail(self, validation_uuid: uuid.UUID) -> str:
        self.repository.update_mail_verification_info(validation_uuid)
        return "Your confirmation has been registered"
    
    def get_users(self) -> list[UserResponse]:
        return self.repository.get_users()