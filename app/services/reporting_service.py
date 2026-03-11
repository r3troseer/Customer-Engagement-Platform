"""
FR11 — Reporting & Analytics service layer.
Report data aggregation, template management, scheduled execution.
"""
# TODO: implement the following functions

# get_esg_report(db, org_id, location_id, start_date, end_date) -> dict
#   - Aggregate EsgMetricValue grouped by EsgObjective
#   - Join EsgActivity for initiative counts
#   - Return structured ESG report dict

# get_compliance_report(db, org_id, location_id, start_date, end_date) -> dict
#   - Aggregate ComplianceRecord statuses per ComplianceFramework
#   - Calculate compliance score = compliant_count / total_count * 100
#   - Include expiring items within 30 days

# get_supplier_report(db, org_id) -> dict
#   - Aggregate SupplierDocument statuses per Supplier
#   - Include esg_score distribution

# get_dashboard_kpis(db, org_id, location_id) -> dict
#   - Live-calculated KPIs:
#     * active_employees (Employee count WHERE status=active)
#     * tokens_issued_this_week (WalletTransaction SUM WHERE direction=credit AND this week)
#     * open_compliance_items (ComplianceRecord count WHERE status NOT IN (compliant, expired))
#     * supplier_docs_pending_review (SupplierDocument count WHERE review_status=pending)
#     * leaderboard_entries_this_week (LeaderboardEntry count for open snapshot)
#   - Also upserts DashboardKpi rows for historical tracking

# get_scheduled_templates(db) -> list[ReportTemplate]
#   - Query ReportTemplate WHERE schedule_enabled=True AND status='active'

# create_template(db, data, creator_id) -> ReportTemplate
# update_template(db, template_id, data) -> ReportTemplate

# execute_report_run(db, template) -> ReportRun
#   1. Insert ReportRun with run_status='running', started_at=now()
#   2. Call appropriate aggregator based on template.report_type
#   3. Call export_service.generate_pdf(data) or generate_csv(data)
#   4. Save file via file_storage.save_upload()
#   5. Insert ReportExport row
#   6. Update ReportRun: status='completed', completed_at=now(), file_path
#   7. Return ReportRun
