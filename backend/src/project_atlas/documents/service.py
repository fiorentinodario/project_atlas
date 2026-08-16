from pathlib import Path
from uuid import UUID

from flask import current_app
from sqlalchemy import select
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from project_atlas.documents.extractors import extract_text
from project_atlas.documents.storage import DocumentStorage
from project_atlas.errors import ApiError
from project_atlas.extensions import db
from project_atlas.models import ActivityLog, Document, Project, User
from project_atlas.models.enums import DocumentStatus, ProjectRole
from project_atlas.projects.service import accessible_project
from project_atlas.rag.indexing import index_document
from project_atlas.tasks.service import WRITE_ROLES

ALLOWED_TYPES = {
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
}


def serialize_document(document: Document) -> dict:
    return {
        "id": str(document.id),
        "project_id": str(document.project_id),
        "filename": document.filename,
        "mime_type": document.mime_type,
        "size_bytes": document.size_bytes,
        "status": document.status.value,
        "processing_error": document.processing_error,
        "indexed_at": document.indexed_at.isoformat() if document.indexed_at else None,
        "indexing_error": document.indexing_error,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
    }


def validate_upload(file: FileStorage | None) -> tuple[str, str]:
    if file is None or not file.filename:
        raise ApiError("FILE_REQUIRED", "A document file is required.", 422)
    filename = secure_filename(file.filename)
    if not filename:
        raise ApiError("INVALID_FILENAME", "The document filename is invalid.", 422)
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_TYPES or file.mimetype not in ALLOWED_TYPES[extension]:
        raise ApiError(
            "UNSUPPORTED_FILE_TYPE",
            "Only PDF, TXT and Markdown files are supported.",
            415,
        )
    if extension == ".pdf":
        header = file.stream.read(5)
        file.stream.seek(0)
        if header != b"%PDF-":
            raise ApiError("INVALID_PDF", "The uploaded file is not a valid PDF.", 422)
    return filename, extension


def list_documents(project_id: UUID, user_id: UUID) -> list[Document]:
    accessible_project(project_id, user_id)
    return list(
        db.session.scalars(
            select(Document)
            .where(Document.project_id == project_id)
            .order_by(Document.created_at.desc())
        )
    )


def create_document(project: Project, user: User, file: FileStorage) -> Document:
    filename, extension = validate_upload(file)
    file.stream.seek(0, 2)
    size_bytes = file.stream.tell()
    file.stream.seek(0)
    if size_bytes == 0:
        raise ApiError("EMPTY_FILE", "The uploaded document is empty.", 422)

    document = Document(
        project=project,
        uploaded_by=user,
        filename=filename,
        storage_path="pending",
        mime_type=file.mimetype,
        size_bytes=size_bytes,
    )
    db.session.add(document)
    db.session.flush()
    storage = DocumentStorage(current_app.config["UPLOAD_FOLDER"])
    try:
        document.storage_path = storage.save(file, project.id, document.id, extension)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    process_document(document, extension, storage)
    return document


def process_document(document: Document, extension: str, storage: DocumentStorage) -> None:
    document.status = DocumentStatus.PROCESSING
    db.session.commit()
    extraction_succeeded = False
    try:
        document.extracted_text = extract_text(
            storage.absolute_path(document.storage_path), extension
        )
        if not document.extracted_text:
            raise ValueError("No text could be extracted from the document")
        document.status = DocumentStatus.READY
        document.processing_error = None
        extraction_succeeded = True
    except Exception:
        current_app.logger.exception(
            "Document processing failed", extra={"document_id": document.id}
        )
        document.status = DocumentStatus.FAILED
        document.processing_error = "Text extraction failed. Check the document and try again."
    db.session.add(
        ActivityLog(
            project_id=document.project_id,
            actor_user_id=document.uploaded_by_id,
            action="DOCUMENT_UPLOADED",
            entity_type="document",
            entity_id=document.id,
            activity_metadata={"filename": document.filename, "status": document.status.value},
        )
    )
    db.session.commit()
    if extraction_succeeded:
        index_document(document, current_app.extensions["embedding_provider"])


def accessible_document(
    document_id: UUID, user_id: UUID, allowed_roles: set[ProjectRole] | None = None
) -> Document:
    document = db.session.get(Document, document_id)
    if document is None:
        raise ApiError("DOCUMENT_NOT_FOUND", "The requested document does not exist.", 404)
    accessible_project(document.project_id, user_id, allowed_roles)
    return document


def delete_document(document: Document, actor: User) -> None:
    storage = DocumentStorage(current_app.config["UPLOAD_FOLDER"])
    storage.delete(document.storage_path)
    db.session.add(
        ActivityLog(
            project_id=document.project_id,
            actor=actor,
            action="DOCUMENT_DELETED",
            entity_type="document",
            entity_id=document.id,
            activity_metadata={"filename": document.filename},
        )
    )
    db.session.delete(document)
    db.session.commit()


DOCUMENT_WRITE_ROLES = WRITE_ROLES
