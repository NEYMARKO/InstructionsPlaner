from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID

import uuid

Base = declarative_base()

class EmailConfirmation(Base):
    __tablename__ = "email_confirmation"
    email = Column(String, primary_key=True)
    sent_uuid = Column(UUID(as_uuid=True))
    activated = Column(Boolean)
    requested_at = Column(TIMESTAMP)

class User(Base):
    __tablename__ = "user"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    is_student = Column(Boolean, nullable=False)

class Group(Base):
    __tablename__ = "group"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

class TrainingPeriod(Base):
    __tablename__ = "training_period"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    start_time = Column(TIMESTAMP, nullable=False)

class Remark(Base):
    __tablename__ = "remark"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID, nullable=False)
    text = Column(String, nullable=False)