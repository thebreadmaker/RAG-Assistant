import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

# Ensure logs directory exists at safina-rag/logs/
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging(name: str = "safina-rag") -> logging.Logger:
    """Configure comprehensive logging with file and console handlers.
    
    Creates:
    - all_TIMESTAMP.log: All logs at DEBUG level
    - errors_TIMESTAMP.log: Errors and above
    - Console output at INFO level
    
    Returns:
        logging.Logger: Configured logger instance
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to prevent duplicates
    logger.handlers.clear()
    
    # Detailed formatter with context
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Simple formatter for console
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler - All logs with rotation
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    all_logs_file = LOGS_DIR / f"all_{timestamp}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        str(all_logs_file), 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # File handler - Errors only with rotation
    error_logs_file = LOGS_DIR / f"errors_{timestamp}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        str(error_logs_file),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Console handler - INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"✅ Logging initialized - Logs directory: {LOGS_DIR}")
    
    return logger


# Create module-level logger - use this throughout the app
logger = setup_logging()
