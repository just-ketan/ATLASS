"""Object storage abstraction for ATLASS."""

import os
import shutil
from pathlib import Path


class ObjectStorage:
    """Simple local filesystem object storage for MVP."""

    def __init__(self, base_dir="data/objects"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_key(self, object_key: str) -> Path:
        normalized = os.path.normpath(object_key).lstrip(os.sep)
        if normalized == "." or normalized.startswith(".."):
            raise ValueError("object_key must stay within object storage")
        return self.base_dir / normalized

    def put_file(self, object_key: str, file_path: str | Path) -> str:
        """Upload a file to object storage."""
        dest_path = self._resolve_key(object_key)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest_path)
        return str(dest_path)

    def put_bytes(self, object_key: str, data: bytes) -> str:
        """Upload bytes to object storage."""
        dest_path = self._resolve_key(object_key)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)
        return str(dest_path)

    def get_file_path(self, object_key: str) -> str:
        """Get the local path for an object (only works for local filesystem storage)."""
        return str(self._resolve_key(object_key))
