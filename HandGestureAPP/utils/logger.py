import logging
from pathlib import Path
from datetime import datetime

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger("HandGestureRPS")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        file_handler = logging.FileHandler(log_dir / f"handsgesturerps_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
    return logger
