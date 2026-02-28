import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from organizer.config import DuplicatesConfig

logger = logging.getLogger("organizer")


@dataclass
class DedupResult:
    deleted: int = 0
    renamed: int = 0
    would_delete: int = 0
    skipped: bool = False
    errors: list[str] = field(default_factory=list)


class Deduplicator:
    def __init__(self, config: DuplicatesConfig, dry_run: bool = False):
        self._config = config
        self._dry_run = dry_run
        self._pattern = re.compile(config.pattern) if config.enabled else None

    def process(self, directory: Path) -> DedupResult:
        result = DedupResult()
        if not self._config.enabled:
            result.skipped = True
            return result

        copies = self._find_copies(directory)
        for copy_path, original_path in copies:
            if not original_path.exists():
                continue
            copy_hash = _sha256(copy_path)
            original_hash = _sha256(original_path)

            if copy_hash == original_hash:
                if self._dry_run:
                    result.would_delete += 1
                    logger.info("[DRY-RUN] Would delete duplicate: %s", copy_path.name)
                else:
                    copy_path.unlink()
                    result.deleted += 1
                    logger.info("Deleted duplicate: %s", copy_path.name)
            else:
                # Content differs — rename the copy to remove the (N) suffix
                new_name = self._generate_unique_name(original_path, copy_path)
                if self._dry_run:
                    logger.info(
                        "[DRY-RUN] Would rename %s → %s", copy_path.name, new_name
                    )
                else:
                    copy_path.rename(copy_path.parent / new_name)
                    logger.info("Renamed %s → %s", copy_path.name, new_name)
                result.renamed += 1

        return result

    def _find_copies(self, directory: Path) -> list[tuple[Path, Path]]:
        pairs = []
        for file in directory.iterdir():
            if not file.is_file():
                continue
            match = self._pattern.search(file.name)
            if match:
                original_name = (
                    file.name[: match.start()] + file.name[match.end() :]
                )
                original_path = directory / original_name
                pairs.append((file, original_path))
        return pairs

    def _generate_unique_name(self, original: Path, copy: Path) -> str:
        stem = original.stem
        suffix = original.suffix
        counter = 2
        while True:
            candidate = f"{stem}_v{counter}{suffix}"
            if not (copy.parent / candidate).exists():
                return candidate
            counter += 1


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
