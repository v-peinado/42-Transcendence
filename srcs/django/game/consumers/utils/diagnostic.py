import logging
import sys

class DiagnosticLogger:
    """Logger simple para mensajes importantes"""

    # Configure logging
    logger = logging.getLogger('game.consumers')
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    @classmethod
    def debug(cls, source, message, data=None):
        """Log debug message"""
        pass  # Desactivado para reducir ruido

    @classmethod
    def info(cls, source, message, data=None):
        """Log info message"""
        cls._log(logging.INFO, source, message)

    @classmethod
    def warn(cls, source, message, data=None):
        """Log warning message"""
        cls._log(logging.WARNING, source, message)

    @classmethod
    def error(cls, source, message, data=None, exc_info=True):
        """Log error message"""
        cls._log(logging.ERROR, source, message, exc_info)

    @classmethod
    def _log(cls, level, source, message, exc_info=False):
        """Internal logging method"""
        # Basic message
        log_msg = f"[{source}] {message}"
        
        # Log the message
        cls.logger.log(level, log_msg, exc_info=exc_info)
