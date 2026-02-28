import argparse
import logging
import os
import time
from pathlib import Path

from organizer.archiver import Archiver
from organizer.classifier import RegexClassifier
from organizer.config import load_config
from organizer.deduplicator import Deduplicator
from organizer.llm_classifier import LlmClassifier
from organizer.logger import setup_logger
from organizer.mover import FileMover
from organizer.notifier import Notifier, RunSummary
from organizer.scanner import scan_directory

DEFAULT_CONFIG = Path(__file__).parent.parent.parent / "config.yaml"
ENV_FILE = Path("C:/Users/Will/OneDrive/Dev/Homelab/scripts/.env")


def _load_env(env_path: Path) -> None:
    """Load environment variables from a .env file (key=value format)."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def main():
    parser = argparse.ArgumentParser(description="Downloads Organizer")
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG, help="Path to config.yaml"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without moving/deleting files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process only the first N files (0 = no limit)",
    )
    parser.add_argument(
        "--env-file", type=Path, default=ENV_FILE, help="Path to .env file"
    )
    args = parser.parse_args()

    _load_env(args.env_file)
    config = load_config(args.config)
    if args.dry_run:
        config.dry_run = True

    log = setup_logger(config.log_file)
    log.info("=== Downloads Organizer started (dry_run=%s) ===", config.dry_run)

    start = time.time()
    summary = RunSummary(dry_run=config.dry_run)

    # Phase 1: Deduplicate
    log.info("Phase 1: Deduplication")
    dedup = Deduplicator(config.duplicates, dry_run=config.dry_run)
    dedup_result = dedup.process(Path(config.source))
    summary.duplicates_deleted = dedup_result.deleted
    log.info(
        "Dedup done: %d deleted, %d renamed",
        dedup_result.deleted,
        dedup_result.renamed,
    )

    # Phase 2: Classify & Move
    log.info("Phase 2: Classification & Move")
    regex_classifier = RegexClassifier(
        contexts=config.contexts,
        type_mapping=config.type_mapping,
        default_context=config.default_context,
        default_type=config.default_type,
    )
    llm_classifier = LlmClassifier(config.llm)
    mover = FileMover(config.destinations, dry_run=config.dry_run)

    files = scan_directory(Path(config.source))
    if args.limit > 0:
        files = files[: args.limit]
    log.info("Found %d files to process (limit=%s)", len(files), args.limit or "none")

    for file_info in files:
        classification = regex_classifier.classify(file_info.name)

        # LLM fallback for ambiguous files
        if classification.matched_by == "default" and config.llm.enabled:
            llm_result = llm_classifier.classify(file_info)
            if llm_result and llm_result.confidence >= 0.7:
                classification.context = llm_result.context
                classification.file_type = llm_result.file_type
                classification.matched_by = "llm"

        result = mover.move(file_info.path, classification)
        if result.success or result.dry_run:
            summary.files_sorted += 1
        elif result.error:
            summary.errors += 1
            log.error("Failed to move %s: %s", file_info.name, result.error)

    # Save LLM cache
    llm_classifier.save_cache()

    # Phase 3: Archive
    log.info("Phase 3: Archival")
    archiver = Archiver(config.retention, config.archive_dir, dry_run=config.dry_run)
    organized_dirs = [
        Path(dest) for dest in config.destinations.values() if Path(dest).exists()
    ]
    archive_result = archiver.process(organized_dirs)
    summary.files_archived = archive_result.archived
    log.info("Archive done: %d archived", archive_result.archived)

    # Phase 4: Notify
    summary.duration_seconds = time.time() - start
    log.info("Phase 4: Notification")
    notifier = Notifier(config.notification)
    notifier.send(summary)

    log.info("=== Done in %.1fs ===", summary.duration_seconds)
    log.info(summary.format_message())


if __name__ == "__main__":
    main()
