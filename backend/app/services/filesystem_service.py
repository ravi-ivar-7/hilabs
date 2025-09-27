import os
import shutil
from pathlib import Path
from typing import Optional
from ..core.config import get_settings


class FileSystemService:
    def __init__(self):
        settings = get_settings()
        # Use project root upload directory
        self.base_path = Path(__file__).parent.parent.parent.parent / "upload"
        self.base_path.mkdir(exist_ok=True)
        
        # Ensure state directories exist
        for state in ["contracts-tn", "contracts-wa"]:
            state_dir = self.base_path / state
            state_dir.mkdir(exist_ok=True)
    
    def upload_file(self, bucket_name: str, object_name: str, data: bytes) -> bool:
        try:
            file_path = self.base_path / bucket_name / object_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(data)
            return True
        except Exception:
            return False
    
    def download_file(self, bucket_name: str, object_name: str) -> Optional[bytes]:
        try:
            file_path = self.base_path / bucket_name / object_name
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    return f.read()
            return None
        except Exception:
            return None
    
    def delete_file(self, bucket_name: str, object_name: str) -> bool:
        try:
            file_path = self.base_path / bucket_name / object_name
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def file_exists(self, bucket_name: str, object_name: str) -> bool:
        try:
            file_path = self.base_path / bucket_name / object_name
            return file_path.exists()
        except Exception:
            return False
    
    def get_file_path(self, bucket_name: str, object_name: str) -> Path:
        return self.base_path / bucket_name / object_name
    
    def get_file_size(self, bucket_name: str, object_name: str) -> Optional[int]:
        try:
            file_path = self.base_path / bucket_name / object_name
            if file_path.exists():
                return file_path.stat().st_size
            return None
        except Exception:
            return None
