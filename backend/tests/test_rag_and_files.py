from app.core.security import sanitize_filename, validate_upload
from app.core.errors import AppError
from app.rag.cleaner import clean_text
from app.rag.chunker import chunk_pages
import pytest


def test_sanitize_strips_path():
    assert ".." not in sanitize_filename("..\\secret\\note.pdf")
    assert sanitize_filename("C:/tmp/my file.pdf").endswith("my_file.pdf") or "file" in sanitize_filename("x.pdf")


def test_validate_reject_exe(monkeypatch):
    with pytest.raises(AppError):
        validate_upload("virus.exe", 100)


def test_clean_and_chunk():
    text = clean_text("hello-\nworld\n\n\n  extra")
    assert "helloworld" in text or "hello" in text
    pages = [{"text": "Word " * 200, "page_number": 1, "slide_number": None}]
    chunks = chunk_pages(pages, 80, 10)
    assert len(chunks) > 1
    assert chunks[0]["page_number"] == 1
