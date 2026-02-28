from pathlib import Path

from organizer.mover import FileMover, MoveResult
from organizer.classifier import Classification


def test_move_file_to_destination(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    dest = tmp_path / "dest"
    (source / "facture.pdf").write_text("content")

    destinations = {"Pro": str(dest / "Pro"), "Perso": str(dest / "Perso")}
    mover = FileMover(destinations, dry_run=False)
    classification = Classification(context="Pro", file_type="Documents", matched_by="regex")

    result = mover.move(source / "facture.pdf", classification)
    assert result.success
    assert (dest / "Pro" / "Documents" / "facture.pdf").exists()
    assert not (source / "facture.pdf").exists()


def test_move_creates_directories(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    dest = tmp_path / "dest"
    (source / "photo.png").write_text("img")

    destinations = {"Perso": str(dest / "Perso")}
    mover = FileMover(destinations, dry_run=False)
    classification = Classification(context="Perso", file_type="Images", matched_by="regex")

    result = mover.move(source / "photo.png", classification)
    assert result.success
    assert (dest / "Perso" / "Images" / "photo.png").exists()


def test_move_handles_name_conflict(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    dest = tmp_path / "dest" / "Pro" / "Documents"
    dest.mkdir(parents=True)
    (source / "report.pdf").write_text("new version")
    (dest / "report.pdf").write_text("existing")

    destinations = {"Pro": str(tmp_path / "dest" / "Pro")}
    mover = FileMover(destinations, dry_run=False)
    classification = Classification(context="Pro", file_type="Documents", matched_by="regex")

    result = mover.move(source / "report.pdf", classification)
    assert result.success
    # Original still exists
    assert (dest / "report.pdf").exists()
    # New file got a timestamp suffix
    files = list(dest.glob("report_*.pdf"))
    assert len(files) == 1


def test_dry_run_moves_nothing(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "file.txt").write_text("x")

    destinations = {"Perso": str(tmp_path / "dest" / "Perso")}
    mover = FileMover(destinations, dry_run=True)
    classification = Classification(context="Perso", file_type="Documents", matched_by="default")

    result = mover.move(source / "file.txt", classification)
    assert result.dry_run
    assert (source / "file.txt").exists()


def test_move_batch(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    for i in range(3):
        (source / f"file{i}.pdf").write_text(f"content{i}")

    destinations = {"Perso": str(tmp_path / "dest" / "Perso")}
    mover = FileMover(destinations, dry_run=False)

    moves = [
        (source / f"file{i}.pdf", Classification("Perso", "Documents", "default"))
        for i in range(3)
    ]
    results = mover.move_batch(moves)
    assert len(results) == 3
    assert all(r.success for r in results)
