import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from organizer.llm_classifier import LlmClassifier, FileClassification
from organizer.scanner import FileInfo
from organizer.config import LlmConfig


def make_file_info(name: str = "test.pdf", size: int = 1024) -> FileInfo:
    return FileInfo(
        path=Path(f"/tmp/{name}"),
        name=name,
        extension=Path(name).suffix,
        size=size,
        modified=datetime(2025, 6, 15),
        mime_type="application/pdf",
    )


def make_classifier(tmp_path: Path, enabled: bool = True) -> LlmClassifier:
    config = LlmConfig(
        enabled=enabled,
        base_url="http://localhost:11434",
        model="qwen3:14b",
        cache_file=str(tmp_path / "cache.json"),
        oneshot_keywords=["installer", "setup"],
        keeper_keywords=["facture", "devis", "contrat"],
    )
    return LlmClassifier(config)


def test_classify_returns_file_classification(tmp_path: Path):
    classifier = make_classifier(tmp_path)
    mock_response = {
        "message": {
            "content": json.dumps(
                {
                    "context": "Pro",
                    "file_type": "Documents",
                    "durability": "KEEPER",
                    "confidence": 0.95,
                }
            )
        }
    }
    with patch("organizer.llm_classifier.Client") as MockClient:
        instance = MockClient.return_value
        instance.chat.return_value = mock_response
        result = classifier.classify(make_file_info("facture_2025.pdf"))

    assert isinstance(result, FileClassification)
    assert result.context == "Pro"
    assert result.durability == "KEEPER"


def test_cache_prevents_duplicate_calls(tmp_path: Path):
    classifier = make_classifier(tmp_path)
    mock_response = {
        "message": {
            "content": json.dumps(
                {
                    "context": "Perso",
                    "file_type": "Images",
                    "durability": "KEEPER",
                    "confidence": 0.8,
                }
            )
        }
    }
    with patch("organizer.llm_classifier.Client") as MockClient:
        instance = MockClient.return_value
        instance.chat.return_value = mock_response
        result1 = classifier.classify(make_file_info("photo.png"))
        result2 = classifier.classify(make_file_info("photo.png"))
        # Only one call to Ollama
        assert instance.chat.call_count == 1

    assert result1.context == result2.context


def test_disabled_returns_none(tmp_path: Path):
    classifier = make_classifier(tmp_path, enabled=False)
    result = classifier.classify(make_file_info())
    assert result is None


def test_ollama_unavailable_returns_none(tmp_path: Path):
    classifier = make_classifier(tmp_path)
    with patch("organizer.llm_classifier.Client") as MockClient:
        instance = MockClient.return_value
        instance.chat.side_effect = Exception("Connection refused")
        result = classifier.classify(make_file_info())

    assert result is None


def test_cache_persists_to_disk(tmp_path: Path):
    classifier = make_classifier(tmp_path)
    mock_response = {
        "message": {
            "content": json.dumps(
                {
                    "context": "Tech",
                    "file_type": "Code",
                    "durability": "KEEPER",
                    "confidence": 0.9,
                }
            )
        }
    }
    with patch("organizer.llm_classifier.Client") as MockClient:
        instance = MockClient.return_value
        instance.chat.return_value = mock_response
        classifier.classify(make_file_info("script.py"))
        classifier.save_cache()

    cache_path = tmp_path / "cache.json"
    assert cache_path.exists()
    cache_data = json.loads(cache_path.read_text())
    assert len(cache_data) == 1


def test_invalid_json_response_returns_none(tmp_path: Path):
    classifier = make_classifier(tmp_path)
    mock_response = {"message": {"content": "this is not valid json at all"}}
    with patch("organizer.llm_classifier.Client") as MockClient:
        instance = MockClient.return_value
        instance.chat.return_value = mock_response
        result = classifier.classify(make_file_info())

    assert result is None
