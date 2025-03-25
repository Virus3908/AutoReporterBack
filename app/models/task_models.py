# app/models/task_models.py

import uuid
from sqlalchemy import (
    Column, Integer, String, Text, Float, TIMESTAMP,
    ForeignKey, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    type = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False, server_default=text("0"))
    callback_url = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    convert = relationship("Convert", back_populates="task", uselist=False)
    diarize = relationship("Diarize", back_populates="task", uselist=False)
    transcribe = relationship("Transcribe", back_populates="task", uselist=False)
    report = relationship("Report", back_populates="task", uselist=False)


class Convert(Base):
    __tablename__ = "convert"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    file_url = Column(Text, nullable=False)
    converted_file_url = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    task = relationship("Task", back_populates="convert")


class Diarize(Base):
    __tablename__ = "diarize"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    file_url = Column(Text, nullable=False)
    segments = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    task = relationship("Task", back_populates="diarize")


class Transcribe(Base):
    __tablename__ = "transcribe"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    transcription = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    task = relationship("Task", back_populates="transcribe")


class Report(Base):
    __tablename__ = "report"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    promt = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    report = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    task = relationship("Task", back_populates="report")