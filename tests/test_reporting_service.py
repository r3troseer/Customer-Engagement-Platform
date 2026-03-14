"""
FR11 — Unit tests for pure-logic helpers in reporting_service and export_service.
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
from app.services.export_service import generate_csv, generate_pdf


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


# ── export_service: generate_pdf ──────────────────────────────────────────────

def test_generate_pdf_returns_bytes():
    data = {"organization_id": 1, "overall_score": "75.00", "objectives": []}
    result = generate_pdf(data, "esg")
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result[:4] == b"%PDF"


def test_generate_pdf_with_list_field():
    data = {
        "organization_id": 1,
        "objectives": [
            {"name": "Carbon Reduction", "target": "100", "actual": "80", "unit": "tCO2", "status": "active"},
        ],
    }
    result = generate_pdf(data, "esg")
    assert result[:4] == b"%PDF"


# ── export_service: generate_csv ─────────────────────────────────────────────

def test_generate_csv_esg_has_correct_columns():
    data = {
        "objectives": [
            {"name": "Carbon", "target": "100", "actual": "80", "unit": "tCO2", "status": "active"},
        ]
    }
    result = generate_csv(data, "esg")
    header = result.decode("utf-8").splitlines()[0]
    assert header == "name,target,actual,unit,status"


def test_generate_csv_compliance_has_correct_columns():
    data = {
        "frameworks": [
            {"framework_name": "ISO 14001", "compliant": 8, "total": 10, "percentage": 80.0},
        ]
    }
    result = generate_csv(data, "compliance")
    header = result.decode("utf-8").splitlines()[0]
    assert header == "framework_name,compliant,total,percentage"


def test_generate_csv_supplier_has_correct_columns():
    data = {
        "total_suppliers": 5, "active_suppliers": 4, "inactive_suppliers": 1,
        "suspended_suppliers": 0, "avg_esg_score": "82.50",
        "documents_pending_review": 2, "certified_suppliers": 3,
    }
    result = generate_csv(data, "supplier")
    header = result.decode("utf-8").splitlines()[0]
    assert header == "total,active,inactive,suspended,avg_esg_score,docs_pending,certified"


def test_generate_csv_dashboard_has_correct_columns():
    data = {
        "kpis": [
            {"kpi_code": "ACTIVE_EMPLOYEES", "kpi_name": "Active Employees",
             "kpi_value": "42", "unit": "employees"},
        ]
    }
    result = generate_csv(data, "dashboard")
    header = result.decode("utf-8").splitlines()[0]
    assert header == "kpi_code,kpi_name,kpi_value,unit"
