"""
Database models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.db.database import Base


class SeverityLevel(str, enum.Enum):
    """Incident severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentStatus(str, enum.Enum):
    """Incident status"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ActionStatus(str, enum.Enum):
    """Action execution status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class Incident(Base):
    """Incident model"""
    __tablename__ = "incidents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cluster_name = Column(String(255), nullable=False, index=True)
    namespace = Column(String(255), nullable=True, index=True)
    resource_type = Column(String(100), nullable=True)
    resource_name = Column(String(255), nullable=True)
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(SQLEnum(SeverityLevel), nullable=False, default=SeverityLevel.MEDIUM, index=True)
    status = Column(SQLEnum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN, index=True)
    
    root_cause = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    actions = relationship("Action", back_populates="incident", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="incident", cascade="all, delete-orphan")


class Action(Base):
    """Kubernetes action model"""
    __tablename__ = "actions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=True, index=True)
    
    action_type = Column(String(100), nullable=False, index=True)  # restart, scale, rollback, etc.
    cluster_name = Column(String(255), nullable=False)
    namespace = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_name = Column(String(255), nullable=False)
    
    parameters = Column(JSON, nullable=True)
    dry_run = Column(Boolean, default=True)
    
    status = Column(SQLEnum(ActionStatus), nullable=False, default=ActionStatus.PENDING, index=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    
    requested_by = Column(String(255), nullable=False)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    executed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    incident = relationship("Incident", back_populates="actions")


class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=True, index=True)
    
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    context = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    incident = relationship("Incident", back_populates="chat_messages")


class Query(Base):
    """Query history model"""
    __tablename__ = "queries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)
    
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=False, index=True)  # ask, recommend, status, etc.
    
    response = Column(Text, nullable=True)
    context_used = Column(JSON, nullable=True)
    
    execution_time = Column(Integer, nullable=True)  # milliseconds
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class ClusterHealth(Base):
    """Cluster health status model"""
    __tablename__ = "cluster_health"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cluster_name = Column(String(255), nullable=False, unique=True, index=True)
    
    health_score = Column(Integer, nullable=False)  # 0-100
    status = Column(String(50), nullable=False)  # healthy, degraded, critical
    
    metrics = Column(JSON, nullable=True)
    issues = Column(JSON, nullable=True)
    
    last_checked = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    action = Column(String(255), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    
    user_id = Column(String(255), nullable=False, index=True)
    user_ip = Column(String(50), nullable=True)
    
    details = Column(JSON, nullable=True)
    result = Column(String(50), nullable=False)  # success, failure
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
