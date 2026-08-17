from app.api.uploads import _safe_name
from fastapi import HTTPException


def test_upload_name_is_sanitized():
    assert _safe_name("My Notes.md") == "My_Notes.md"


def test_upload_rejects_executables():
    try:
        _safe_name("payload.exe")
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400
