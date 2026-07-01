from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Boolean, TIMESTAMP, DateTime, func

import uuid

Base = declarative_base()

class EmailConfirmation(Base):
    __tablename__ = "email_confirmation"
    email: Mapped[str] = mapped_column(String, primary_key=True)
    sent_uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True))
    activated: Mapped[bool] = mapped_column(Boolean)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "user"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    is_student: Mapped[bool] = mapped_column(Boolean, nullable=False)

class Group(Base):
    __tablename__ = "group"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)

class TrainingPeriod(Base):
    __tablename__ = "training_period"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location: Mapped[str] = mapped_column(String, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)

class Remark(Base):
    __tablename__ = "remark"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id: Mapped[UUID] = mapped_column(UUID, nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)

class SessionModel(Base): # otherwise it is ambiguous when working with sqlalchemy.org.Session
    __tablename__ = "session"
    user_uuid: Mapped[str] = mapped_column(String, primary_key=True, default=str(uuid.uuid4))
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    refreshes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())