from pathlib import Path

import yaml
from pydantic import BaseModel


class DuplicatesConfig(BaseModel):
    enabled: bool = True
    strategy: str = "delete"
    pattern: str = r"\s*\(\d+\)(?=\.\w+$)"


class LlmConfig(BaseModel):
    enabled: bool = False
    base_url: str = "http://localhost:11434"
    model: str = "qwen3:14b"
    cache_file: str = ""
    oneshot_keywords: list[str] = []
    keeper_keywords: list[str] = []


class NotificationConfig(BaseModel):
    enabled: bool = False
    ha_url: str = "http://homeassistant.local:8123"
    ha_token_env: str = "HA_TOKEN"
    service: str = "script/notify_engine"
    who: str = "will"


class ContextConfig(BaseModel):
    patterns: list[str]
    subfolders: list[str]


class Config(BaseModel):
    source: str
    archive_dir: str
    destinations: dict[str, str]
    dry_run: bool = False
    log_file: str = "organizer.log"
    contexts: dict[str, ContextConfig]
    type_mapping: dict[str, list[str]]
    default_context: str = "Perso"
    default_type: str = "Autres"
    retention: dict[str, int]
    duplicates: DuplicatesConfig
    llm: LlmConfig
    notification: NotificationConfig


def load_config(path: Path) -> Config:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Config(**raw)
