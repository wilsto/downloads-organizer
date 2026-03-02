# Changelog

## [Unreleased]

## [0.3.0] - 2026-03-02

### Added
- `--verbose` CLI flag for detailed per-file logging instead of summary
- `--limit` support in deduplication phase
- 5 integration tests for main orchestration flow

### Changed
- Removed hardcoded `.env` file loading from main — use shell-inherited env vars instead
- Flattened deduplicator nesting (extract `_process_pair` / `_handle_duplicate` / `_handle_content_differs`)
- Replaced fragile regex JSON extraction with `JSONDecoder.raw_decode()` in LLM classifier
- Removed unused `subfolders` field from `ContextConfig` and `config.yaml`
- Pinned dependency upper bounds (`pydantic<3`, `ollama<1`, `httpx<1`, `pyyaml<7`)

## [0.2.0] - 2026-02-28

### Added
- `--limit N` CLI flag to process only the first N files
- Telegram notification via HA `script.notify_engine`
- HTML formatted messages with emoji bullets and status indicators
- Conditional error line (hidden when zero)
- Log path reference in notification footer
- 11 unit tests for notifier module

### Changed
- Notification service: `notify/telegram` -> `script/notify_engine`
- Notification payload now includes `who`, `title`, `enable_telegram` parameters
- `NotificationConfig` has new `who` field (default: `"will"`)

## [0.1.0] - 2026-02-28

### Added
- 4-phase pipeline: Deduplicate -> Classify & Move -> Archive -> Notify
- Regex-based classification into Pro / Perso / Tech contexts
- LLM fallback (Qwen3 14B via Ollama) for ambiguous files with cache
- SHA256 deduplication with auto-delete identical / rename if different
- Per-type retention policies with monthly archival
- YAML configuration with Pydantic validation
- Rotating log files (5MB, 3 backups)
- `--dry-run` mode for safe preview
- Windows Task Scheduler script (every 15 min)
- 50 unit tests across all modules
