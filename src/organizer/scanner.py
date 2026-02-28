import mimetypes
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class FileInfo:
    path: Path
    name: str
    extension: str
    size: int
    modified: datetime
    mime_type: str | None

    @property
    def extension_lower(self) -> str:
        return self.extension.lower().lstrip(".")


def scan_directory(directory: Path) -> list[FileInfo]:
    if not directory.exists():
        return []

    files = []
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        stat = entry.stat()
        mime, _ = mimetypes.guess_type(entry.name)
        files.append(
            FileInfo(
                path=entry,
                name=entry.name,
                extension=entry.suffix,
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime),
                mime_type=mime,
            )
        )
    return files
