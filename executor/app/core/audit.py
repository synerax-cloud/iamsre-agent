"""
Audit logging for executor actions
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def log_action(
    action: str,
    resource_type: str,
    resource_name: str,
    namespace: str,
    user: str,
    result: str,
    dry_run: bool = False,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log an action to audit log
    
    In production, this would write to Cloud Logging or a database
    """
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "resource_type": resource_type,
        "resource_name": resource_name,
        "namespace": namespace,
        "user": user,
        "result": result,
        "dry_run": dry_run,
        "details": details or {}
    }
    
    # Log to stdout (captured by Cloud Logging in GKE)
    logger.info(f"AUDIT: {audit_entry}")
    
    # TODO: In production, also write to database
    # if settings.DATABASE_URL:
    #     await write_to_database(audit_entry)
