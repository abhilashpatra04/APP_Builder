import uuid
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    PLAN_REVIEW = "plan_review"
    ARCHITECTING = "architecting"
    TASK_REVIEW = "task_review"
    CODING = "coding"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    projects = relationship("Project", back_populates="user")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=True)
    prompt = Column(Text, nullable=False)
    status = Column(String, default=ProjectStatus.PLANNING)
    current_stage = Column(String, default="planning")
    thread_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="projects")
    plan = relationship("Plan", back_populates="project", uselist=False)
    task_plan = relationship("TaskPlanRecord", back_populates="project", uselist=False)
    files = relationship("ProjectFile", back_populates="project")
    chat_messages = relationship("ChatMessage", back_populates="project")


class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    plan_json = Column(Text, nullable=False)
    tech_stacks = Column(JSON, default=list)
    review_status = Column(String, default="pending")
    user_edits = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="plan")


class TaskPlanRecord(Base):
    __tablename__ = "task_plans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    task_plan_json = Column(Text, nullable=False)
    review_status = Column(String, default="pending")
    user_edits = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="task_plan")


class ProjectFile(Base):
    __tablename__ = "project_files"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    filepath = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    status = Column(String, default="pending")
    before_content = Column(Text, nullable=True)
    error_log = Column(Text, nullable=True)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="files")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    affected_files = Column(JSON, default=list)
    applied = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="chat_messages")
