import os
import shutil
import hashlib
from datetime import datetime
from typing import Optional
from telegram import File as TelegramFile
from utils.logger import get_logger

logger = get_logger(__name__)

def save_uploaded_file(file_info: TelegramFile, filename: str) -> str:
    """Save uploaded file from Telegram to local storage"""
    try:
        # Create documents directory if it doesn't exist
        docs_dir = "db/documents"
        os.makedirs(docs_dir, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in filename if c.isalnum() or c in '._-')
        unique_filename = f"{timestamp}_{safe_filename}"
        
        file_path = os.path.join(docs_dir, unique_filename)
        
        # Download file from Telegram
        with open(file_path, 'wb') as f:
            file_info.download(out=f)
        
        logger.info(f"File saved successfully: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise

def get_file_hash(file_path: str) -> Optional[str]:
    """Calculate MD5 hash of file"""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return None

def cleanup_old_files(days: int = 30) -> int:
    """Clean up files older than specified days"""
    try:
        docs_dir = "db/documents"
        if not os.path.exists(docs_dir):
            return 0
        
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for filename in os.listdir(docs_dir):
            file_path = os.path.join(docs_dir, filename)
            if os.path.isfile(file_path):
                if os.path.getmtime(file_path) < cutoff_time:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"Deleted old file: {filename}")
                    except Exception as e:
                        logger.error(f"Error deleting file {filename}: {e}")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_files: {e}")
        return 0

def get_file_info(file_path: str) -> dict:
    """Get file information"""
    try:
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        stat_info = os.stat(file_path)
        return {
            "size": stat_info.st_size,
            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "extension": os.path.splitext(file_path)[1].lower(),
            "basename": os.path.basename(file_path)
        }
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        return {"error": str(e)}