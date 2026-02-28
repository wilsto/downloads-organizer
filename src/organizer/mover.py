import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from organizer.classifier import Classification

logger = logging.getLogger("organizer")


@dataclass
class MoveResult:
    source: Path
    destination: Path | None = None
    success: bool = False
    dry_run: bool = False
    error: str | None = None


class FileMover:
    def __init__(self, destinations: dict[str, str], dry_run: bool = False):
        self._destinations = destinations
        self._dry_run = dry_run

    def move(self, file_path: Path, classification: Classification) -> MoveResult:
        base_dir = self._destinations.get(classification.context)
        if not base_dir:
            return MoveResult(
                source=file_path,
                error=f"No destination for context: {classification.context}",
            )

        target_dir = Path(base_dir) / classification.file_type
        target_file = target_dir / file_path.name

        if self._dry_run:
            logger.info("[DRY-RUN] Would move %s → %s", file_path.name, target_file)
            return MoveResult(
                source=file_path, destination=target_file, dry_run=True, success=False
            )

        target_dir.mkdir(parents=True, exist_ok=True)

        if target_file.exists():
            target_file = self._resolve_conflict(target_file)

        shutil.move(str(file_path), str(target_file))
        logger.info("Moved %s → %s", file_path.name, target_file)
        return MoveResult(source=file_path, destination=target_file, success=True)

    def move_batch(
        self, items: list[tuple[Path, Classification]]
    ) -> list[MoveResult]:
        return [self.move(path, cls) for path, cls in items]

    def _resolve_conflict(self, target: Path) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{target.stem}_{timestamp}{target.suffix}"
        return target.parent / new_name
