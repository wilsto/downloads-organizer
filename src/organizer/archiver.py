import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("organizer")


@dataclass
class ArchiveResult:
    archived: int = 0
    would_archive: int = 0
    skipped: int = 0


class Archiver:
    def __init__(
        self, retention: dict[str, int], archive_dir: str, dry_run: bool = False
    ):
        self._retention = retention
        self._archive_dir = Path(archive_dir)
        self._dry_run = dry_run

    def process(self, organized_dirs: list[Path]) -> ArchiveResult:
        result = ArchiveResult()
        now = datetime.now()

        for base_dir in organized_dirs:
            if not base_dir.exists():
                continue
            for type_dir in base_dir.iterdir():
                if not type_dir.is_dir():
                    continue
                type_name = type_dir.name
                max_days = self._retention.get(type_name)
                if max_days is None or max_days == 0:
                    continue

                for file in type_dir.iterdir():
                    if not file.is_file():
                        continue
                    age_days = (now - datetime.fromtimestamp(file.stat().st_mtime)).days
                    if age_days <= max_days:
                        continue

                    month_str = datetime.fromtimestamp(file.stat().st_mtime).strftime(
                        "%Y-%m"
                    )
                    archive_subdir = self._archive_dir / month_str

                    if self._dry_run:
                        result.would_archive += 1
                        logger.info(
                            "[DRY-RUN] Would archive %s → %s/",
                            file.name,
                            archive_subdir,
                        )
                    else:
                        archive_subdir.mkdir(parents=True, exist_ok=True)
                        target = archive_subdir / file.name
                        shutil.move(str(file), str(target))
                        result.archived += 1
                        logger.info("Archived %s → %s", file.name, target)

        return result
