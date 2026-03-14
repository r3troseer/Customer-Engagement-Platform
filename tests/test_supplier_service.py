"""
FR5 — Supplier service unit tests.
Tests cover pure-logic helpers and key state transitions.
No real DB, no filesystem, no S3 — all dependencies mocked.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import make_document, make_supplier


# ── Import the helpers we will implement ─────────────────────────────────────
# These are the pure functions extracted from supplier_service.py.
from app.services.supplier_service import (
    _aggregate_compliance_status,
    _recalculate_esg_score,
)


# =============================================================================
# _aggregate_compliance_status
# =============================================================================

class TestAggregateComplianceStatus:

    def test_no_documents_returns_not_started(self):
        assert _aggregate_compliance_status([]) == "not_started"

    def test_all_approved_returns_compliant(self):
        docs = [
            make_document(review_status="approved"),
            make_document(review_status="approved"),
        ]
        assert _aggregate_compliance_status(docs) == "compliant"

    def test_any_rejected_returns_non_compliant(self):
        docs = [
            make_document(review_status="approved"),
            make_document(review_status="rejected"),
        ]
        assert _aggregate_compliance_status(docs) == "non_compliant"

    def test_rejected_takes_priority_over_pending(self):
        docs = [
            make_document(review_status="pending"),
            make_document(review_status="rejected"),
        ]
        assert _aggregate_compliance_status(docs) == "non_compliant"

    def test_any_pending_returns_pending_verification(self):
        docs = [
            make_document(review_status="approved"),
            make_document(review_status="pending"),
        ]
        assert _aggregate_compliance_status(docs) == "pending_verification"

    def test_needs_update_returns_pending_verification(self):
        docs = [
            make_document(review_status="approved"),
            make_document(review_status="needs_update"),
        ]
        assert _aggregate_compliance_status(docs) == "pending_verification"

    def test_single_approved_returns_compliant(self):
        docs = [make_document(review_status="approved")]
        assert _aggregate_compliance_status(docs) == "compliant"


# =============================================================================
# _recalculate_esg_score
# =============================================================================

class TestRecalculateEsgScore:

    def test_returns_none_when_no_approved_docs(self):
        docs = [make_document(review_status="pending")]
        result = _recalculate_esg_score(docs)
        assert result is None

    def test_returns_none_when_docs_list_empty(self):
        assert _recalculate_esg_score([]) is None

    def test_returns_score_when_all_approved(self):
        docs = [
            make_document(review_status="approved"),
            make_document(review_status="approved"),
        ]
        result = _recalculate_esg_score(docs)
        assert result is not None
        assert isinstance(result, Decimal)
        assert result > 0

    def test_does_not_recalculate_when_any_not_approved(self):
        docs = [
            make_document(review_status="approved"),
            make_document(review_status="pending"),
        ]
        result = _recalculate_esg_score(docs)
        assert result is None


# =============================================================================
# delete_supplier — soft-delete logic
# =============================================================================

class TestDeleteSupplier:

    async def test_soft_delete_sets_status_inactive(self, mock_db):
        from app.services.supplier_service import delete_supplier

        supplier = make_supplier(status="active")
        # Patch get_supplier to return our mock without hitting DB
        with patch("app.services.supplier_service.get_supplier", new=AsyncMock(return_value=supplier)):
            current_user = {"user_id": 1, "roles": ["admin"]}
            await delete_supplier(mock_db, supplier_id=1, current_user=current_user)

        assert supplier.status == "inactive"
        mock_db.commit.assert_awaited()  # at least once (audit_service adds a second commit)

    async def test_soft_delete_does_not_call_db_delete(self, mock_db):
        from app.services.supplier_service import delete_supplier

        supplier = make_supplier(status="active")
        with patch("app.services.supplier_service.get_supplier", new=AsyncMock(return_value=supplier)):
            current_user = {"user_id": 1, "roles": ["admin"]}
            await delete_supplier(mock_db, supplier_id=1, current_user=current_user)

        mock_db.delete.assert_not_called()


# =============================================================================
# review_document — state transitions
# =============================================================================

class TestReviewDocument:

    async def test_approved_sets_review_status(self, mock_db):
        from app.services.supplier_service import review_document

        doc = make_document(review_status="pending")
        supplier = make_supplier(documents=[doc])

        with (
            patch("app.services.supplier_service.get_supplier", new=AsyncMock(return_value=supplier)),
            patch("app.services.supplier_service._get_document", new=AsyncMock(return_value=doc)),
            patch("app.services.supplier_service.list_documents", new=AsyncMock(return_value=[doc])),
        ):
            result = await review_document(
                mock_db, supplier_id=1, doc_id=1,
                action="approved", reviewer_id=2, feedback=None,
            )

        assert result.review_status == "approved"
        assert result.reviewer_id == 2
        mock_db.commit.assert_awaited()

    async def test_rejected_sets_feedback(self, mock_db):
        from app.services.supplier_service import review_document

        doc = make_document(review_status="pending")
        supplier = make_supplier(documents=[doc])

        with (
            patch("app.services.supplier_service.get_supplier", new=AsyncMock(return_value=supplier)),
            patch("app.services.supplier_service._get_document", new=AsyncMock(return_value=doc)),
            patch("app.services.supplier_service.list_documents", new=AsyncMock(return_value=[doc])),
        ):
            result = await review_document(
                mock_db, supplier_id=1, doc_id=1,
                action="rejected", reviewer_id=2, feedback="Missing expiry date.",
            )

        assert result.review_status == "rejected"
        assert result.review_feedback == "Missing expiry date."


# =============================================================================
# get_expiring_certs — date threshold filter
# =============================================================================

class TestGetExpiringCerts:

    async def test_returns_docs_at_or_before_threshold(self, mock_db):
        from app.services.supplier_service import get_expiring_certs

        threshold = date(2024, 7, 1)
        expiring = make_document(expiry_date=date(2024, 6, 30), review_status="approved", status="active")
        safe = make_document(expiry_date=date(2024, 12, 31), review_status="approved", status="active")

        # Simulate DB returning only the expiring doc
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [expiring]
        mock_db.execute.return_value = result_mock

        results = await get_expiring_certs(mock_db, threshold_date=threshold)

        assert expiring in results
        assert safe not in results

    async def test_returns_empty_when_no_expiring_docs(self, mock_db):
        from app.services.supplier_service import get_expiring_certs

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = result_mock

        results = await get_expiring_certs(mock_db, threshold_date=date(2024, 7, 1))

        assert results == []
