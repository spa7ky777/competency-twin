from pathlib import Path

from app.rag.extractors import extract_file


def test_txt_extract(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("hello clustering", encoding="utf-8")
    pages = extract_file(p, "txt")
    assert "clustering" in pages[0]["text"]
