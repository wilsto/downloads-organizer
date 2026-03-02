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
    def __init__(
        self, config: DuplicatesConfig, dry_run: bool = False, verbose: bool = False
    ):
        self._config = config
        self._dry_run = dry_run
        self._verbose = verbose
        self._pattern = re.compile(config.pattern) if config.enabled else None

    def process(self, directory: Path, limit: int = 0) -> DedupResult:
        result = DedupResult()
        if not self._config.enabled:
            result.skipped = True
            return result

        copies = self._find_copies(directory)
        if limit > 0:
            copies = copies[:limit]

        deleted_examples: list[str] = []
        renamed_examples: list[str] = []

        for copy_path, original_path in copies:
            if not original_path.exists():
                continue
            self._process_pair(
                copy_path, original_path, result, deleted_examples, renamed_examples
            )

        if not self._verbose:
            self._log_summary(result, deleted_examples, renamed_examples)

        return result

    def _process_pair(
        self,
        copy_path: Path,
        original_path: Path,
        result: DedupResult,
        deleted_examples: list[str],
        renamed_examples: list[str],
    ) -> None:
        is_exact_duplicate = _sha256(copy_path) == _sha256(original_path)

        if is_exact_duplicate:
            self._handle_duplicate(copy_path, result, deleted_examples)
        else:
            self._handle_content_differs(copy_path, original_path, result, renamed_examples)

    def _handle_duplicate(
        self, copy_path: Path, result: DedupResult, examples: list[str]
    ) -> None:
        if self._dry_run:
            result.would_delete += 1
            label = "[DRY-RUN] Would delete duplicate: %s"
        else:
            copy_path.unlink()
            result.deleted += 1
            label = "Deleted duplicate: %s"

        if self._verbose:
            logger.info(label, copy_path.name)
        else:
            examples.append(copy_path.name)

    def _handle_content_differs(
        self,
        copy_path: Path,
        original_path: Path,
        result: DedupResult,
        examples: list[str],
    ) -> None:
        new_name = self._generate_unique_name(original_path, copy_path)

        if not self._dry_run:
            copy_path.rename(copy_path.parent / new_name)

        prefix = "[DRY-RUN] " if self._dry_run else ""
        if self._verbose:
            logger.info("%sRenamed %s → %s", prefix, copy_path.name, new_name)
        else:
            examples.append(f"{copy_path.name} → {new_name}")
        result.renamed += 1

    def _log_summary(
        self,
        result: DedupResult,
        deleted_examples: list[str],
        renamed_examples: list[str],
    ) -> None:
        max_examples = 5
        prefix = "[DRY-RUN] " if self._dry_run else ""
        count_deleted = result.would_delete if self._dry_run else result.deleted

        if count_deleted > 0:
            verb = "Would delete" if self._dry_run else "Deleted"
            logger.info("%s%s %d duplicates", prefix, verb, count_deleted)
            for name in deleted_examples[:max_examples]:
                logger.info("  - %s", name)
            remaining = count_deleted - max_examples
            if remaining > 0:
                logger.info("  ... and %d more", remaining)

        if result.renamed > 0:
            verb = "Would rename" if self._dry_run else "Renamed"
            logger.info("%s%s %d files", prefix, verb, result.renamed)
            for desc in renamed_examples[:max_examples]:
                logger.info("  - %s", desc)
            remaining = result.renamed - max_examples
            if remaining > 0:
                logger.info("  ... and %d more", remaining)

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
