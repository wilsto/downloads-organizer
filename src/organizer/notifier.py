import logging
import os
from dataclasses import dataclass

import httpx

from organizer.config import NotificationConfig

logger = logging.getLogger("organizer")


@dataclass
class RunSummary:
    files_sorted: int = 0
    duplicates_deleted: int = 0
    files_archived: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    dry_run: bool = False

    def format_message(self) -> str:
        mode = " [DRY-RUN]" if self.dry_run else ""
        return (
            f"*Downloads Organizer{mode}*\n\n"
            f"Fichiers tries: {self.files_sorted}\n"
            f"Doublons supprimes: {self.duplicates_deleted}\n"
            f"Fichiers archives: {self.files_archived}\n"
            f"Duree: {self.duration_seconds:.1f}s\n"
            f"Erreurs: {self.errors}"
        )


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
        payload = {"message": summary.format_message()}

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info("Notification sent to Telegram via HA")
            return True
        except httpx.HTTPError as e:
            logger.warning("Failed to send notification: %s", e)
            return False
