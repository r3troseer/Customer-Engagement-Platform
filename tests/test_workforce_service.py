"""
FR6 — Light unit tests for pure-logic functions in leaderboard_service.
No DB, no I/O — only deterministic helpers.
"""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import InsufficientTokensError
from app.services.leaderboard_service import (
    _assign_ranks,
    _calculate_score,
    _calculate_tokens,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_token_rule(tokens_awarded: str) -> MagicMock:
    rule = MagicMock()
    rule.tokens_awarded = Decimal(tokens_awarded)
    return rule


def make_entry(score: str) -> MagicMock:
    entry = MagicMock()
    entry.score = Decimal(score)
    entry.rank_position = None
    return entry


# ── calculate_tokens ───────────────────────────────────────────────────────────

def test_calculate_tokens_flat_rate():
    rule = make_token_rule("5.00")
    result = _calculate_tokens(rule, Decimal("8.00"))
    assert result == Decimal("40.00")


def test_calculate_tokens_no_hours_uses_flat_award():
    """When hours_worked is None, fall back to the flat tokens_awarded value."""
    rule = make_token_rule("50.00")
    result = _calculate_tokens(rule, None)
    assert result == Decimal("50.00")


def test_calculate_tokens_no_rule_returns_zero():
    result = _calculate_tokens(None, Decimal("8.00"))
    assert result == Decimal("0")


# ── calculate_score ────────────────────────────────────────────────────────────

def test_calculate_score_regular_log():
    """Regular log: score equals tokens, no bonus applied."""
    tokens = Decimal("40.00")
    result = _calculate_score(tokens, is_sustainability=False, bonus_rule=None)
    assert result == Decimal("40.00")


def test_calculate_score_sustainability_log_with_bonus_rule():
    """Sustainability log: score = tokens + bonus."""
    tokens = Decimal("40.00")
    bonus_rule = make_token_rule("25.00")
    result = _calculate_score(tokens, is_sustainability=True, bonus_rule=bonus_rule)
    assert result == Decimal("65.00")


def test_calculate_score_sustainability_log_no_bonus_rule():
    """Sustainability log with no bonus rule: score equals tokens (no crash)."""
    tokens = Decimal("40.00")
    result = _calculate_score(tokens, is_sustainability=True, bonus_rule=None)
    assert result == Decimal("40.00")


# ── assign_ranks ───────────────────────────────────────────────────────────────

def test_assign_ranks_orders_by_score_desc():
    entries = [make_entry("100"), make_entry("300"), make_entry("200")]
    ranked = _assign_ranks(entries)
    scores = [e.score for e in ranked]
    assert scores == [Decimal("300"), Decimal("200"), Decimal("100")]


def test_assign_ranks_sets_rank_position():
    entries = [make_entry("100"), make_entry("300"), make_entry("200")]
    ranked = _assign_ranks(entries)
    assert ranked[0].rank_position == 1
    assert ranked[1].rank_position == 2
    assert ranked[2].rank_position == 3


def test_assign_ranks_empty_list():
    assert _assign_ranks([]) == []


# ── InsufficientTokensError ────────────────────────────────────────────────────

def test_insufficient_tokens_error_message():
    err = InsufficientTokensError(balance=10.0, required=50.0)
    assert "10" in err.detail
    assert "50" in err.detail
