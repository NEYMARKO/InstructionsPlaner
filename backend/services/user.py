from __future__ import annotations
import os
import uuid
import smtplib
import traceback
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session
from email.utils import formatdate
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..repositories.user import UserRepository
from ..dto.user import UserResponse, UserRequest

load_dotenv(str(Path(__file__).parent / ".env"))

class UserService():

    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def get_service(self) -> UserService:
        return self
    
    def send_confirmation_mail(self, email) -> None:
        
        mail_sender = os.getenv("MAIL_SENDER")
        mail_sender_pass = os.getenv("MAIL_SENDER_PASS")

        if not mail_sender or not mail_sender_pass:
            raise RuntimeError("Can't locate mail sender or his password in env")

        confirm_uuid = uuid.uuid4()

        SMTPServer = "smtp.office365.com"
        SMTPPort = 587
        recipients = [email]

        subject = "E-mail confirmation"
        body = f'Please confirm your email by clicking on the following link: <a href="http://127.0.0.1:8000/users/confirm/{confirm_uuid}">Confirm</a>'

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
    
    def validate_email(self, email: str, wait_time: int = 120) -> bool:
        """
        Sends e-mail with activation link to the provided e-mail address (`email`) and waits
        `wait_time` seconds for user to confirm. In case `wait_time` is exceeded, exception is
        thrown.
        """
        print("SENDING EMAIL")
        self.send_confirmation_mail(email)
        return "@" in email
    
    def create_user(self, user: UserRequest) -> UserResponse:
        if not self.validate_email(user.email):
            raise HTTPException(status_code=400, detail="Email not verified")
        return self.repository.save_user(user)
    
    def get_users(self) -> list[UserResponse]:
        return self.repository.get_users()