"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ActionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Schemas
class AskRequest(BaseModel):
    """Request for asking a question"""
    query: str = Field(..., min_length=1, max_length=5000, description="Natural language query")
    cluster_name: Optional[str] = Field(None, description="Target cluster name")
    namespace: Optional[str] = Field(None, description="Kubernetes namespace")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class RecommendRequest(BaseModel):
    """Request for recommendations"""
    cluster_name: str = Field(..., description="Target cluster name")
    namespace: Optional[str] = Field(None, description="Kubernetes namespace")
    issue_description: Optional[str] = Field(None, description="Description of the issue")
    include_metrics: bool = Field(True, description="Include metrics in analysis")


class ExecuteActionRequest(BaseModel):
    """Request to execute an action"""
    action_type: str = Field(..., description="Type of action (restart, scale, rollback, etc.)")
    cluster_name: str = Field(..., description="Target cluster name")
    namespace: str = Field(..., description="Kubernetes namespace")
    resource_type: str = Field(..., description="Resource type (deployment, pod, etc.)")
    resource_name: str = Field(..., description="Resource name")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    dry_run: bool = Field(True, description="Perform dry run first")


class ApproveActionRequest(BaseModel):
    """Request to approve an action"""
    action_id: str = Field(..., description="Action ID")
    approved: bool = Field(..., description="Whether action is approved")
    comment: Optional[str] = Field(None, description="Approval comment")


class ChatRequest(BaseModel):
    """Chat message request"""
    message: str = Field(..., min_length=1, max_length=5000, description="Chat message")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    incident_id: Optional[str] = Field(None, description="Related incident ID")


# Response Schemas
class IncidentResponse(BaseModel):
    """Incident response"""
    id: str
    cluster_name: str
    namespace: Optional[str]
    resource_type: Optional[str]
    resource_name: Optional[str]
    title: str
    description: Optional[str]
    severity: SeverityLevel
    status: IncidentStatus
    root_cause: Optional[str]
    recommendation: Optional[str]
    detected_at: datetime
    resolved_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class ActionResponse(BaseModel):
    """Action response"""
    id: str
    incident_id: Optional[str]
    action_type: str
    cluster_name: str
    namespace: str
    resource_type: str
    resource_name: str
    parameters: Optional[Dict[str, Any]]
    dry_run: bool
    status: ActionStatus
    result: Optional[str]
    error: Optional[str]
    requested_by: str
    requested_at: datetime
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    executed_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ClusterHealthResponse(BaseModel):
    """Cluster health response"""
    cluster_name: str
    health_score: int = Field(..., ge=0, le=100)
    status: str
    metrics: Optional[Dict[str, Any]]
    issues: Optional[List[Dict[str, Any]]]
    last_checked: datetime
    
    class Config:
        from_attributes = True


class AskResponse(BaseModel):
    """Response to ask endpoint"""
    query: str
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    context_used: List[Dict[str, Any]]
    related_incidents: Optional[List[IncidentResponse]]
    recommendations: Optional[List[str]]


class ChatResponse(BaseModel):
    """Chat response"""
    session_id: str
    message: str
    response: str
    context: Optional[Dict[str, Any]]
    suggested_actions: Optional[List[ActionResponse]]


class StatusResponse(BaseModel):
    """Status response"""
    clusters: List[ClusterHealthResponse]
    active_incidents: List[IncidentResponse]
    pending_actions: List[ActionResponse]
    summary: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
