import os
import re
import shutil
import time
from pathlib import Path
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from backend.config import (
    STORAGE_DRIVER,
    STORAGE_BUCKET_NAME,
    LOCAL_STORAGE_DIR,
    MAX_FILE_SIZE_MB,
    ALLOWED_EXTENSIONS
)

class CloudObjectStorageService:
    """
    Cloud Object Storage Service abstraction layer.
    
    In local development, it mimics AWS S3 / Google Cloud Storage / Firebase Storage
    by organizing files into hierarchical object keys within a simulated bucket:
    assignments/{assignment_id}/{student_id}/{unique_filename}
    
    Can be easily swapped with boto3 (AWS S3) or google-cloud-storage (GCS)
    without altering business logic in the controllers.
    """

    def __init__(self):
        self.driver = STORAGE_DRIVER
        self.bucket_name = STORAGE_BUCKET_NAME
        self.base_dir = Path(LOCAL_STORAGE_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """Sanitizes filename to prevent directory traversal and invalid characters."""
        clean = Path(filename).name
        clean = re.sub(r"[^\w\.-]", "_", clean)
        return clean or "submission_file"

    def validate_file(self, file: UploadFile, content: bytes) -> None:
        """Validates extension and file size against cloud security policies."""
        filename = file.filename or ""
        ext = filename.split(".")[-1].lower() if "." in filename else ""

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '.{ext}' is not permitted. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({size_mb:.2f} MB) exceeds maximum limit of {MAX_FILE_SIZE_MB} MB"
            )

    async def upload_file(
        self,
        file: UploadFile,
        assignment_id: str,
        student_id: str
    ) -> Tuple[str, str, int]:
        """
        Uploads an object into cloud storage.
        
        Returns:
            storage_path (key in bucket)
            file_url (accessible download URI)
            file_size_bytes
        """
        content = await file.read()
        self.validate_file(file, content)

        clean_filename = self.sanitize_filename(file.filename)
        timestamp = int(time.time())
        stored_filename = f"{timestamp}_{clean_filename}"

        # Cloud Object Key: assignments/<assignment_id>/<student_id>/<filename>
        storage_path = f"assignments/{assignment_id}/{student_id}/{stored_filename}"

        # Write to simulated cloud storage bucket
        target_file_path = self.base_dir / storage_path
        target_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_file_path, "wb") as f:
            f.write(content)

        file_size_bytes = len(content)
        file_url = f"/api/submissions/download-by-path?path={storage_path}"

        return storage_path, file_url, file_size_bytes

    def get_file_path(self, storage_path: str) -> Path:
        """Resolves object key to local filesystem path with path-traversal protection."""
        resolved = (self.base_dir / storage_path).resolve()
        # Security: Prevent path traversal outside storage bucket
        if not str(resolved).startswith(str(self.base_dir.resolve())):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: Invalid storage path reference"
            )
        if not resolved.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in object storage"
            )
        return resolved

    def delete_file(self, storage_path: str) -> bool:
        """Deletes object from storage."""
        try:
            target = self.get_file_path(storage_path)
            if target.is_file():
                target.unlink()
                return True
        except HTTPException:
            pass
        return False

# Global Singleton
storage_service = CloudObjectStorageService()
