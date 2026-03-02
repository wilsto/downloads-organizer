from pathlib import Path

from organizer.deduplicator import Deduplicator, DedupResult
from organizer.config import DuplicatesConfig


def make_dedup(dry_run: bool = False) -> Deduplicator:
    config = DuplicatesConfig(
        enabled=True, strategy="delete", pattern=r"\s*\(\d+\)(?=\.\w+$)"
    )
    return Deduplicator(config, dry_run=dry_run)


def test_detect_duplicate_pattern(tmp_path: Path):
    original = tmp_path / "report.pdf"
    copy = tmp_path / "report (1).pdf"
    original.write_text("same content")
    copy.write_text("same content")

    dedup = make_dedup()
    result = dedup.process(tmp_path)
    assert result.deleted == 1
    assert original.exists()
    assert not copy.exists()


def test_keep_both_when_content_differs(tmp_path: Path):
    original = tmp_path / "report.pdf"
    copy = tmp_path / "report (1).pdf"
    original.write_text("version 1")
    copy.write_text("version 2 - different")

    dedup = make_dedup()
    result = dedup.process(tmp_path)
    assert result.deleted == 0
    assert result.renamed == 1
    assert original.exists()
    # Copy should be renamed (no longer has (1))
    assert not copy.exists()


def test_dry_run_deletes_nothing(tmp_path: Path):
    original = tmp_path / "file.txt"
    copy = tmp_path / "file (1).txt"
    original.write_text("same")
    copy.write_text("same")

    dedup = make_dedup(dry_run=True)
    result = dedup.process(tmp_path)
    assert result.deleted == 0
    assert result.would_delete == 1
    assert copy.exists()


def test_multiple_copies(tmp_path: Path):
    original = tmp_path / "doc.pdf"
    copy1 = tmp_path / "doc (1).pdf"
    copy2 = tmp_path / "doc (2).pdf"
    original.write_text("same content")
    copy1.write_text("same content")
    copy2.write_text("same content")

    dedup = make_dedup()
    result = dedup.process(tmp_path)
    assert result.deleted == 2
    assert original.exists()


def test_no_duplicates(tmp_path: Path):
    (tmp_path / "a.txt").write_text("aaa")
    (tmp_path / "b.txt").write_text("bbb")

    dedup = make_dedup()
    result = dedup.process(tmp_path)
    assert result.deleted == 0
    assert result.renamed == 0


def test_disabled_dedup(tmp_path: Path):
    config = DuplicatesConfig(enabled=False)
    dedup = Deduplicator(config, dry_run=False)
    (tmp_path / "file.txt").write_text("x")
    (tmp_path / "file (1).txt").write_text("x")
    result = dedup.process(tmp_path)
    assert result.deleted == 0
    assert result.skipped is True


def test_process_respects_limit(tmp_path: Path):
    """With 5 duplicate pairs and limit=2, only 2 should be processed."""
    for i in range(5):
        name = f"file{i}"
        (tmp_path / f"{name}.txt").write_text("same")
        (tmp_path / f"{name} (1).txt").write_text("same")

    dedup = make_dedup()
    result = dedup.process(tmp_path, limit=2)
    assert result.deleted == 2


def test_process_limit_zero_processes_all(tmp_path: Path):
    """limit=0 means no limit — all duplicates should be processed."""
    for i in range(5):
        name = f"file{i}"
        (tmp_path / f"{name}.txt").write_text("same")
        (tmp_path / f"{name} (1).txt").write_text("same")

    dedup = make_dedup()
    result = dedup.process(tmp_path, limit=0)
    assert result.deleted == 5
