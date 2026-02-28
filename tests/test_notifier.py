import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

from organizer.config import NotificationConfig
from organizer.notifier import Notifier, RunSummary


@pytest.fixture
def config():
    return NotificationConfig(
        enabled=True,
        ha_url="http://homeassistant.local:8123",
        ha_token_env="HA_TOKEN",
        service="script/notify_engine",
        who="will",
    )


@pytest.fixture
def summary():
    return RunSummary(
        files_sorted=10,
        duplicates_deleted=3,
        files_archived=2,
        errors=0,
        duration_seconds=5.2,
        dry_run=True,
    )


class TestFormatMessage:
    def test_format_uses_html_bold(self, summary):
        msg = summary.format_message()
        assert "<b>" in msg

    def test_format_has_emoji_bullets(self, summary):
        msg = summary.format_message()
        assert "\U0001f4c2" in msg  # folder emoji
        assert "\U0001f5d1" in msg  # wastebasket emoji
        assert "\U0001f4e6" in msg  # package emoji

    def test_format_title_dry_run_badge(self, summary):
        title = summary.format_title()
        assert "DRY-RUN" in title

    def test_format_title_no_dry_run_badge(self):
        summary = RunSummary(files_sorted=5, dry_run=False)
        title = summary.format_title()
        assert "DRY-RUN" not in title

    def test_format_shows_errors_when_present(self):
        summary = RunSummary(errors=3, dry_run=False)
        msg = summary.format_message()
        assert "3" in msg
        assert "\u26a0\ufe0f" in msg  # warning emoji

    def test_format_hides_errors_when_zero(self, summary):
        msg = summary.format_message()
        assert "Erreur" not in msg

    def test_format_shows_log_path(self, summary):
        msg = summary.format_log_message()
        assert "organizer.log" in msg


class TestNotifierSend:
    @patch.dict(os.environ, {"HA_TOKEN": "test-token-123"})
    @patch("organizer.notifier.httpx.post")
    def test_send_calls_ha_with_correct_payload(self, mock_post, config, summary):
        mock_post.return_value = MagicMock(status_code=200, raise_for_status=MagicMock())
        notifier = Notifier(config)

        result = notifier.send(summary)

        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer test-token-123"
        assert "script/notify_engine" in call_kwargs.args[0]

        payload = call_kwargs.kwargs["json"]
        assert payload["who"] == "will"
        assert payload["enable_telegram"] is True
        assert payload["enable_voice"] is False

    def test_send_disabled_skips(self, summary):
        config = NotificationConfig(enabled=False)
        notifier = Notifier(config)
        result = notifier.send(summary)
        assert result is False

    @patch.dict(os.environ, {}, clear=True)
    def test_send_missing_token_skips(self, config, summary):
        os.environ.pop("HA_TOKEN", None)
        notifier = Notifier(config)
        result = notifier.send(summary)
        assert result is False

    @patch.dict(os.environ, {"HA_TOKEN": "test-token-123"})
    @patch("organizer.notifier.httpx.post")
    def test_send_http_error_returns_false(self, mock_post, config, summary):
        mock_post.side_effect = httpx.HTTPError("Connection refused")
        notifier = Notifier(config)
        result = notifier.send(summary)
        assert result is False
