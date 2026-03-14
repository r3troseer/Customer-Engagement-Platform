"""
FR11 — Unit tests for pure-logic helpers in reporting_service.
No DB, no I/O — only deterministic helpers.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.services.reporting_service import (
    _compliance_rate,
    _esg_overall_score,
    _week_start,
)


# ── _week_start ────────────────────────────────────────────────────────────────

def test_week_start_on_monday():
    # 2024-06-03 is a Monday
    assert _week_start(date(2024, 6, 3)) == date(2024, 6, 3)


def test_week_start_on_wednesday():
    # 2024-06-05 is a Wednesday → Monday is 2024-06-03
    assert _week_start(date(2024, 6, 5)) == date(2024, 6, 3)


def test_week_start_on_sunday():
    # 2024-06-09 is a Sunday → Monday is 2024-06-03
    assert _week_start(date(2024, 6, 9)) == date(2024, 6, 3)


# ── _compliance_rate ───────────────────────────────────────────────────────────

def test_compliance_rate_all_compliant():
    assert _compliance_rate(10, 10) == 100.0


def test_compliance_rate_half_compliant():
    assert _compliance_rate(5, 10) == 50.0


def test_compliance_rate_zero_total():
    assert _compliance_rate(0, 0) == 0.0


def test_compliance_rate_zero_compliant():
    assert _compliance_rate(0, 8) == 0.0


# ── _esg_overall_score ────────────────────────────────────────────────────────

def test_esg_overall_score_empty():
    assert _esg_overall_score([]) == Decimal("0")


def test_esg_overall_score_single_objective_full():
    # actual == target → 100%
    result = _esg_overall_score([(Decimal("100"), Decimal("100"))])
    assert result == Decimal("100.00")


def test_esg_overall_score_single_objective_half():
    result = _esg_overall_score([(Decimal("50"), Decimal("100"))])
    assert result == Decimal("50.00")


def test_esg_overall_score_multiple_objectives():
    # 100% + 50% = average 75%
    pairs = [(Decimal("100"), Decimal("100")), (Decimal("50"), Decimal("100"))]
    result = _esg_overall_score(pairs)
    assert result == Decimal("75.00")


def test_esg_overall_score_skips_zero_target():
    # Zero target objectives are skipped (can't divide by zero)
    pairs = [(Decimal("0"), Decimal("0")), (Decimal("50"), Decimal("100"))]
    result = _esg_overall_score(pairs)
    assert result == Decimal("50.00")
