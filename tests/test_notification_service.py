"""
FR12 — Unit tests for pure-logic helpers in notification_service.
No DB, no I/O — only deterministic helpers.
"""
from unittest.mock import MagicMock

import pytest

from app.services.notification_service import _category_enabled


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_prefs(**overrides) -> MagicMock:
    prefs = MagicMock()
    prefs.email_enabled = True
    prefs.push_enabled = True
    prefs.in_app_enabled = True
    prefs.reward_notifications_enabled = True
    prefs.compliance_alerts_enabled = True
    prefs.report_notifications_enabled = True
    prefs.challenge_notifications_enabled = True
    for k, v in overrides.items():
        setattr(prefs, k, v)
    return prefs


# ── _category_enabled ──────────────────────────────────────────────────────────

def test_token_reward_uses_reward_flag():
    prefs = make_prefs(reward_notifications_enabled=True)
    assert _category_enabled(prefs, "token_reward") is True


def test_token_reward_disabled_when_reward_flag_off():
    prefs = make_prefs(reward_notifications_enabled=False)
    assert _category_enabled(prefs, "token_reward") is False


def test_leaderboard_uses_reward_flag():
    prefs = make_prefs(reward_notifications_enabled=False)
    assert _category_enabled(prefs, "leaderboard") is False


def test_compliance_uses_compliance_flag():
    prefs = make_prefs(compliance_alerts_enabled=True)
    assert _category_enabled(prefs, "compliance") is True


def test_expiry_uses_compliance_flag():
    prefs = make_prefs(compliance_alerts_enabled=False)
    assert _category_enabled(prefs, "expiry") is False


def test_report_uses_report_flag():
    prefs = make_prefs(report_notifications_enabled=True)
    assert _category_enabled(prefs, "report") is True


def test_challenge_uses_challenge_flag():
    prefs = make_prefs(challenge_notifications_enabled=False)
    assert _category_enabled(prefs, "challenge") is False


def test_unknown_type_defaults_to_true():
    prefs = make_prefs()
    assert _category_enabled(prefs, "unknown_type") is True
