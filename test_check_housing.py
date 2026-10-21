import os

# Fake values so tests never touch your real .env or send real texts.
os.environ.setdefault("ASURITE_USERNAME", "test-user")
os.environ.setdefault("ASURITE_PASSWORD", "test-pass")
os.environ.setdefault("ALERT_PHONE_NUMBER", "5551234567")
os.environ.setdefault("ALERT_CARRIER_GATEWAY", "vtext.com")
os.environ.setdefault("ALERT_SENDER_EMAIL", "test@example.com")
os.environ.setdefault("ALERT_SENDER_APP_PASSWORD", "test-app-password")

from unittest.mock import patch

import check_housing


class FakeDriver:
    """Pretends to be Selenium. No browser needed."""

    def __init__(self, no_rooms_message_shown):
        self.no_rooms_message_shown = no_rooms_message_shown

    def find_element(self, by, value):
        if self.no_rooms_message_shown:
            return object()
        raise Exception("element not found")


def test_no_rooms_message_means_not_available():
    assert check_housing.rooms_available(FakeDriver(True)) is False


def test_missing_message_means_rooms_available():
    assert check_housing.rooms_available(FakeDriver(False)) is True


def test_text_alert_goes_to_carrier_gateway():
    with patch("check_housing.smtplib.SMTP_SSL") as mock_smtp:
        check_housing.send_text_alert()
        server = mock_smtp.return_value.__enter__.return_value
        server.sendmail.assert_called_once()
        sent_to = server.sendmail.call_args[0][1]
        expected = f"{check_housing.ALERT_PHONE_NUMBER}@{check_housing.ALERT_CARRIER_GATEWAY}"
        assert sent_to == expected