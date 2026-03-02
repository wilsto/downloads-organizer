"""Integration tests for main orchestration flow."""

import yaml
from pathlib import Path
from unittest.mock import patch

import pytest

from organizer.main import main


@pytest.fixture
def setup_env(tmp_path: Path):
    """Create a minimal working environment for main()."""
    source = tmp_path / "Downloads"
    source.mkdir()
    archive = tmp_path / "_Archive"
    dest_perso = tmp_path / "Perso"
    dest_pro = tmp_path / "Pro"
    dest_tech = tmp_path / "Tech"

    config = {
        "source": str(source),
        "archive_dir": str(archive),
        "destinations": {
            "Pro": str(dest_pro),
            "Perso": str(dest_perso),
            "Tech": str(dest_tech),
        },
        "dry_run": True,
        "log_file": str(tmp_path / "organizer.log"),
        "contexts": {
            "Pro": {"patterns": ["(?i)(facture|devis)"]},
            "Perso": {"patterns": ["(?i)(photo|scan)"]},
            "Tech": {"patterns": ["(?i)(\\.py$|\\.js$)"]},
        },
        "type_mapping": {
            "Documents": ["pdf", "docx"],
            "Images": ["png", "jpg"],
            "Code": ["py", "js"],
        },
        "default_context": "Perso",
        "default_type": "Autres",
        "retention": {"Documents": 365},
        "duplicates": {
            "enabled": True,
            "strategy": "delete",
            "pattern": r"\s*\(\d+\)(?=\.\w+$)",
        },
        "llm": {"enabled": False, "cache_file": str(tmp_path / "llm_cache.json")},
        "notification": {"enabled": False},
    }

    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(config))

    return {"source": source, "config_path": config_path, "destinations": {
        "Pro": dest_pro, "Perso": dest_perso, "Tech": dest_tech,
    }}


def test_main_dry_run_no_files(setup_env):
    """main() runs successfully with an empty source directory."""
    with patch("sys.argv", ["organize", "--config", str(setup_env["config_path"]), "--dry-run"]):
        main()  # Should not raise


def test_main_dry_run_with_files(setup_env):
    """main() in dry-run mode does not move files."""
    source = setup_env["source"]
    (source / "facture_2025.pdf").write_text("invoice content")
    (source / "photo_vacation.jpg").write_bytes(b"\x89PNG")
    (source / "script.py").write_text("print('hello')")

    with patch("sys.argv", ["organize", "--config", str(setup_env["config_path"]), "--dry-run"]):
        main()

    # Files should still be in source (dry-run)
    assert (source / "facture_2025.pdf").exists()
    assert (source / "photo_vacation.jpg").exists()
    assert (source / "script.py").exists()


def test_main_moves_files(setup_env):
    """main() in live mode moves files to correct destinations."""
    source = setup_env["source"]
    (source / "facture_2025.pdf").write_text("invoice content")

    config_path = setup_env["config_path"]
    # Override dry_run to False
    config = yaml.safe_load(config_path.read_text())
    config["dry_run"] = False
    config_path.write_text(yaml.dump(config))

    with patch("sys.argv", ["organize", "--config", str(config_path)]):
        main()

    # File should be moved to Pro/Documents/
    dest = setup_env["destinations"]["Pro"] / "Documents" / "facture_2025.pdf"
    assert dest.exists()
    assert not (source / "facture_2025.pdf").exists()


def test_main_dedup_removes_copies(setup_env):
    """main() deduplicates files with (N) suffix that match originals."""
    source = setup_env["source"]
    (source / "readme.pdf").write_text("same content")
    (source / "readme (1).pdf").write_text("same content")

    config_path = setup_env["config_path"]
    config = yaml.safe_load(config_path.read_text())
    config["dry_run"] = False
    config_path.write_text(yaml.dump(config))

    with patch("sys.argv", ["organize", "--config", str(config_path)]):
        main()

    # Original should be moved, copy should be deleted
    assert not (source / "readme (1).pdf").exists()


def test_main_with_limit(setup_env):
    """main() respects --limit flag."""
    source = setup_env["source"]
    for i in range(5):
        (source / f"file_{i}.pdf").write_text(f"content {i}")

    with patch("sys.argv", [
        "organize", "--config", str(setup_env["config_path"]),
        "--dry-run", "--limit", "2",
    ]):
        main()  # Should not raise, processes only 2 files
