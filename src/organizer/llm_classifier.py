import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

from ollama import Client

from organizer.config import LlmConfig
from organizer.scanner import FileInfo

logger = logging.getLogger("organizer")

SYSTEM_PROMPT = """/no_think
Tu es un expert en organisation de fichiers. Classifie ce fichier.

Contextes possibles : Pro (travail), Perso (personnel/admin), Tech (dev/homelab)
Durabilité : KEEPER (document à conserver : facture, devis, contrat, photo perso, CV)
             ou ONE-SHOT (temporaire : installer, setup, guide, changelog, cache)

Réponds UNIQUEMENT avec un objet JSON, sans texte avant ou après :
{"context": "Pro|Perso|Tech", "file_type": "Documents|Images|Presentations|Spreadsheets|Archives|Executables|Media|Code|Data|Autres", "durability": "KEEPER|ONE-SHOT", "confidence": 0.0-1.0}"""


@dataclass
class FileClassification:
    context: str
    file_type: str
    durability: str
    confidence: float


class LlmClassifier:
    def __init__(self, config: LlmConfig):
        self._config = config
        self._cache: dict[str, dict] = {}
        self._load_cache()

    def classify(self, file_info: FileInfo) -> FileClassification | None:
        if not self._config.enabled:
            return None

        cache_key = f"{file_info.name}|{file_info.size}"
        if cache_key in self._cache:
            return FileClassification(**self._cache[cache_key])

        try:
            client = Client(host=self._config.base_url)
            user_prompt = (
                f"Fichier : {file_info.name}\n"
                f"Taille : {_human_size(file_info.size)}\n"
                f"Date : {file_info.modified.strftime('%Y-%m-%d')}\n"
                f"Type MIME : {file_info.mime_type or 'inconnu'}"
            )
            response = client.chat(
                model=self._config.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                options={"temperature": 0},
            )
            content = response["message"]["content"]
            content = _extract_json(content)
            data = json.loads(content)
            result = FileClassification(
                context=data["context"],
                file_type=data["file_type"],
                durability=data["durability"],
                confidence=float(data["confidence"]),
            )
            self._cache[cache_key] = asdict(result)
            return result
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("LLM returned invalid JSON for %s: %s", file_info.name, e)
            return None
        except Exception as e:
            logger.warning("Ollama unavailable for %s: %s", file_info.name, e)
            return None

    def save_cache(self) -> None:
        cache_path = Path(self._config.cache_file)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2))

    def _load_cache(self) -> None:
        cache_path = Path(self._config.cache_file)
        if cache_path.exists():
            try:
                self._cache = json.loads(cache_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._cache = {}


def _extract_json(text: str) -> str:
    """Extract JSON from LLM response, stripping think tags, code fences, etc."""
    import re as _re

    # Strip <think>...</think> blocks (Qwen3 thinking mode)
    text = _re.sub(r"<think>.*?</think>", "", text, flags=_re.DOTALL)
    text = text.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    text = text.strip()
    # Try to find JSON object in text
    match = _re.search(r"\{[^{}]*\}", text)
    if match:
        return match.group(0)
    return text


def _human_size(size_bytes: int) -> str:
    for unit in ("o", "Ko", "Mo", "Go"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} To"
