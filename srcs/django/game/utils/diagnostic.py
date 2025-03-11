import logging
import sys
import traceback
import json
from datetime import datetime

class DiagnosticLogger:
    """Central diagnostic logging for game module"""

    # Configure logging
    logger = logging.getLogger('game.diagnostic')
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    @classmethod
    def debug(cls, source, message, data=None):
        """Log debug message"""
        cls._log(logging.DEBUG, source, message, data)

    @classmethod
    def info(cls, source, message, data=None):
        """Log info message"""
        cls._log(logging.INFO, source, message, data)

    @classmethod
    def warn(cls, source, message, data=None):
        """Log warning message"""
        cls._log(logging.WARNING, source, message, data)

    @classmethod
    def error(cls, source, message, data=None, exc_info=True):
        """Log error message"""
        cls._log(logging.ERROR, source, message, data, exc_info)

    @classmethod
    def _log(cls, level, source, message, data=None, exc_info=False):
        """Internal logging method"""
        # Basic message
        log_msg = f"[{source}] {message}"
        
        # Add data if provided
        if data is not None:
            try:
                if isinstance(data, dict) or isinstance(data, list):
                    data_str = json.dumps(data, default=str)
                else:
                    data_str = str(data)
                    
                log_msg += f" - Data: {data_str}"
            except Exception as e:
                log_msg += f" - Data: [Error serializing: {str(e)}]"
        
        # Log the message
        cls.logger.log(level, log_msg, exc_info=exc_info)
        
        # In case of error, add stack trace if not already included
        if level >= logging.ERROR and not exc_info:
            stack = ''.join(traceback.format_stack()[:-1])
            cls.logger.log(level, f"Stack trace for previous error:\n{stack}")
