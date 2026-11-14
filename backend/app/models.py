import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    memberships = relationship("Membership", back_populates="tenant", cascade="all, delete-orphan")
    sops = relationship("SOP", back_populates="tenant", cascade="all, delete-orphan")
    training_sessions = relationship("TrainingSession", back_populates="tenant")

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    memberships = relationship("Membership", back_populates="account", cascade="all, delete-orphan")
    training_sessions = relationship("TrainingSession", back_populates="account")

class Membership(Base):
    __tablename__ = "memberships"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "manager" | "employee"
    created_at = Column(DateTime, default=utc_now)
    
    account = relationship("Account", back_populates="memberships")
    tenant = relationship("Tenant", back_populates="memberships")

class SOP(Base):
    __tablename__ = "sops"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    title = Column(String(200), nullable=False)
    active_version_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    tenant = relationship("Tenant", back_populates="sops")
    versions = relationship("SOPVersion", back_populates="sop", cascade="all, delete-orphan")

class SOPVersion(Base):
    __tablename__ = "sop_versions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    sop_id = Column(String(36), ForeignKey("sops.id"), nullable=False)
    version_no = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # "draft" | "approved" | "superseded"
    steps_json = Column(JSON, nullable=False)  # List of {id, instruction}
    rubric_json = Column(JSON, nullable=False)  # List of {id, label, weight, critical}
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    sop = relationship("SOP", back_populates="versions")

class TrainingSession(Base):
    __tablename__ = "training_sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    sop_version_id = Column(String(36), ForeignKey("sop_versions.id"), nullable=False)
    module_json = Column(JSON, nullable=False)  # Compiled ModuleDraft
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    
    tenant = relationship("Tenant", back_populates="training_sessions")
    account = relationship("Account", back_populates="training_sessions")
    turns = relationship("Turn", back_populates="session", cascade="all, delete-orphan", order_by="Turn.turn_no")
    result = relationship("TrainingResult", back_populates="session", uselist=False, cascade="all, delete-orphan")

class Turn(Base):
    __tablename__ = "turns"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("training_sessions.id"), nullable=False)
    turn_no = Column(Integer, nullable=False)
    employee_text = Column(Text, nullable=False)
    customer_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    session = relationship("TrainingSession", back_populates="turns")

class TrainingResult(Base):
    __tablename__ = "training_results"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("training_sessions.id"), unique=True, nullable=False)
    score = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)
    critical_failure = Column(Boolean, nullable=False, default=False)
    payload_json = Column(JSON, nullable=False)  # FinalResult payload
    created_at = Column(DateTime, default=utc_now)
    
    session = relationship("TrainingSession", back_populates="result")
