from pathlib import Path

from organizer.scanner import scan_directory, FileInfo


def test_scan_finds_root_files(tmp_path: Path):
    (tmp_path / "doc.pdf").write_text("hello")
    (tmp_path / "img.png").write_bytes(b"\x89PNG")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.txt").write_text("nested")

    files = scan_directory(tmp_path)
    names = [f.name for f in files]
    assert "doc.pdf" in names
    assert "img.png" in names
    # Only root-level files, not nested
    assert "nested.txt" not in names


def test_scan_returns_file_info(tmp_path: Path):
    (tmp_path / "test.pdf").write_text("content")
    files = scan_directory(tmp_path)
    assert len(files) == 1
    info = files[0]
    assert isinstance(info, FileInfo)
    assert info.name == "test.pdf"
    assert info.extension == ".pdf"
    assert info.size > 0
    assert info.path == tmp_path / "test.pdf"


def test_scan_empty_directory(tmp_path: Path):
    files = scan_directory(tmp_path)
    assert files == []


def test_scan_ignores_directories(tmp_path: Path):
    (tmp_path / "folder").mkdir()
    (tmp_path / "file.txt").write_text("x")
    files = scan_directory(tmp_path)
    assert len(files) == 1
    assert files[0].name == "file.txt"
