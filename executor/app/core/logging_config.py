"""
Logging configuration for executor
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['service'] = 'executor'
        log_record['environment'] = settings.ENVIRONMENT


def setup_logging():
    """Setup application logging"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    logging.getLogger("kubernetes").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger.info("Logging configured successfully")
