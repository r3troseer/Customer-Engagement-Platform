"""
FR5 — Supplier Transparency service layer.
All business logic for supplier CRUD, document upload/review, and compliance tracking.
"""
# TODO: implement the following functions

# create_supplier(db, data, current_user) -> Supplier
#   - Creates Supplier row
#   - Writes audit log via Sunny's audit_service.log_action()

# update_supplier(db, supplier_id, data, current_user) -> Supplier
#   - Updates Supplier row
#   - Writes audit log

# delete_supplier(db, supplier_id, current_user) -> None
#   - Soft-delete: sets status='inactive'
#   - Writes audit log

# upload_document(db, supplier_id, file, metadata, uploader_id) -> SupplierDocument
#   - Saves file via utils.file_storage.save_upload()
#   - Creates SupplierDocument row with review_status='pending'
#   - Notifies admins: notification_service.notify_document_uploaded()
#   - Writes audit log

# review_document(db, doc_id, status, reviewer_id, feedback) -> SupplierDocument
#   - Updates review_status (approved/rejected/needs_update)
#   - Updates parent Supplier.esg_score if all docs approved
#   - Writes audit log

# get_compliance_status(db, supplier_id) -> dict
#   - Aggregates SupplierDocument statuses into compliance summary

# update_compliance_status(db, supplier_id, new_status, reviewer_id) -> ComplianceRecord
#   - Appends a new compliance_records row (never overwrites — append-only history)
#   - Writes audit log

# get_compliance_history(db, supplier_id, pagination) -> list[ComplianceRecord]
#   - Returns ordered compliance_records for the supplier

# get_public_suppliers(db, pagination) -> list[Supplier]
#   - Filters is_public=True, returns only safe public fields

# get_expiring_certs(db, threshold_date) -> list[SupplierDocument]
#   - Called by compliance_tasks daily to find expiring certificates
