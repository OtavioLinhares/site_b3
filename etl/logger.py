import logging
import os
from datetime import datetime

class PipelineLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(self.log_dir, f"update_{self.today}.log")
        
        # Setup Logger
        self.logger = logging.getLogger("PipelineLogger")
        self.logger.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File Handler
        fh = logging.FileHandler(self.log_file)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        # Console Handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
    def info(self, msg):
        self.logger.info(msg)
        
    def warning(self, msg):
        self.logger.warning(msg)
        
    def error(self, msg):
        self.logger.error(msg)
        
    def log_exclusion(self, ticker, reason, details=None):
        msg = f"EXCLUSION [{ticker}]: {reason}"
        if details:
            msg += f" | {details}"
        self.logger.warning(msg)
