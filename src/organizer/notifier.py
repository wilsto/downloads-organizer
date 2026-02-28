import logging
import os
from dataclasses import dataclass

import httpx

from organizer.config import NotificationConfig

logger = logging.getLogger("organizer")


LOG_PATH = "organizer.log"


@dataclass
class RunSummary:
    files_sorted: int = 0
    duplicates_deleted: int = 0
    files_archived: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    dry_run: bool = False

    def format_title(self) -> str:
        mode = " [DRY-RUN]" if self.dry_run else ""
        status = "\u2705" if self.errors == 0 else "\u26a0\ufe0f"
        return f"{status} Downloads Organizer{mode}"

    def format_message(self) -> str:
        lines = [
            f"\U0001f4c2 <b>Fichiers tries :</b> {self.files_sorted}",
            f"\U0001f5d1 <b>Doublons supprimes :</b> {self.duplicates_deleted}",
            f"\U0001f4e6 <b>Archives :</b> {self.files_archived}",
            f"\u23f1 <b>Duree :</b> {self.duration_seconds:.1f}s",
        ]
        if self.errors > 0:
            lines.append(f"\u26a0\ufe0f <b>Erreurs :</b> {self.errors}")
        return "\n".join(lines)

    def format_log_message(self) -> str:
        return f"\n\U0001f4cb <i>{LOG_PATH}</i>"


class Notifier:
    def __init__(self, config: NotificationConfig):
        self._config = config

    def send(self, summary: RunSummary) -> bool:
        if not self._config.enabled:
            logger.info("Notifications disabled, skipping")
            return False

        token = os.environ.get(self._config.ha_token_env)
        if not token:
            logger.warning(
                "HA token not found in env var %s", self._config.ha_token_env
            )
            return False

        url = f"{self._config.ha_url}/api/services/{self._config.service}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        message = summary.format_message() + summary.format_log_message()
        payload = {
            "who": self._config.who,
            "title": summary.format_title(),
            "message": message,
            "enable_telegram": True,
            "enable_voice": False,
            "enable_text": False,
            "enable_persistent": False,
        }

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info("Notification sent to Telegram via HA")
            return True
        except httpx.HTTPError as e:
            logger.warning("Failed to send notification: %s", e)
            return False
