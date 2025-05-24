import logging
import os
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    """Get configured logger instance"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (optional)
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(f'{log_dir}/bot.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Set level
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    
    return logger