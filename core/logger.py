import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Optional

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'app.log')

# Configure logger
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Prevent double logging

# File handler with rotation
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2*1024*1024, backupCount=5)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
))
logger.addHandler(file_handler)

# Helper function

def get_logger(name: Optional[str] = None):
    if name:
        return logger.getChild(name)
    return logger
