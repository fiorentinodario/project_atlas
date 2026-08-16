from io import BytesIO
from pathlib import Path

from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import select

from project_atlas.extensions import db
from project_atlas.models import Document, DocumentChunk, Project, ProjectMember, User
from project_atlas.models.enums import DocumentStatus, ProjectRole


def account(client: FlaskClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": email.split("@")[0].title(),
            "email": email,
            "password": "securepass123",
        },
    )
    return response.get_json()["data"]["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def project(client: FlaskClient, token: str) -> str:
    response = client.post(
        "/api/v1/projects",
        json={"name": "Document project"},
        headers=auth(token),
    )
    return response.get_json()["data"]["project"]["id"]


def upload(client: FlaskClient, project_id: str, token: str, content: bytes, filename: str):
    mime_type = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".csv": "text/csv",
    }[Path(filename).suffix.lower()]
    return client.post(
        f"/api/v1/projects/{project_id}/documents",
        data={"file": (BytesIO(content), filename, mime_type)},
        headers=auth(token),
        content_type="multipart/form-data",
    )


def test_text_upload_is_stored_and_processed(app: Flask, client: FlaskClient) -> None:
    token = account(client, "owner@example.com")
    project_id = project(client, token)

    response = upload(
        client,
        project_id,
        token,
        b"Project Atlas requirements\nAuthentication is required.",
        "requirements.txt",
    )

    assert response.status_code == 201
    payload = response.get_json()["data"]["document"]
    assert payload["status"] == "READY"
    assert payload["filename"] == "requirements.txt"
    with app.app_context():
        document = db.session.scalar(select(Document))
        assert document is not None
        assert "Authentication is required" in document.extracted_text
        assert document.indexed_at is None
        assert document.indexing_error == "Embedding provider is not configured."
        assert db.session.scalar(select(DocumentChunk)) is not None
        assert Path(app.config["UPLOAD_FOLDER"], document.storage_path).is_file()


def test_unsupported_extension_is_rejected(client: FlaskClient) -> None:
    token = account(client, "owner@example.com")
    project_id = project(client, token)

    response = upload(client, project_id, token, b"spreadsheet", "budget.csv")

    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_fake_pdf_is_rejected_before_storage(client: FlaskClient) -> None:
    token = account(client, "owner@example.com")
    project_id = project(client, token)

    response = upload(client, project_id, token, b"not a pdf", "brief.pdf")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "INVALID_PDF"


def test_malformed_pdf_is_recorded_as_failed(app: Flask, client: FlaskClient) -> None:
    token = account(client, "owner@example.com")
    project_id = project(client, token)

    response = upload(client, project_id, token, b"%PDF-malformed", "broken.pdf")

    assert response.status_code == 201
    assert response.get_json()["data"]["document"]["status"] == "FAILED"
    with app.app_context():
        document = db.session.scalar(select(Document))
        assert document.status is DocumentStatus.FAILED
        assert document.processing_error is not None


def test_viewer_can_list_but_cannot_upload(app: Flask, client: FlaskClient) -> None:
    owner_token = account(client, "owner@example.com")
    viewer_token = account(client, "viewer@example.com")
    project_id = project(client, owner_token)
    with app.app_context():
        project_record = db.session.scalar(select(Project))
        viewer = db.session.scalar(select(User).where(User.email == "viewer@example.com"))
        db.session.add(ProjectMember(project=project_record, user=viewer, role=ProjectRole.VIEWER))
        db.session.commit()

    listing = client.get(f"/api/v1/projects/{project_id}/documents", headers=auth(viewer_token))
    uploading = upload(client, project_id, viewer_token, b"notes", "notes.txt")

    assert listing.status_code == 200
    assert uploading.status_code == 403


def test_delete_removes_metadata_and_file(app: Flask, client: FlaskClient) -> None:
    token = account(client, "owner@example.com")
    project_id = project(client, token)
    created = upload(client, project_id, token, b"temporary", "temporary.md")
    document_id = created.get_json()["data"]["document"]["id"]
    with app.app_context():
        document = db.session.scalar(select(Document))
        stored_path = Path(app.config["UPLOAD_FOLDER"], document.storage_path)
        assert stored_path.exists()

    response = client.delete(f"/api/v1/documents/{document_id}", headers=auth(token))

    assert response.status_code == 204
    assert not stored_path.exists()
    with app.app_context():
        assert db.session.scalar(select(Document)) is None
