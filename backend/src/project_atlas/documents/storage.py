from pathlib import Path
from uuid import UUID

from werkzeug.datastructures import FileStorage


class DocumentStorage:
    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()

    def save(self, file: FileStorage, project_id: UUID, document_id: UUID, extension: str) -> str:
        relative_path = Path(str(project_id)) / f"{document_id}{extension}"
        destination = (self.root / relative_path).resolve()
        if self.root not in destination.parents:
            raise ValueError("Invalid document storage path")
        destination.parent.mkdir(parents=True, exist_ok=True)
        file.save(destination)
        return relative_path.as_posix()

    def absolute_path(self, relative_path: str) -> Path:
        path = (self.root / relative_path).resolve()
        if self.root not in path.parents:
            raise ValueError("Invalid document storage path")
        return path

    def delete(self, relative_path: str) -> None:
        path = self.absolute_path(relative_path)
        if path.exists():
            path.unlink()
        try:
            path.parent.rmdir()
        except OSError:
            pass
