"""
Shared pytest fixtures for the CEP test suite.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_db():
    """Async mock of SQLAlchemy AsyncSession for unit tests."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.delete = MagicMock()
    return db


def make_supplier(**kwargs):
    """Factory for a minimal Supplier-like object (plain MagicMock)."""
    s = MagicMock()
    s.id = kwargs.get("id", 1)
    s.supplier_name = kwargs.get("supplier_name", "EcoFarm Produce")
    s.supplier_code = kwargs.get("supplier_code", "SUP001")
    s.status = kwargs.get("status", "active")
    s.esg_score = kwargs.get("esg_score", None)
    s.is_public = kwargs.get("is_public", False)
    s.documents = kwargs.get("documents", [])
    return s


def make_document(**kwargs):
    """Factory for a minimal SupplierDocument-like object (plain MagicMock)."""
    d = MagicMock()
    d.id = kwargs.get("id", 1)
    d.supplier_id = kwargs.get("supplier_id", 1)
    d.title = kwargs.get("title", "ISO 14001 Certificate")
    d.document_type = kwargs.get("document_type", "certificate")
    d.review_status = kwargs.get("review_status", "pending")
    d.reviewed_at = kwargs.get("reviewed_at", None)
    d.reviewer_id = kwargs.get("reviewer_id", None)
    d.review_feedback = kwargs.get("review_feedback", None)
    d.status = kwargs.get("status", "active")
    d.expiry_date = kwargs.get("expiry_date", None)
    return d
