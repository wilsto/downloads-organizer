# Downloads Organizer

Autonomous Python agent that organizes, deduplicates, and archives files from your Downloads folder, with smart classification and Telegram notifications.

## Features

- **4-phase pipeline**: Deduplicate -> Classify & Move -> Archive -> Notify
- **Regex-first classification** into configurable contexts (Pro / Perso / Tech)
- **LLM fallback** via Ollama (Qwen3 14B) for ambiguous files, with persistent cache
- **SHA256 deduplication**: auto-delete identical copies, rename when content differs
- **Per-type retention** policies with monthly archival
- **Telegram notifications** via Home Assistant `notify_engine`
- **Dry-run mode** for safe preview before any real changes
- **Scheduled execution** via Windows Task Scheduler (every 15 min)

## Architecture

```
src/organizer/
  main.py            # CLI entry point & orchestrator
  config.py          # Pydantic models + YAML loader
  scanner.py         # Directory scanning (root-level files)
  classifier.py      # Regex-based context/type classification
  llm_classifier.py  # Ollama LLM fallback with cache
  deduplicator.py    # SHA256 duplicate detection & cleanup
  mover.py           # File routing to destination folders
  archiver.py        # Retention-based archival by month
  notifier.py        # HA Telegram notification
  logger.py          # Rotating file + console logging
```

## Setup

```bash
# Clone
git clone https://github.com/wilsto/downloads-organizer.git
cd downloads-organizer

# Create venv & install
uv venv .venv
.venv/Scripts/activate  # Windows
uv pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your HA_TOKEN
# Edit config.yaml with your paths and rules
```

## Usage

```bash
# Preview changes (safe)
python -m organizer.main --dry-run

# Preview on a subset
python -m organizer.main --dry-run --limit 50

# Run for real
python -m organizer.main

# Custom config
python -m organizer.main --config /path/to/config.yaml
```

## Configuration

All settings live in `config.yaml`:

| Section | Description |
|---------|-------------|
| `source` | Downloads folder to scan |
| `destinations` | Context -> destination path mapping |
| `contexts` | Regex patterns per context (Pro, Perso, Tech) |
| `type_mapping` | Extension -> file type mapping |
| `retention` | Days before archival, per file type (0 = never) |
| `duplicates` | Dedup strategy and pattern |
| `llm` | Ollama model, cache file, keyword lists |
| `notification` | HA URL, service, target user |

## Scheduled Execution

Install the Windows Task Scheduler task (runs every 15 minutes):

```powershell
powershell -ExecutionPolicy Bypass -File install_task.ps1
```

## Tests

```bash
python -m pytest -v
```

## License

MIT
