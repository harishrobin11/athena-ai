import logging
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """
    Custom formatter to output logs as structured JSON strings.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Inject standard contextual attributes if present
        if getattr(record, "user_id", None):
            log_obj["user_id"] = record.user_id
        if getattr(record, "workspace_id", None):
            log_obj["workspace_id"] = record.workspace_id
        
        # Include exception tracebacks if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

def setup_logger(name: str = "athena") -> logging.Logger:
    """
    Configures and returns a singleton logger instance emitting JSON to stdout.
    """
    logger = logging.getLogger(name)
    
    # Prevent re-adding handlers if already initialized
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JSONFormatter())
        
        logger.addHandler(console_handler)
        
        # Prevent propagation to the root logger to avoid duplicate standard logs
        logger.propagate = False
        
    return logger

# Global singleton
logger = setup_logger()
