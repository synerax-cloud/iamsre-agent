"""
Logging configuration
Sets up structured logging for the application
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add level
        log_record['level'] = record.levelname
        
        # Add service name
        log_record['service'] = 'ai-sre-backend'
        
        # Add environment
        log_record['environment'] = settings.ENVIRONMENT
        
        # Add trace ID if available
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id


def setup_logging():
    """Setup application logging"""
    
    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Set formatter based on format setting
    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Silence noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("kubernetes").setLevel(logging.WARNING)
    
    logger.info("Logging configured successfully")
