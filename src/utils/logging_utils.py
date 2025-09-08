"""
Logging utilities for Project Synapse
Structured logging with Indian context awareness
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from config.settings import settings


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Avoid duplicate handlers
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        if settings.log_file:
            log_path = Path(settings.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Set level
        logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    return logger
