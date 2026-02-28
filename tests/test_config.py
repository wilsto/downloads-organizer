from pathlib import Path
import pytest
import yaml

from organizer.config import load_config, Config


@pytest.fixture
def valid_config_file(tmp_path: Path) -> Path:
    config = {
        "source": str(tmp_path / "Downloads"),
        "archive_dir": str(tmp_path / "_Archive"),
        "destinations": {
            "Pro": str(tmp_path / "Pro"),
            "Perso": str(tmp_path / "Perso"),
            "Tech": str(tmp_path / "Tech"),
        },
        "dry_run": True,
        "log_file": str(tmp_path / "organizer.log"),
        "contexts": {
            "Pro": {
                "patterns": ["(?i)(powerbi|facture)"],
                "subfolders": ["Documents", "Presentations"],
            },
        },
        "type_mapping": {
            "Documents": ["pdf", "docx"],
            "Images": ["png", "jpg"],
        },
        "default_context": "Perso",
        "default_type": "Autres",
        "retention": {"Documents": 365, "Images": 180},
        "duplicates": {
            "enabled": True,
            "strategy": "delete",
            "pattern": r"\s*\(\d+\)(?=\.\w+$)",
        },
        "llm": {
            "enabled": False,
            "base_url": "http://localhost:11434",
            "model": "qwen3:14b",
            "cache_file": str(tmp_path / "cache.json"),
            "oneshot_keywords": ["installer"],
            "keeper_keywords": ["facture"],
        },
        "notification": {
            "enabled": False,
            "ha_url": "http://homeassistant.local:8123",
            "ha_token_env": "HA_TOKEN",
            "service": "notify/telegram",
        },
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.dump(config))
    return config_path


def test_load_valid_config(valid_config_file: Path):
    config = load_config(valid_config_file)
    assert isinstance(config, Config)
    assert config.dry_run is True
    assert config.default_context == "Perso"
    assert "Pro" in config.destinations
    assert config.retention["Documents"] == 365


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/config.yaml"))


def test_config_has_required_fields(valid_config_file: Path):
    config = load_config(valid_config_file)
    assert config.source
    assert config.archive_dir
    assert config.destinations
    assert config.contexts
    assert config.type_mapping
    assert config.duplicates
    assert config.llm
    assert config.notification


def test_config_invalid_yaml(tmp_path: Path):
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text(": invalid: yaml: [")
    with pytest.raises(Exception):
        load_config(bad_file)
