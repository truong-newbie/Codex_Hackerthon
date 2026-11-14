import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Index
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
    active = Column(Boolean, nullable=False, default=True, server_default="1")
    token_version = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime, default=utc_now)
    
    memberships = relationship("Membership", back_populates="account", cascade="all, delete-orphan")
    training_sessions = relationship("TrainingSession", back_populates="account")

class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (Index("ux_memberships_user_tenant", "user_id", "tenant_id", unique=True),)
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "manager" | "employee"
    active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime, default=utc_now)
    
    account = relationship("Account", back_populates="memberships")
    tenant = relationship("Tenant", back_populates="memberships")

class SOP(Base):
    __tablename__ = "sops"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    title = Column(String(200), nullable=False)
    active_version_id = Column(String(36), nullable=True)
    archived_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    tenant = relationship("Tenant", back_populates="sops")
    versions = relationship("SOPVersion", back_populates="sop", cascade="all, delete-orphan")

class SOPVersion(Base):
    __tablename__ = "sop_versions"
    __table_args__ = (Index("ux_sop_versions_sop_number", "sop_id", "version_no", unique=True),)
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    sop_id = Column(String(36), ForeignKey("sops.id"), nullable=False)
    version_no = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # "draft" | "approved" | "superseded"
    revision = Column(Integer, nullable=False, default=0, server_default="0")
    base_version_id = Column(String(36), nullable=True)
    policy_json = Column(JSON, nullable=True)
    steps_json = Column(JSON, nullable=False)  # List of {id, instruction}
    rubric_json = Column(JSON, nullable=False)  # List of {id, label, weight, critical}
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    sop = relationship("SOP", back_populates="versions")

class TrainingSession(Base):
    __tablename__ = "training_sessions"
    __table_args__ = (
        Index("ix_training_sessions_tenant_time", "tenant_id", "created_at", "id"),
        Index("ix_training_sessions_user_time", "user_id", "created_at", "id"),
    )
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    sop_version_id = Column(String(36), ForeignKey("sop_versions.id"), nullable=False)
    module_json = Column(JSON, nullable=False)  # Compiled ModuleDraft
    state = Column(String(20), nullable=False, default="active", server_default="active")
    revision = Column(Integer, nullable=False, default=0, server_default="0")
    busy_operation_id = Column(String(36), nullable=True)
    execution_profile_json = Column(JSON, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    
    tenant = relationship("Tenant", back_populates="training_sessions")
    account = relationship("Account", back_populates="training_sessions")
    turns = relationship("Turn", back_populates="session", cascade="all, delete-orphan", order_by="Turn.turn_no")
    result = relationship("TrainingResult", back_populates="session", uselist=False, cascade="all, delete-orphan")

class Turn(Base):
    __tablename__ = "turns"
    __table_args__ = (
        Index("ux_turns_session_number", "session_id", "turn_no", unique=True),
        Index("ux_turns_operation", "operation_id", unique=True),
    )
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("training_sessions.id"), nullable=False)
    turn_no = Column(Integer, nullable=False)
    operation_id = Column(String(36), nullable=True)
    employee_text = Column(Text, nullable=False)
    customer_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    session = relationship("TrainingSession", back_populates="turns")

class TrainingResult(Base):
    __tablename__ = "training_results"
    __table_args__ = (Index("ux_training_results_operation", "operation_id", unique=True),)
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("training_sessions.id"), unique=True, nullable=False)
    operation_id = Column(String(36), nullable=True)
    score = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)
    critical_failure = Column(Boolean, nullable=False, default=False)
    payload_json = Column(JSON, nullable=False)  # FinalResult payload
    scoring_version = Column(String(30), nullable=True)
    evidence_schema_version = Column(String(30), nullable=True)
    transcript_revision = Column(Integer, nullable=True)
    transcript_sha256 = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    session = relationship("TrainingSession", back_populates="result")


class Operation(Base):
    __tablename__ = "operations"
    __table_args__ = (
        Index("ux_operations_actor_key", "tenant_id", "user_id", "kind", "idempotency_key", unique=True),
        Index("ix_operations_session_status", "session_id", "status"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("training_sessions.id"), nullable=True)
    kind = Column(String(20), nullable=False)
    idempotency_key = Column(String(80), nullable=False)
    payload_sha256 = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="pending", server_default="pending")
    attempt = Column(Integer, nullable=False, default=1, server_default="1")
    request_revision = Column(Integer, nullable=True)
    snapshot_json = Column(JSON, nullable=True)
    lease_token = Column(String(36), nullable=True)
    lease_until = Column(DateTime, nullable=True)
    response_json = Column(JSON, nullable=True)
    error_code = Column(String(40), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_tenant_time", "tenant_id", "created_at", "id"),)

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    actor_id = Column(String(36), ForeignKey("accounts.id"), nullable=False)
    action = Column(String(60), nullable=False)
    resource_type = Column(String(40), nullable=False)
    resource_id = Column(String(36), nullable=False)
    request_id = Column(String(36), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
