from unittest.mock import AsyncMock, patch

from app.api.uploads import _safe_name, _upload_path
from app.rag.service import _prune_chroma
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_name_is_sanitized():
    assert _safe_name("My Notes.md") == "My_Notes.md"


def test_upload_rejects_executables():
    try:
        _safe_name("payload.exe")
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400


def test_list_uploads_includes_builtin_knowledge():
    response = client.get("/api/uploads")
    assert response.status_code == 200
    body = response.json()
    assert "uploads" in body
    assert "builtin" in body
    names = {item["name"] for item in body["builtin"]}
    assert "company_policy.md" in names
    assert "files" in body


def test_delete_rejects_path_escape():
    try:
        _upload_path("../secret")
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400


def test_delete_rejects_knowledge_path():
    try:
        _upload_path("knowledge/company_policy.md")
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400


def test_delete_missing_knowledge_file_from_uploads():
    response = client.delete("/api/uploads/company_policy.md")
    assert response.status_code == 404


@patch("app.api.uploads.ingest_knowledge", new_callable=AsyncMock)
def test_delete_upload_removes_file_from_list(mock_ingest):
    mock_ingest.return_value = {"status": "ok", "chunks": 1, "backend": "memory_keyword"}
    name = "zz_agentlens_delete_test.txt"
    response = client.post("/api/uploads", files={"file": (name, b"temporary sales notes", "text/plain")})
    assert response.status_code == 200
    listed = client.get("/api/uploads").json()
    assert any(item["name"] == name for item in listed["uploads"])
    deleted = client.delete(f"/api/uploads/{name}")
    assert deleted.status_code == 200
    listed = client.get("/api/uploads").json()
    assert all(item["name"] != name for item in listed["uploads"])


def test_prune_chroma_removes_stale_ids():
    class FakeCollection:
        def __init__(self):
            self.ids = ["keep-0", "gone-0"]
            self.deleted = []

        def get(self, include=None):
            return {"ids": list(self.ids)}

        def delete(self, ids):
            self.deleted = ids
            self.ids = [item for item in self.ids if item not in ids]

    collection = FakeCollection()
    assert _prune_chroma(collection, {"keep-0"}) == 1
    assert collection.deleted == ["gone-0"]


def test_read_builtin_knowledge_file():
    response = client.get("/api/files", params={"path": "knowledge/company_policy.md"})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "company_policy.md"
    assert body["source"] == "knowledge"
    assert body["content"]


def test_read_rejects_path_escape():
    response = client.get("/api/files", params={"path": "../backend/.env"})
    assert response.status_code == 400


def test_read_rejects_files_outside_knowledge_folders():
    response = client.get("/api/files", params={"path": "src/main.py"})
    assert response.status_code == 400


def test_read_missing_file_is_404():
    response = client.get("/api/files", params={"path": "uploads/not_here.md"})
    assert response.status_code == 404
