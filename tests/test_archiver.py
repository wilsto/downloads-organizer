import os
import time
from pathlib import Path

from organizer.archiver import Archiver, ArchiveResult


RETENTION = {
    "Executables": 3,
    "Documents": 365,
    "Code": 0,  # never archive
}


def _age_file(path: Path, days: int):
    """Set file modification time to `days` ago."""
    old_time = time.time() - (days * 86400)
    os.utime(path, (old_time, old_time))


def test_archive_old_executables(tmp_path: Path):
    archive_dir = tmp_path / "_Archive"
    source = tmp_path / "Tech" / "Executables"
    source.mkdir(parents=True)
    old_exe = source / "setup.exe"
    old_exe.write_text("x")
    _age_file(old_exe, 5)  # 5 days old, retention = 3

    archiver = Archiver(RETENTION, str(archive_dir), dry_run=False)
    result = archiver.process([tmp_path / "Tech"])

    assert result.archived == 1
    assert not old_exe.exists()
    # File moved to archive
    archived = list(archive_dir.rglob("setup.exe"))
    assert len(archived) == 1


def test_keep_recent_files(tmp_path: Path):
    archive_dir = tmp_path / "_Archive"
    source = tmp_path / "Pro" / "Executables"
    source.mkdir(parents=True)
    recent = source / "new_app.exe"
    recent.write_text("x")
    # File is fresh (just created), retention = 3 days

    archiver = Archiver(RETENTION, str(archive_dir), dry_run=False)
    result = archiver.process([tmp_path / "Pro"])

    assert result.archived == 0
    assert recent.exists()


def test_never_archive_code(tmp_path: Path):
    archive_dir = tmp_path / "_Archive"
    source = tmp_path / "Tech" / "Code"
    source.mkdir(parents=True)
    old_py = source / "script.py"
    old_py.write_text("x")
    _age_file(old_py, 999)

    archiver = Archiver(RETENTION, str(archive_dir), dry_run=False)
    result = archiver.process([tmp_path / "Tech"])

    assert result.archived == 0
    assert old_py.exists()


def test_dry_run_archives_nothing(tmp_path: Path):
    archive_dir = tmp_path / "_Archive"
    source = tmp_path / "Pro" / "Executables"
    source.mkdir(parents=True)
    old_exe = source / "old.exe"
    old_exe.write_text("x")
    _age_file(old_exe, 10)

    archiver = Archiver(RETENTION, str(archive_dir), dry_run=True)
    result = archiver.process([tmp_path / "Pro"])

    assert result.would_archive == 1
    assert result.archived == 0
    assert old_exe.exists()


def test_archive_organizes_by_month(tmp_path: Path):
    archive_dir = tmp_path / "_Archive"
    source = tmp_path / "Pro" / "Executables"
    source.mkdir(parents=True)
    old = source / "app.exe"
    old.write_text("x")
    _age_file(old, 30)

    archiver = Archiver(RETENTION, str(archive_dir), dry_run=False)
    archiver.process([tmp_path / "Pro"])

    # Should be in a YYYY-MM subfolder
    archived = list(archive_dir.rglob("app.exe"))
    assert len(archived) == 1
    # Parent should match YYYY-MM pattern
    parent_name = archived[0].parent.name
    assert len(parent_name) == 7  # "2025-01" format
    assert "-" in parent_name
